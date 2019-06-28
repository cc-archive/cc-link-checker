import argparse
import concurrent.futures as fp
import sys
import time
from threading import Lock
from urllib.parse import urljoin, urlsplit

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
scraped_links = {}
map_broken_links = {}


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


def create_absolute_link(link_analysis):
    """Creates absolute links from relative links

    Args:
        link_analysis (class 'urllib.parse.SplitResult'): Link splitted by urlsplit, that is to be converted

    Returns:
        str: absolute link
    """
    href = link_analysis.geturl()
    if (
        link_analysis.scheme == ""
        and link_analysis.netloc == ""
        and link_analysis.path != ""
    ):
        href = urljoin(base_url, href)
    return href


def check_existing(link):
    """This function checks if the link is already present in scraped_links.

    Args:
        link (bs4.element.Tag): The anchor tag extracted using BeautifulSoup which is to be checked

    Returns:
        String or Number: The status of the link(200) or error message
    """
    href = link["href"]
    analyse = urlsplit(href)
    href = create_absolute_link(analyse)
    status = scraped_links.get(href)
    if status:
        if status not in [200, "ignore"]:
            map_broken_links[href].append(base_url)
        return status
    else:
        status = scrape(href)
        scraped_links[href] = status
        if status not in [200, "ignore"]:
            map_broken_links[href] = [base_url]
        return status


def get_status(href):
    """Sends request to link and returns status_code or Timeout Error

    Args:
        href (str): href extracted from anchor tag which is to be scraped

    Returns:
        int or str: Status code of response or "Timeout Error"
    """
    try:
        res = requests.get(href, headers=HEADER, timeout=10)
    except requests.exceptions.Timeout:
        return "Timeout Error"
    else:
        return res.status_code


def scrape(href):
    """Checks the status of the link and returns the status code 200 or the error encountered.

    Args:
        href (str): href extracted from anchor tag which is to be scraped

    Returns:
        int or str: Error encountered or Status code 200
    """
    analyse = urlsplit(href)
    if analyse.scheme == "" or analyse.scheme in ["https", "http"]:
        if analyse.scheme == "":
            analyse = analyse._replace(scheme="https")
        href = analyse.geturl()
        res = get_status(href)
        return res
    elif analyse.scheme == "mailto":
        return "ignore"
    else:
        return "Invalid protocol detected"


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


def check_link(link, licens_name, base_url):
    """Function that checks the link for errors and warning, and prints it. This is the target for thread.

    Args:
        link (class 'bs4.element.tag'): The link that is to be checked for errors or warning
        licens_name (str): Name of the license file
        base_url (str): The url on which the license file is displayed
    """
    global caught_errors, err_code
    try:
        href = link["href"]
    except KeyError:
        # if there exists an <a> tag without href
        verbose_print("Found anchor tag without href -\t", link)
        return
    if href[0] == "#":
        verbose_print("Skipping internal link -\t", link)
        return
    status = check_existing(link)
    with lock:
        if status not in [200, "ignore"]:
            caught_errors += 1
            if caught_errors == 1:
                if not verbose:
                    print("Errors:")
                output_write("\n{}\nURL: {}".format(licens_name, base_url))
            err_code = 1
            print(status, "-\t", link)
            output_write(status, "-\t", link)


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
    with fp.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {
            executor.submit(check_link, link, licens.string, base_url): link
            for link in links_in_license
        }
        fp.as_completed(future_to_url)
    errors_total += caught_errors

if output_err:
    output_summary(errors_total)
    print("\nError file present at: ", output.name)
print("Completed in: {}".format(time.time() - START_TIME))
sys.exit(err_code)
