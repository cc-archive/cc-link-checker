#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Check for broken links in Creative Commons licenses
"""

# Standard library
from urllib.parse import urljoin, urlsplit
import argparse
import os
import sys
import time
import traceback

# Third-party
from bs4 import BeautifulSoup
from junit_xml import TestCase, TestSuite, to_xml_report_file
import grequests  # WARNING: Always import grequests before requests
import requests


# Set defaults
START_TIME = time.time()
HEADER = {
    "User-Agent": "Mozilla/5.0 (X11; Linux i686 on x86_64; rv:10.0)"
    " Gecko/20100101 Firefox/10.0"
}
MEMOIZED_LINKS = {}
MAP_BROKEN_LINKS = {}
GOOD_RESPONSE = [200, 300, 301, 302]
REQUESTS_TIMEOUT = 5
GITHUB_BASE = (
    "https://raw.githubusercontent.com/creativecommons/creativecommons.org"
    "/master/docroot/legalcode/"
)
LICENSE_LOCAL_PATH = "../creativecommons.org/docroot/legalcode"
TEST_ORDER = ["zero", "4.0", "3.0", "2.5", "2.1", "2.0"]
DEFAULT_ROOT_URL = "https://creativecommons.org"
CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10


class CheckerError(Exception):
    def __init__(self, message, code=None):
        self.code = code if code else 1
        self.message = "({}) {}".format(self.code, message)
        super(CheckerError, self).__init__(self.message)

    def __str__(self):
        return self.message


def parse_argument(arguments):
    """parse arguments from cli

    Args:
        args (list): list of arguments parsed from command line
    """
    # Setup argument parser
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--local",
        help="Scrapes license files from local file system",
        action="store_true",
    )
    parser.add_argument(
        "--output-errors",
        help="Outputs all link errors to file (default: errorlog.txt) and"
        " creates junit-xml type summary(test-summary/junit-xml-report.xml)",
        metavar="output_file",
        const="errorlog.txt",
        nargs="?",
        type=argparse.FileType("w", encoding="utf-8"),
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="append_const",
        const=10,
        dest="verbosity",
        help="Decrease verbosity. Can be specified multiple times.",
    )
    parser.add_argument(
        "--root-url", help=f"Set root URL (default: {DEFAULT_ROOT_URL})",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="append_const",
        const=-10,
        dest="verbosity",
        help="Increase verbosity. Can be specified multiple times.",
    )

    args = parser.parse_args(arguments)
    if args.root_url is None:
        args.root_url = DEFAULT_ROOT_URL
    args.log_level = WARNING
    if args.verbosity:
        for v in args.verbosity:
            args.log_level += v
        if args.log_level < DEBUG:
            args.log_level = DEBUG
        elif args.log_level > CRITICAL:
            args.log_level = CRITICAL
    if not args.output_errors:
        args.output_errors = None
    return args


def get_local_licenses():
    """This function get all the licenses stored locally

    Returns:
        list: list of file names of license file
    """
    try:
        license_names_unordered = os.listdir(LICENSE_LOCAL_PATH)
    except FileNotFoundError:
        raise CheckerError(
            "Local license path({}) does not exist".format(LICENSE_LOCAL_PATH)
        )
    # Catching permission denied(OS ERROR) or other errors
    except:
        raise
    # Although license_names_unordered is sorted below, is not ordered
    # according to TEST_ORDER.
    license_names_unordered.sort()
    license_names = []
    # Test newer licenses first (they are the most volatile) and exclude
    # non-.html files
    for version in TEST_ORDER:
        for name in license_names_unordered:
            if ".html" in name and version in name:
                license_names.append(name)
    for name in license_names_unordered:
        if ".html" in name and name not in license_names:
            license_names.append(name)
    return license_names


def get_github_licenses():
    """This function scrapes all the license file in the repo:
    https://github.com/creativecommons/creativecommons.org/tree/master/docroot/legalcode

    Returns:
        str[]: The list of license/deeds files found in the repository
    """
    URL = (
        "https://github.com/creativecommons/creativecommons.org/tree/master"
        "/docroot/legalcode"
    )
    page_text = request_text(URL)
    soup = BeautifulSoup(page_text, "lxml")
    license_names_unordered = []
    for link in soup.table.tbody.find_all("a", class_="js-navigation-open"):
        license_names_unordered.append(link.string)
    # Although license_names_unordered is sorted below, is not ordered
    # according to TEST_ORDER.
    license_names_unordered.sort()
    license_names = []
    # Test newer licenses first (they are the most volatile) and exclude
    # non-.html files
    for version in TEST_ORDER:
        for name in license_names_unordered:
            if ".html" in name.string and version in name.string:
                license_names.append(name)
    for name in license_names_unordered:
        if ".html" in name.string and name not in license_names:
            license_names.append(name)
    return license_names


def request_text(page_url):
    """This function makes a requests get and returns the text result

    Args:
        page_url (str): URL to perform a GET request for

    Returns:
        str: request response text
    """
    try:
        r = requests.get(page_url, headers=HEADER, timeout=REQUESTS_TIMEOUT)
        fetched_text = r.content
    except requests.exceptions.ConnectionError:
        raise CheckerError(
            "FAILED to retreive source HTML ({}) due to"
            " ConnectionError".format(page_url),
            1,
        )
    except requests.exceptions.Timeout:
        raise CheckerError(
            "FAILED to retreive source HTML ({}) due to"
            " Timeout".format(page_url),
            1,
        )
    except:
        raise
    return fetched_text


def request_local_text(license_name):
    """This function reads license content from license file stored in local
    file system

    Args:
        license_name (str): Name of the license

    Returns:
        str: Content of license file
    """
    filename = license_name
    path = os.path.join(LICENSE_LOCAL_PATH, filename)
    try:
        with open(path) as lic:
            return lic.read()
    except FileNotFoundError:
        raise CheckerError(
            "Local license path({}) does not exist".format(path)
        )
    # Catching permission denied(OS ERROR) or other errors
    except:
        raise


def create_base_link(args, filename):
    """Generates base URL on which the license file will be displayed

    Args:
        filename (str): Name of the license file

    Returns:
        str: Base URL of the license file
    """
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
        return args.root_url + extra

    if len(parts) == 4:
        extra = extra + "/" + parts[2]
    extra = extra + "/legalcode"
    if len(parts) >= 3:
        extra = extra + "." + parts[-1]
    return args.root_url + extra


def get_scrapable_links(
    args, base_url, links_in_license, context, context_printed
):
    """Filters out anchor tags without href attribute, internal links and
    mailto scheme links

    Args:
        base_url (string): URL on which the license page will be displayed
        links_in_license (list): List of all the links found in file

    Returns:
        set: valid_anchors - list of all scrapable anchor tags
             valid_links - list of all absolute scrapable links
    """
    valid_links = []
    valid_anchors = []
    warnings = []
    for link in links_in_license:
        try:
            href = link["href"]
        except KeyError:
            try:
                assert link["id"]
            except KeyError:
                try:
                    assert link["name"]
                    warnings.append(
                        "  {:<24}{}".format("Anchor uses name", link)
                    )
                except:
                    warnings.append(
                        "  {:<24}{}".format("Anchor w/o href or id", link)
                    )
            continue
        if href[0] == "#":
            # anchor links are valid, but out of scope
            # No need to report non-issue (not actionable)
            # warnings.append(
            #     "  {:<24}{}".format("Skipping internal link ", link)
            # )
            continue
        if href.startswith("mailto:"):
            # mailto links are valid, but out of scope
            # No need to report non-issue (not actionable)
            # warnings.append
            #     "  {:<24}{}".format("Skipping mailto link ", link)
            # )
            continue
        analyze = urlsplit(href)
        valid_links.append(create_absolute_link(base_url, analyze))
        valid_anchors.append(link)
    # Logging level WARNING or lower
    if warnings and args.log_level <= WARNING:
        print(context)
        print("Warnings:")
        print("\n".join(warnings))
        context_printed = True
    return (valid_anchors, valid_links, context_printed)


def create_absolute_link(base_url, link_analysis):
    """Creates absolute links from relative links

    Args:
        base_url (string): URL on which the license page will be displayed
        link_analysis (class 'urllib.parse.SplitResult'): Link splitted by
            urlsplit, that is to be converted

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
        status = MEMOIZED_LINKS.get(link)
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


def exception_handler(request, exception):
    """Handles Invalid Scheme and Timeout Error from grequests.get

    Args:
        request (class 'grequests.AsyncRequest'): Request on which error
            occured
        exception (class 'requests.exceptions'): Exception occured

    Returns:
        str: Exception occured in string format
    """
    if type(exception) == requests.exceptions.ConnectionError:
        return "Connection Error"
    elif type(exception) == requests.exceptions.ConnectTimeout:
        return "Timeout Error"
    elif type(exception) == requests.exceptions.InvalidSchema:
        return "Invalid Schema"
    else:
        return type(exception).__name__


def memoize_result(check_links, responses):
    """Memoize the result of links checked

    Args:
        check_links (list): List of fresh links that are processed
        responses (list): List of response status codes corresponding to
            check_links
    """
    for idx, link in enumerate(check_links):
        MEMOIZED_LINKS[link] = responses[idx]


def write_response(
    args,
    all_links,
    response,
    base_url,
    license_name,
    valid_anchors,
    context,
    context_printed,
):
    """Writes broken links to CLI and file

    Args:
        all_links (list): List of all scrapable links found in website
        response (list): Response status code/ exception of all the links in
            all_links
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
                if args.log_level <= ERROR:
                    if not context_printed:
                        print(context)
                    print("Errors:")
                output_write(
                    args, "\n{}\nURL: {}".format(license_name, base_url)
                )
            result = "  {:<24}{}".format(str(status), valid_anchors[idx])
            if args.log_level <= ERROR:
                print(result)
            output_write(args, result)
    return caught_errors


def map_links_file(link, file_url):
    """Maps broken link to the files of occurence

    Args:
        link (str): Broken link encountered
        file_url (str): File url in which the broken link was encountered
    """
    if MAP_BROKEN_LINKS.get(link):
        if file_url not in MAP_BROKEN_LINKS[link]:
            MAP_BROKEN_LINKS[link].append(file_url)
    else:
        MAP_BROKEN_LINKS[link] = [file_url]


def output_write(args, *args_, **kwargs):
    """Prints to output file is --output-error flag is set
    """
    if args.output_errors:
        kwargs["file"] = args.output_errors
        print(*args_, **kwargs)


def output_summary(args, license_names, num_errors):
    """Prints short summary of broken links in the output error file

    Args:
        license_names: Array of link to license files
        num_errors (int): Number of broken links found
    """
    output_write(
        args, "\n\n{}\n{} SUMMARY\n{}\n".format("*" * 39, " " * 15, "*" * 39)
    )
    output_write(args, "Timestamp: {}".format(time.ctime()))
    output_write(args, "Total files checked: {}".format(len(license_names)))
    output_write(args, "Number of error links: {}".format(num_errors))
    keys = MAP_BROKEN_LINKS.keys()
    output_write(args, "Number of unique broken links: {}\n".format(len(keys)))
    for key, value in MAP_BROKEN_LINKS.items():
        output_write(args, "\nBroken link - {} found in:".format(key))
        for url in value:
            output_write(args, url)


def output_test_summary(errors_total):
    """Prints summary of script output in form of junit-xml

    Args:
        errors_total (int): Total number of broken links
    """
    if not os.path.isdir("test-summary"):
        os.mkdir("test-summary")
    with open("test-summary/junit-xml-report.xml", "w") as test_summary:
        time_taken = time.time() - START_TIME
        test_case = TestCase(
            "Broken links checker", "License files", time_taken
        )
        if errors_total != 0:
            test_case.add_failure_info(
                f"{errors_total} broken links found",
                f"Number of error links: {errors_total}\nNumber of unique"
                f" broken links: {len(MAP_BROKEN_LINKS.keys())}",
            )
        ts = TestSuite("cc-link-checker", [test_case])
        to_xml_report_file(test_summary, [ts])


def main():
    args = parse_argument(sys.argv[1:])

    if args.local:
        license_names = get_local_licenses()
    else:
        license_names = get_github_licenses()
    if args.log_level <= INFO:
        print("Number of files to be checked:", len(license_names))
    errors_total = 0
    exit_status = 0
    for license_name in license_names:
        caught_errors = 0
        context_printed = False
        # Refer to issue for more info on samplingplus_1.0.br.htm:
        #   https://github.com/creativecommons/cc-link-checker/issues/9
        if license_name == "samplingplus_1.0.br.html":
            continue
        filename = license_name[: -len(".html")]
        base_url = create_base_link(args, filename)
        context = f"\n\nChecking: {license_name}\nURL: {base_url}"
        if args.local:
            source_html = request_local_text(license_name)
        else:
            page_url = "{}{}".format(GITHUB_BASE, license_name)
            source_html = request_text(page_url)
        license_soup = BeautifulSoup(source_html, "lxml")
        links_in_license = license_soup.find_all("a")
        link_count = len(links_in_license)
        if args.log_level <= INFO:
            print(f"{context}\nNumber of links found: {link_count}")
            context_printed = True
        valid_anchors, valid_links, context_printed = get_scrapable_links(
            args, base_url, links_in_license, context, context_printed
        )
        if valid_links:
            memoized_results = get_memoized_result(valid_links, valid_anchors)
            stored_links = memoized_results[0]
            stored_anchors = memoized_results[1]
            stored_result = memoized_results[2]
            check_links = memoized_results[3]
            check_anchors = memoized_results[4]
            if check_links:
                rs = (
                    # Since we're only checking for validity, we can retreive
                    # only the headers/metadata
                    grequests.head(link, timeout=REQUESTS_TIMEOUT)
                    for link in check_links
                )
                responses = list()
                # Explicitly close connections to free up file handles and
                # avoid Connection Errors per:
                # https://stackoverflow.com/a/22839550
                for response in grequests.map(
                    rs, exception_handler=exception_handler
                ):
                    try:
                        responses.append(response.status_code)
                        response.close()
                    except AttributeError:
                        responses.append(response)
                memoize_result(check_links, responses)
                stored_anchors += check_anchors
                stored_result += responses
            stored_links += check_links
            caught_errors = write_response(
                args,
                stored_links,
                stored_result,
                base_url,
                license_name,
                stored_anchors,
                context,
                context_printed,
            )

        if caught_errors:
            errors_total += caught_errors
            exit_status = 1

    print("\nCompleted in: {}".format(time.time() - START_TIME))

    if args.output_errors:
        output_summary(args, license_names, errors_total)
        print("\nError file present at: ", args.output_errors.name)
        output_test_summary(errors_total)

    sys.exit(exit_status)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        sys.exit(e.code)
    except KeyboardInterrupt:
        print("INFO (130) Halted via KeyboardInterrupt.", file=sys.stderr)
        sys.exit(130)
    except CheckerError:
        error_type, error_value, error_traceback = sys.exc_info()
        print("ERROR {}".format(error_value), file=sys.stderr)
        sys.exit(error_value.code)
    except:
        print("ERROR (1) Unhandled exception:", file=sys.stderr)
        print(traceback.print_exc(), file=sys.stderr)
        sys.exit(1)
