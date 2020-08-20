#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

"""Check for broken links in Creative Commons license deeds, legalcode, and rdf
"""

# Standard library
import argparse
import sys
import time
import traceback

# Third-party
from bs4 import BeautifulSoup
import grequests  # WARNING: Always import grequests before requests

# Local
from link_checker.constants import (
    REQUESTS_TIMEOUT,
    START_TIME,
    LICENSE_GITHUB_BASE,
    LICENSES_DIR,
    DEFAULT_ROOT_URL,
    CRITICAL,
    WARNING,
    INFO,
    DEBUG,
)

from link_checker.utils import (
    CheckerError,
    get_legalcode,
    get_rdf,
    get_index_rdf,
    request_text,
    request_local_text,
    get_scrapable_links,
    get_links_from_rdf,
    create_base_link,
    get_memoized_result,
    exception_handler,
    memoize_result,
    write_response,
    output_summary,
    output_test_summary,
)


def parse_argument(arguments):
    """parse arguments from cli

    Args:
        args (list): list of arguments parsed from command line
    """
    # Setup argument parser
    parser = argparse.ArgumentParser(
        prog="link_checker.py", description=__doc__
    )
    parser.add_argument(
        "--legalcode",
        help="Runs link_checker for legalcode only. (Note: --licenses is"
        " deprecated and will be dropped from a future release. Please use"
        " --legalcode instead.)",
        action="store_true",
    )
    parser.add_argument(
        "--deeds",
        help="Runs link_checker for deeds only (the legalcode files will still"
        " be scraped, but not checked for broken links)",
        action="store_true",
    )
    parser.add_argument(
        "--rdf", help="Runs link_checker for rdf only", action="store_true"
    )
    parser.add_argument(
        "--index",
        help="Runs link_checker for index.rdf only",
        action="store_true",
    )
    parser.add_argument(
        "--local",
        help="Scrapes legalcode files from local file system",
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
    # Sub-Parser Section
    subparsers = parser.add_subparsers(help="sub-command help")
    # legalcode section: link_checker legalcode -h
    parser_legalcode = subparsers.add_parser("legalcode", help="legalcode help")
    parser_legalcode.add_argument(
        "--local",
        help=(
            "Scrapes legalcode files from local file system.\n"
            "Add 'LICENSE_LOCAL_PATH' to your environment,\n"
            "otherwise this tool will search for legalcode files\n"
            f"in '{LICENSES_DIR}'."
        ),
        action="store_true",
    )
    parser_legalcode.set_defaults(func=check_legalcode)
    # deeds section: link_checker deeds -h
    parser_deeds = subparsers.add_parser("deeds", help="deeds help")
    parser_deeds.add_argument(
        "--local",
        help=(
            "Scrapes deed files based on the legalcode files found on the local file system.\n"
            "Add 'LICENSE_LOCAL_PATH' to your environment,\n"
            "otherwise this tool will search for legalcode files\n"
            f"in '{LICENSES_DIR}'."
        ),
        action="store_true",
    )
    parser_deeds.set_defaults(func=check_deeds)
    # rdf section: link_checker rdf -h
    parser_rdf = subparsers.add_parser("rdf", help="rdf help")
    parser_rdf.add_argument(
        "--local",
        help=(
            "Scrapes rdf files based on the legalcode files found on the local file system.\n"
            "Add 'LICENSE_LOCAL_PATH' to your environment,\n"
            "otherwise this tool will search for legalcode files\n"
            f"in '{LICENSES_DIR}'."
        ),
        action="store_true",
    )
    parser_rdf.add_argument(
        "--index",
        help=(
            "Checks index.rdf file instead of checking rdf files.\n"
            "If you want to check the index.rdf file locally add\n"
            "'INDEX_RDF_LOCAL_PATH' to your environment; otherwise this\n"
            "variable defaults to './index.rdf'."
        ),
        action="store_true",
    )
    parser_rdf.set_defaults(func=check_rdfs)


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


def check_legalcode(args):
    print("\n\nChecking LegalCode License...\n\n")
    license_names = get_legalcode(args)
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
            page_url = "{}{}".format(LICENSE_GITHUB_BASE, license_name)
            source_html = request_text(page_url)
        license_soup = BeautifulSoup(source_html, "lxml")
        links_found = license_soup.find_all("a")
        link_count = len(links_found)
        if args.log_level <= INFO:
            print(f"{context}\nNumber of links found: {link_count}")
            context_printed = True
        valid_anchors, valid_links, context_printed = get_scrapable_links(
            args, base_url, links_found, context, context_printed
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

    return [exit_status, 0, 0]


def check_deeds(args):
    print("\n\nChecking Deeds...\n\n")
    license_names = get_legalcode(args)
    if args.log_level <= INFO:
        print("Number of files to be checked:", len(license_names))
    errors_total = 0
    exit_status = 0
    for license_name in license_names:
        caught_errors = 0
        context_printed = False
        filename = license_name[: -len(".html")]
        deed_base_url = create_base_link(args, filename, for_deeds=True)
        # Deeds template:
        # https://github.com/creativecommons/cc.engine/blob/master/
        # cc/engine/templates/legalcode/standard_deed.html
        # Scrapping the html found on the active site
        if deed_base_url:
            context = f"\n\nChecking: \nURL: {deed_base_url}"
            page_url = deed_base_url
            source_html = request_text(page_url)
            license_soup = BeautifulSoup(source_html, "lxml")
            links_found = license_soup.find_all("a")
            link_count = len(links_found)
            if args.log_level <= INFO:
                print(f"{context}\nNumber of links found: {link_count}")
                context_printed = True
            base_url = deed_base_url
            valid_anchors, valid_links, context_printed = get_scrapable_links(
                args, base_url, links_found, context, context_printed
            )
            if valid_links:
                memoized_results = get_memoized_result(
                    valid_links, valid_anchors
                )
                stored_links = memoized_results[0]
                stored_anchors = memoized_results[1]
                stored_result = memoized_results[2]

                check_links = memoized_results[3]
                check_anchors = memoized_results[4]
                if check_links:
                    rs = (
                        # Since we're only checking for validity,
                        # we can retreive
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

    return [0, exit_status, 0]


def check_rdfs(args):
    if args.index:
        print("\n\nChecking index.rdf...\n\n")
        rdf_obj_list = get_index_rdf(args)
    else:
        print("\n\nChecking RDFs...\n\n")
        rdf_obj_list = get_rdf(args)
    if args.log_level <= INFO:
        if not args.index:
            print("Number of rdf files to be checked:", len(rdf_obj_list))
        else:
            print(
                "Number of rdf objects/sections to be checked in index.rdf:",
                len(rdf_obj_list),
            )
    errors_total = 0
    exit_status = 0
    for rdf_obj in rdf_obj_list:
        caught_errors = 0
        context_printed = False
        rdf_url = (
            rdf_obj["rdf:about"]
            if args.index
            else f'{rdf_obj["rdf:about"]}rdf'
        )
        links_found = get_links_from_rdf(rdf_obj)
        checking = "URL" if not args.index else "RDF_ABOUT"
        context = f"\n\nChecking: \n{checking}: {rdf_url}"
        link_count = len(links_found)
        if args.log_level <= INFO:
            print(f"{context}\nNumber of links found: {link_count}")
            context_printed = True
        base_url = rdf_url
        valid_anchors, valid_links, context_printed = get_scrapable_links(
            args, base_url, links_found, context, context_printed, rdf=True,
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
                    # Since we're only checking for validity,
                    # we can retreive
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
                rdf_url,
                rdf_obj,
                stored_anchors,
                context,
                context_printed,
            )

        if caught_errors:
            errors_total += caught_errors
            exit_status = 1

    print("\nCompleted in: {}".format(time.time() - START_TIME))

    if args.output_errors:
        output_summary(args, rdf_obj_list, errors_total)
        print("\nError file present at: ", args.output_errors.name)
        output_test_summary(errors_total)

    return [0, 0, exit_status]


def main():
    args = parse_argument(sys.argv[1:])
    print(args)
    exit_status_list = []
    if args.legalcode:
        exit_status_list = check_legalcode(args)
    if args.deeds:
        exit_status_list = check_deeds(args)
    if args.rdf:
        exit_status_list = check_rdfs(args)
    else:
        print(
            "\nRunning Full Inspection:"
            " Checking Links for LegalCode, Deed, RDF, and index.rdf files"
        )
        exit_status_legalcode, y, z = check_legalcode(args)
        x, exit_status_deeds, z = check_deeds(args)
        x, y, exit_status_rdf = check_rdfs(args)
        args.index = True
        x, y, exit_status_index_rdf = check_rdfs(args)
        exit_status_list = [
            exit_status_legalcode,
            exit_status_deeds,
            exit_status_rdf,
            exit_status_index_rdf,
        ]
    if 1 in exit_status_list:
        return sys.exit(1)
    return sys.exit(0)


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
