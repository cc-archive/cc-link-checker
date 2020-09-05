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
    LICENSE_LOCAL_PATH,
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
    output_summaries,
)


def parse_arguments():
    """parse arguments from CLI

    Args:
        args (list): list of arguments parsed from command line interface
    """

    # Primary argument parser and sub-parser (for subcommands)
    parser = argparse.ArgumentParser(
        prog="link_checker",
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Also see the help output each subcommand",
    )
    subparsers = parser.add_subparsers(
        title="subcommands (a single subcomamnd is required)",
        dest="subcommand",
        required=True,
    )

    # Shared Parsers

    # Shared parser (optional arguments used by all subcommands)
    parser_shared = argparse.ArgumentParser()
    parser_shared.add_argument(
        "-q",
        "--quiet",
        action="append_const",
        const=10,
        help="decrease verbosity (can be specified multiple times)",
        dest="verbosity",
    )
    parser_shared.add_argument(
        "--root-url",
        default=DEFAULT_ROOT_URL,
        help=f"set root URL (default: '{DEFAULT_ROOT_URL}')",
    )
    parser_shared.add_argument(
        "--limit",
        default=10,
        type=int,
        help=f"Limit check lists to specified integer (default: 10)",
    )
    parser_shared.add_argument(
        "-v",
        "--verbose",
        action="append_const",
        const=-10,
        help="increase verbosity (can be specified multiple times)",
        dest="verbosity",
    )

    # Shared licenses parser (optional arguments used by all license
    # subcommands)
    parser_shared_licenses = argparse.ArgumentParser(add_help=False)
    parser_shared_licenses.add_argument(
        "--local",
        action="store_true",
        help="process local filesystem legalcode files to determine valid"
        " license paths (uses LICENSE_LOCAL_PATH environment variable and"
        f" falls back to default: '{LICENSES_DIR}')",
    )

    # Shared reporting parser (optional arguments used by all reporting
    # subcommands)
    parser_shared_reporting = argparse.ArgumentParser(add_help=False)
    parser_shared_reporting.add_argument(
        "--output-errors",
        nargs="?",
        const="errorlog.txt",
        type=argparse.FileType("w", encoding="utf-8"),
        help="output all link errors to file (default: errorlog.txt) and"
        " create junit-xml type summary (test-summary/junit-xml-report.xml)",
        metavar="output_file",
    )

    # Shared RDF parser (optional arguments used by all RDF subcommands)
    parser_shared_rdf = argparse.ArgumentParser(add_help=False)
    parser_shared_rdf.add_argument(
        "--local-index",
        action="store_true",
        help="process local filesystem index.rdf (uses INDEX_RDF_LOCAL_PATH"
        " environment variable and falls back to default: './index.rdf')",
    )

    # Subcommands

    # Deeds subcommand: link_checker deeds -h
    parser_deeds = subparsers.add_parser(
        "deeds",
        add_help=False,
        help="check the links for each license's deed",
        parents=[
            parser_shared,
            parser_shared_licenses,
            parser_shared_reporting,
        ],
    )
    parser_deeds.set_defaults(func=check_deeds)

    # Legalcode subcommand: link_checker legalcode -h
    parser_legalcode = subparsers.add_parser(
        "legalcode",
        add_help=False,
        help="check the links for each license's legalcode",
        parents=[
            parser_shared,
            parser_shared_licenses,
            parser_shared_reporting,
        ],
    )
    parser_legalcode.set_defaults(func=check_legalcode)

    # RDF subcommand: link_checker rdf -h
    parser_rdf = subparsers.add_parser(
        "rdf",
        add_help=False,
        help="check the links for each license's RDF",
        parents=[
            parser_shared,
            parser_shared_licenses,
            parser_shared_rdf,
            parser_shared_reporting,
        ],
    )
    parser_rdf.set_defaults(func=check_rdfs)

    # index.rdf subcommand: link_checker index -h
    parser_index = subparsers.add_parser(
        "index",
        add_help=False,
        help="check the links within index.rdf",
        parents=[parser_shared, parser_shared_rdf, parser_shared_reporting],
    )
    parser_index.set_defaults(func=check_index_rdf)

    # combined subcommand: link_checker combined -h
    parser_combined = subparsers.add_parser(
        "combined",
        add_help=False,
        help="Combined check (deeds, legalcode, rdf, and index)",
        parents=[
            parser_shared,
            parser_shared_licenses,
            parser_shared_rdf,
            parser_shared_reporting,
        ],
    )
    parser_combined.set_defaults(func=check_combined)

    # Canonical License URLs subcommand: link_checker canonical -h
    parser_canonical = subparsers.add_parser(
        "canonical",
        add_help=False,
        help="print canonical license URLs",
        parents=[parser_shared, parser_shared_licenses],
    )
    parser_canonical.set_defaults(func=print_canonical)
    parser_canonical.add_argument(
        "--include-gnu",
        action="store_true",
        help="include GNU licenses in addition to Creative Commons licenses",
    )

    args = parser.parse_args()
    args.log_level = WARNING
    if args.verbosity:
        for v in args.verbosity:
            args.log_level += v
        if args.log_level < DEBUG:
            args.log_level = DEBUG
        elif args.log_level > CRITICAL:
            args.log_level = CRITICAL
    del args.verbosity
    if "output_errors" not in args or not args.output_errors:
        args.output_errors = None

    if args.log_level == DEBUG:
        print(f"DEBUG: args: {args}")

    return args


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
            context = f"\n\nChecking: deed\nURL: {deed_base_url}"
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

    return license_names, errors_total, exit_status


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
        context = f"\n\nChecking: legalcode\nURL: {base_url}"
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

    return license_names, errors_total, exit_status


def check_rdfs(args, index=False):
    if index:
        print("\n\nChecking index.rdf...\n\n")
        rdf_obj_list = get_index_rdf(args)
    else:
        print("\n\nChecking RDFs...\n\n")
        rdf_obj_list = get_rdf(args)
    if args.log_level <= INFO:
        if not index:
            print("Number of RDF files to be checked:", len(rdf_obj_list))
        else:
            print(
                "Number of RDF objects/sections to be checked in index.rdf:",
                len(rdf_obj_list),
            )
    errors_total = 0
    exit_status = 0
    for rdf_obj in rdf_obj_list:
        caught_errors = 0
        context_printed = False
        rdf_url = (
            rdf_obj["rdf:about"] if index else f"{rdf_obj['rdf:about']}rdf"
        )
        links_found = get_links_from_rdf(rdf_obj)
        checking = "URL" if not index else "RDF_ABOUT"
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

    return rdf_obj_list, errors_total, exit_status


def check_index_rdf(args):
    exit_status_list = check_rdfs(args, index=True)
    return license_names, errors_total, exit_status_list


def check_combined(args):
    print(
        "Running Full Inspection:"
        " Checking links for LegalCode, Deeds, RDF, and index.rdf"
    )
    license_names = []
    errors_total = 0
    exit_status = 0

    names, total, exit_status_legalcode = check_legalcode(args)
    license_names += names
    errors_total += total

    names, total, exit_status_deeds = check_deeds(args)
    license_names += names
    errors_total += total

    names, total, exit_status_rdf = check_rdfs(args)
    license_names += names
    errors_total += total

    names, total, exit_status_index_rdf = check_rdfs(args, index=True)
    license_names += names
    errors_total += total

    exit_status_list = [
        exit_status_legalcode,
        exit_status_deeds,
        exit_status_rdf,
        exit_status_index_rdf,
    ]
    if 1 in exit_status_list:
        exit_status = 1
    return license_names, errors_total, exit_status


def print_canonical(args):
    license_names = get_legalcode(args)
    grouped = [
        set(),  # 0: by* 4.0 licenses
        set(),  # 1: by* 3.0 licenses
        set(),  # 2: by* 2.5 licenses
        set(),  # 3: by* 2.1 licenses
        set(),  # 4: by* 2.0 licenses
        set(),  # 5: by* 1.x licenes
        set(),  # 6: miscellanious licenses
        set(),  # 7: zero 1.0 public domain
        set(),  # 8: miscellanious public domain
    ]
    for license_name in license_names:
        if not args.include_gnu:
            testname = license_name.lower()
            if testname.startswith("gpl") or testname.startswith("lgpl"):
                continue
        filename = license_name[: -len(".html")]
        url = create_base_link(args, filename, for_canonical=True)
        parts = url.split("/")
        bystar_starts = ("by", "nc", "nd", "sa")
        if parts[3] == "licenses" and parts[4].startswith(bystar_starts):
            if parts[5].startswith("4"):
                grouped[0].add(url)
            elif parts[5].startswith("3"):
                grouped[1].add(url)
            elif parts[5] == "2.5":
                grouped[2].add(url)
            elif parts[5] == "2.1":
                grouped[3].add(url)
            elif parts[5] == "2.0":
                grouped[4].add(url)
            elif parts[5].startswith("1"):
                grouped[5].add(url)
            else:
                grouped[6].add(url)
        elif parts[3] == "publicdomain" and parts[4] == "zero":
            grouped[7].add(url)
        else:
            grouped[8].add(url)
    for urls in grouped:
        urls = list(urls)
        urls.sort()
        for url in urls:
            print(url)
    return [], 0, 0


def main():
    args = parse_arguments()
    license_names, errors_total, exit_status = args.func(args)
    output_summaries(args, license_names, errors_total)
    if args.log_level <= INFO:
        print()
        print(f"Completed in: {time.time() - START_TIME:.2f} seconds")
    return sys.exit(exit_status)


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
