#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :

"""Check for broken links in Creative Commons license legalcode
"""

# Standard library
from urllib.parse import urljoin, urlsplit
import argparse
import os
import posixpath
import sys
import time
import traceback

# Third-party
from bs4 import BeautifulSoup
from junit_xml import TestCase, TestSuite, to_xml_report_file
import grequests  # WARNING: Always import grequests before requests
import requests

from constants import (
    REQUESTS_TIMEOUT,
    GITHUB_BASE,
    LICENSE_LOCAL_PATH,
    TEST_ORDER,
    DEFAULT_ROOT_URL,
    CRITICAL,
    ERROR,
    WARNING,
    INFO,
    DEBUG,
)

from utils import *

def parse_argument(arguments):
    """parse arguments from cli

    Args:
        args (list): list of arguments parsed from command line
    """
    # Setup argument parser
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--licenses",
        help="Runs link_checker for licenses only",
        action="store_true",
    )
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
    for link in soup.find_all("a", class_="js-navigation-open link-gray-dark"):
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

def check_licenses(args):
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
        filename = license_name[: -len(".html")]
        base_url = create_base_link(args, filename)
        context = f"\n\nChecking: {license_name}\nURL: {base_url}"
        if args.local:
            source_html = request_local_text(LICENSE_LOCAL_PATH, license_name)
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

def main():
    args = parse_argument(sys.argv[1:])
    if args.licenses:
        check_licenses(args)
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
