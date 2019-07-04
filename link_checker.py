import grequests
import argparse
import time
import sys
from urllib.parse import urljoin, urlsplit

# WARNING: Always import grequests before requests
import requests
from bs4 import BeautifulSoup

# Set defaults
START_TIME = time.time()
err_code = 0
verbose = False
output_err = False
HEADER = {
    "User-Agent": "Mozilla/5.0 (X11; Linux i686 on x86_64; rv:10.0) Gecko/20100101 Firefox/10.0"
}
memoized_links = {}
map_broken_links = {}
GOOD_RESPONSE = [200, 300, 301, 302]

# Setup argument parser
parser = argparse.ArgumentParser(description="Script to check broken links")
parser.add_argument(
    "-v", "--verbose", help="Increase verbosity of output", action="store_true"
)
parser.add_argument(
    "--output-error",
    help="Outputs all link errors to file (default: errorlog.txt)",
    metavar="output_file",
    const="errorlog.txt",
    nargs="?",
    type=argparse.FileType("w", encoding="utf-8"),
    dest="output",
)
args = parser.parse_args()
if args.verbose:
    verbose = True
if args.output:
    output = args.output
    output_err = True


def get_all_license():
    """This function scrapes all the license file in the repo 'https://github.com/creativecommons/creativecommons.org/tree/master/docroot/legalcode'.

    Returns:
        str[]: The list of license/deeds files found in the repository
    """
    URL = "https://github.com/creativecommons/creativecommons.org/tree/master/docroot/legalcode"
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "lxml")
    links = soup.table.tbody.find_all("a", class_="js-navigation-open")
    print("No. of files to be checked:", len(links))
    return links


def create_base_link(filename):
    """Generates base URL on which the license file will be displayed

    Args:
        filename (str): Name of the license file

    Returns:
        str: Base URL of the license file
    """
    ROOT_URL = "https://creativecommons.org"
    parts = filename.split("_")

    if parts[0] == "samplingplus":
        extra = "/licenses/sampling+"
    elif parts[0].startswith("zero"):
        extra = "/publicdomain/" + parts[0]
    else:
        extra = "/licenses/" + parts[0]

    extra = extra + "/" + parts[1]
    if parts[0] == "samplingplus" and len(parts) == 3:
        extra = extra + "/" + parts[2] + "/legalcode"
        return ROOT_URL + extra

    if len(parts) == 4:
        extra = extra + "/" + parts[2]
    extra = extra + "/legalcode"
    if len(parts) >= 3:
        extra = extra + "." + parts[-1]
    return ROOT_URL + extra


def verbose_print(*args, **kwargs):
    """Prints only if -v or --verbose flag is set
    """
    if verbose:
        print(*args, **kwargs)


def output_write(*args, **kwargs):
    """Prints to output file is --output-error flag is set
    """
    if output_err:
        kwargs["file"] = output
        print(*args, **kwargs)


def output_summary(num_errors):
    """Prints short summary of broken links in the output error file

    Args:
        num_errors (int): Number of broken links found
    """
    output_write(
        "\n\n{}\n{} SUMMARY\n{}\n".format("*" * 39, " " * 15, "*" * 39)
    )
    output_write("Timestamp: {}".format(time.ctime()))
    output_write("Total files checked: {}".format(len(all_links)))
    output_write("Number of error links: {}".format(num_errors))
    keys = map_broken_links.keys()
    output_write("Number of unique broken links: {}\n".format(len(keys)))
    for key, value in map_broken_links.items():
        output_write("\nBroken link - {} found in:".format(key))
        for url in value:
            output_write(url)


def create_absolute_link(link_analysis):
    """Creates absolute links from relative links

    Args:
        link_analysis (class 'urllib.parse.SplitResult'): Link splitted by urlsplit, that is to be converted

    Returns:
        str: absolute link
    """
    href = link_analysis.geturl()
    # Check for relative link
    if (
        link_analysis.scheme == ""
        and link_analysis.netloc == ""
        and link_analysis.path != ""
    ):
        href = urljoin(base_url, href)
        return href
    # Append scheme https where absent
    if link_analysis.scheme == "":
        link_analysis = link_analysis._replace(scheme="https")
        href = link_analysis.geturl()
        return href
    return href


def get_scrapable_links(links_in_license):
    """Filters out anchor tags without href attribute, internal links and mailto scheme links

    Args:
        links_in_license (list): List of all the links found in file

    Returns:
        set: valid_anchors - list of all scrapable anchor tags
             valid_links - list of all absolute scrapable links
    """
    valid_links = []
    valid_anchors = []
    for link in links_in_license:
        try:
            href = link["href"]
        except KeyError:
            # if there exists an <a> tag without href
            verbose_print("Found anchor tag without href -\t", link)
            continue
        if href[0] == "#":
            verbose_print("Skipping internal link -\t", link)
            continue
        if href.startswith("mailto:"):
            continue
        analyze = urlsplit(href)
        valid_links.append(create_absolute_link(analyze))
        valid_anchors.append(link)
    return (valid_anchors, valid_links)


def exception_handler(request, exception):
    """Handles Invalid Scheme and Timeout Error from grequests.get

    Args:
        request (class 'grequests.AsyncRequest'): Request on which error occured
        exception (class 'requests.exceptions'): Exception occured

    Returns:
        str: Exception occured in string format
    """
    if type(exception) == requests.exceptions.InvalidSchema:
        return "Invalid Schema"
    if type(exception) == requests.exceptions.ConnectTimeout:
        return "Timeout Error"


def map_links_file(link, file_url):
    """Maps broken link to the files of occurence

    Args:
        link (str): Broken link encountered
        file_url (str): File url in which the broken link was encountered
    """
    if map_broken_links.get(link):
        if file_url not in map_broken_links[link]:
            map_broken_links[link].append(file_url)
    else:
        map_broken_links[link] = [file_url]


def write_response(all_links, response, base_url, license_name, valid_anchors):
    """Writes broken links to CLI and file

    Args:
        all_links (list): List of all scrapable links found in website
        response (list): Response status code/ exception of all the links in all_links
        base_url (string): URL on which the license page will be displayed
        license_name (string): Name of license
        valid_anchors (list): List of all the scrapable anchors

    Returns:
        int: Number of broken links found in license
    """
    caught_errors = 0
    for idx, link_status in enumerate(response):
        try:
            status = link_status.status_code
        except AttributeError:
            status = link_status
        if status not in GOOD_RESPONSE:
            map_links_file(all_links[idx], base_url)
            caught_errors += 1
            if caught_errors == 1:
                if not verbose:
                    print("Errors:")
                output_write("\n{}\nURL: {}".format(license_name, base_url))
            print(status, "-\t", valid_anchors[idx])
            output_write(status, "-\t", valid_anchors[idx])
    return caught_errors


def get_memoized_result(valid_links, valid_anchors):
    """Get memoized result of previously checked links

    Args:
        valid_links (list): List of all scrapable links in license
        valid_anchors (list): List of all scrapable anchor tags in license

    Returns:
        set: stored_links - List of links whose responses are memoized
             stored_anchors - List of anchor tags corresponding to stored_links
             stored_result - List of responses corresponding to stored_links
             check_links - List of links which are to be checked
             check_anchors - List of anchor tags corresponding to check_links
    """
    stored_links = []
    stored_anchors = []
    stored_result = []
    check_links = []
    check_anchors = []
    for idx, link in enumerate(valid_links):
        status = memoized_links.get(link)
        if status:
            stored_anchors.append(valid_anchors[idx])
            stored_result.append(status)
            stored_links.append(link)
        else:
            check_links.append(link)
            check_anchors.append(valid_anchors[idx])
    return (
        stored_links,
        stored_anchors,
        stored_result,
        check_links,
        check_anchors,
    )


def memoize_result(check_links, response):
    """Memoize the result of links checked

    Args:
        check_links (list): List of fresh links that are processed
        response (list): List of response corresponding to check_links
    """
    for idx, link in enumerate(check_links):
        memoized_links[link] = response[idx]


all_links = get_all_license()

GITHUB_BASE = "https://raw.githubusercontent.com/creativecommons/creativecommons.org/master/docroot/legalcode/"


errors_total = 0
for licens in all_links:
    caught_errors = 0
    check_extension = licens.string.split(".")
    page_url = GITHUB_BASE + licens.string
    print("\n")
    print("Checking:", licens.string)
    if check_extension[-1] != "html":
        verbose_print("Encountered non-html file -\t skipping", licens.string)
        continue
    # Refer to issue https://github.com/creativecommons/cc-link-checker/issues/9 for more info
    if licens.string == "samplingplus_1.0.br.html":
        continue
    filename = licens.string[:-5]
    base_url = create_base_link(filename)
    print("URL:", base_url)
    source_html = requests.get(page_url, headers=HEADER)
    license_soup = BeautifulSoup(source_html.content, "lxml")
    links_in_license = license_soup.find_all("a")
    verbose_print("No. of links found:", len(links_in_license))
    verbose_print("Errors and Warnings:")
    valid_anchors, valid_links = get_scrapable_links(links_in_license)
    if valid_links:
        stored_links, stored_anchors, stored_result, check_links, check_anchors = get_memoized_result(
            valid_links, valid_anchors
        )
        if check_links:
            rs = (grequests.get(link, timeout=10) for link in check_links)
            response = grequests.map(rs, exception_handler=exception_handler)
            memoize_result(check_links, response)
            stored_anchors += check_anchors
            stored_result += response
        stored_links += check_links
        caught_errors = write_response(
            stored_links,
            stored_result,
            base_url,
            licens.string,
            stored_anchors,
        )

    if caught_errors:
        errors_total += caught_errors
        err_code = 1


print("\nCompleted in: {}".format(time.time() - START_TIME))

if output_err:
    output_summary(errors_total)
    print("\nError file present at: ", output.name)
sys.exit(err_code)
