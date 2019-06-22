import argparse
import sys
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

# Set defaults
err_code = 0
verbose = False
output_err = False
header = {
    "User-Agent": "Mozilla/5.0 (X11; Linux i686 on x86_64; rv:10.0) Gecko/20100101 Firefox/10.0"
}
scraped_links = {}


parser = argparse.ArgumentParser(description="Script to check broken links")
parser.add_argument(
    "-v", "--verbose", help="Increase verbosity of output", action="store_true"
)
parser.add_argument(
    "--output-error",
    help="Output errors report to file (default: errorlog.txt)",
    metavar="output file",
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
    url = "https://github.com/creativecommons/creativecommons.org/tree/master/docroot/legalcode"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    links = soup.table.tbody.find_all("a", class_="js-navigation-open")
    print("No. of files to be checked:", len(links))
    return links


def check_existing(link):
    """This function checks if the link is already present in scraped_links.

    Args:
        link (bs4.element.Tag): The anchor tag extracted using BeautifulSoup which is to be checked

    Returns:
        String or Number: The status of the link
    """
    href = link["href"]
    status = scraped_links.get(href)
    if status:
        return status
    else:
        status = scrape(link)
        scraped_links[href] = status
        return status


def scrape(link):
    """Checks the status of the link and returns the status code 200 or the error encountered.

    Args:
        link (bs4.element.Tag): The anchor tag extracted using BeautifulSoup which is to be checked

    Returns:
        String or Number: Error encountered or Status code 200
    """
    href = link["href"]
    analyse = urlsplit(href)
    if analyse.scheme == "" or analyse.scheme in ["https", "http"]:
        if analyse.scheme == "":
            analyse = analyse._replace(scheme="https")
        if analyse.netloc == "":
            analyse = analyse._replace(netloc="creativecommons.org")
        href = analyse.geturl()
        try:
            res = requests.get(href, headers=header, timeout=10)
        except requests.exceptions.Timeout:
            return "Timeout Error"
        else:
            return res.status_code
    elif analyse.scheme == "mailto":
        return "ignore"
    else:
        return "Invalid protocol detected"


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


all_links = get_all_license()

base = "https://raw.githubusercontent.com/creativecommons/creativecommons.org/master/docroot/legalcode/"

for licens in all_links:
    caught_errors = 0
    check_extension = licens.string.split(".")
    page_url = base + licens.string
    print("\n")
    print("Checking:", licens.string)
    if check_extension[-1] not in ["html", "htm"]:
        verbose_print("Encountered non-html file -\t skipping", licens.string)
        continue
    source_html = requests.get(page_url, headers=header)
    license_soup = BeautifulSoup(source_html.content, "lxml")
    links_in_license = license_soup.find_all("a")
    verbose_print("No. of links found:", len(links_in_license))
    verbose_print("Errors and Warnings:")
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
        status = check_existing(link)
        if status not in [200, "ignore"]:
            caught_errors += 1
            if caught_errors == 1:
                if not verbose:
                    print("Errors:")
                output_write("\n{}".format(licens.string))
            err_code = 1
            print(status, "-\t", link)
            output_write(status, "-\t", link)

if output_err:
    print("\nError file present at: ", output.name)

sys.exit(err_code)
