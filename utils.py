"""Utility functions 
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
    START_TIME,
    HEADER,
    MEMOIZED_LINKS,
    MAP_BROKEN_LINKS,
    GOOD_RESPONSE,
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


class CheckerError(Exception):
  def __init__(self, message, code=None):
      self.code = code if code else 1
      self.message = "({}) {}".format(self.code, message)
      super(CheckerError, self).__init__(self.message)

  def __str__(self):
      return self.message

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

def request_local_text(local_path, filename):
  """This function reads license, deed, or rdf content from the file stored in local
  file system

  Args:
      local_path (str): Path to license, deed, or rdf
      filename (str): Name of the license, deed, or rdf

  Returns:
      str: Content of license file
  """
  path = os.path.join(local_path, filename)
  try:
      with open(path) as lic:
          return lic.read()
  except FileNotFoundError:
      raise CheckerError(
          "Local file path({}) does not exist".format(path)
      )
  # Catching permission denied(OS ERROR) or other errors
  except:
      raise


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

def create_base_link(args, filename):
  """Generates base URL on which the license file will be displayed

  Args:
      filename (str): Name of the license file

  Returns:
      str: Base URL of the license file
  """
  parts = filename.split("_")

  license = parts.pop(0)
  if license == "samplingplus":
      license = "sampling+"

  version = parts.pop(0)

  jurisdiction = None
  language = None
  if license.startswith("zero"):
      path_base = "publicdomain"
  else:
      path_base = "licenses"
      if parts and float(version) < 4.0:
          jurisdiction = parts.pop(0)

  if parts:
      language = parts.pop(0)

  legalcode = "legalcode"
  if language:
      legalcode = f"{legalcode}.{language}"

  url = posixpath.join(args.root_url, path_base)
  url = posixpath.join(url, license)
  url = posixpath.join(url, version)

  if jurisdiction:
      url = posixpath.join(url, jurisdiction)

  url = posixpath.join(url, legalcode)

  return url


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
            result = "  {:<24}{}\n{}{}".format(
                str(status), all_links[idx], " " * 26, valid_anchors[idx]
            )
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
