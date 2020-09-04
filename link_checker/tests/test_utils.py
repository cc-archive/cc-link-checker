# Standard library
from urllib.parse import urlsplit

# Third-party
from bs4 import BeautifulSoup
import grequests
import pytest

# Local/library specific
from link_checker import utils
from link_checker import __main__ as link_checker
from ..utils import (
    CheckerError,
    get_github_legalcode,
    get_index_rdf,
    get_links_from_rdf,
    request_text,
    request_local_text,
    get_scrapable_links,
    create_base_link,
    create_absolute_link,
    get_memoized_result,
    exception_handler,
    map_links_file,
    memoize_result,
    write_response,
    output_summary,
    output_write,
    output_test_summary,
)
from link_checker import constants


@pytest.fixture
def reset_global():
    utils.MEMOIZED_LINKS = {}
    utils.MAP_BROKEN_LINKS = {}
    return


def test_get_github_legalcode():
    all_links = get_github_legalcode()
    assert len(all_links) > 0


license_url_data = [
    # 2 part URL
    (
        "by-nc-nd_2.0",
        "https://creativecommons.org/licenses/by-nc-nd/2.0/legalcode",
        "https://creativecommons.org/licenses/by-nc-nd/2.0/",
        "https://creativecommons.org/licenses/by-nc-nd/2.0/rdf",
    ),
    # 3 part URL
    (
        "by-nc-nd_4.0_cs",
        "https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.cs",
        "https://creativecommons.org/licenses/by-nc-nd/4.0/deed.cs",
        "https://creativecommons.org/licenses/by-nc-nd/4.0/rdf",
    ),
    # 4 part URL
    (
        "by-nc-nd_3.0_rs_sr-Latn",
        "https://creativecommons.org/licenses/by-nc-nd/3.0/rs/"
        "legalcode.sr-Latn",
        "https://creativecommons.org/licenses/by-nc-nd/3.0/rs/",
        "https://creativecommons.org/licenses/by-nc-nd/3.0/rs/rdf",
    ),
    # Special case - samplingplus
    (
        "samplingplus_1.0",
        "https://creativecommons.org/licenses/sampling+/1.0/legalcode",
        "https://creativecommons.org/licenses/sampling+/1.0/",
        "https://creativecommons.org/licenses/sampling+/1.0/rdf",
    ),
    (
        "samplingplus_1.0_br",
        "https://creativecommons.org/licenses/sampling+/1.0/br/legalcode",
        "https://creativecommons.org/licenses/sampling+/1.0/br/",
        "https://creativecommons.org/licenses/sampling+/1.0/br/rdf",
    ),
    # Special case - CC0
    (
        "zero_1.0",
        "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
        "https://creativecommons.org/publicdomain/zero/1.0/",
        "https://creativecommons.org/publicdomain/zero/1.0/rdf",
    ),
]


def id_generator(data):
    id_list = []
    for license in data:
        id_list.append(license[0])
    return id_list


@pytest.mark.parametrize(
    "filename, result, deed_result, rdf_result",
    license_url_data,
    ids=id_generator(license_url_data),
)
def test_create_base_link(filename, result, deed_result, rdf_result):
    args = link_checker.parse_argument([])
    baseURL = create_base_link(args, filename)
    assert baseURL == result
    baseURL = create_base_link(args, filename, for_deeds=True)
    assert baseURL == deed_result
    baseURL = create_base_link(args, filename, for_rdfs=True)
    assert baseURL == rdf_result


def test_output_write(tmpdir):
    # output_errors is set and written to
    output_file = tmpdir.join("errorlog.txt")
    args = link_checker.parse_argument(
        ["--output-errors", output_file.strpath]
    )
    output_write(args, "Output enabled")
    args.output_errors.flush()
    assert output_file.read() == "Output enabled\n"


def test_output_summary(reset_global, tmpdir):
    # output_errors is set and written to
    output_file = tmpdir.join("errorlog.txt")
    args = link_checker.parse_argument(
        ["--output-errors", output_file.strpath]
    )
    utils.MAP_BROKEN_LINKS = {
        "https://link1.demo": [
            "https://file1.url/here",
            "https://file2.url/goes/here",
        ],
        "https://link2.demo": ["https://file4.url/here"],
    }
    all_links = ["some link"] * 5
    output_summary(args, all_links, 3)
    args.output_errors.flush()
    lines = output_file.readlines()
    i = 0
    assert lines[i] == "\n"
    i += 1
    assert lines[i] == "\n"
    i += 1
    assert lines[i] == "***************************************\n"
    i += 1
    assert lines[i] == "                SUMMARY\n"
    i += 1
    assert lines[i] == "***************************************\n"
    i += 1
    assert lines[i] == "\n"
    i += 1
    assert str(lines[i]).startswith("Timestamp:")
    i += 1
    assert lines[i] == "Total files checked: 5\n"
    i += 1
    assert lines[i] == "Number of error links: 3\n"
    i += 1
    assert lines[i] == "Number of unique broken links: 2\n"
    i += 1
    assert lines[i] == "\n"
    i += 1
    assert lines[i] == "\n"
    i += 1
    assert lines[i] == "Broken link - https://link1.demo found in:\n"
    i += 1
    assert lines[i] == "https://file1.url/here\n"
    i += 1
    assert lines[i] == "https://file2.url/goes/here\n"
    i += 1
    assert lines[i] == "\n"
    i += 1
    assert lines[i] == "Broken link - https://link2.demo found in:\n"
    i += 1
    assert lines[i] == "https://file4.url/here\n"


@pytest.mark.parametrize(
    "link, result",
    [
        # relative links
        ("./license", "https://www.demourl.com/dir1/license"),
        ("../", "https://www.demourl.com/"),
        ("/index", "https://www.demourl.com/index"),
        # append https
        ("//demo.url", "https://demo.url"),
        # absolute link
        ("https://creativecommons.org", "https://creativecommons.org"),
    ],
)
def test_create_absolute_link(link, result):
    base_url = "https://www.demourl.com/dir1/dir2"
    analyze = urlsplit(link)
    res = create_absolute_link(base_url, analyze)
    assert res == result


def test_get_scrapable_links():
    args = link_checker.parse_argument([])
    test_file = (
        "<a name='hello'>without href</a>,"
        " <a href='#hello'>internal link</a>,"
        " <a href='mailto:abc@gmail.com'>mailto protocol</a>,"
        " <a href='https://creativecommons.ca'>Absolute link</a>,"
        " <a href='/index'>Relative Link</a>"
    )
    soup = BeautifulSoup(test_file, "lxml")
    test_case = soup.find_all("a")
    base_url = "https://www.demourl.com/dir1/dir2"
    valid_anchors, valid_links, _ = get_scrapable_links(
        args, base_url, test_case, None, False
    )
    assert str(valid_anchors) == (
        '[<a href="https://creativecommons.ca">Absolute link</a>,'
        ' <a href="/index">Relative Link</a>]'
    )
    assert (
        str(valid_links)
        == "['https://creativecommons.ca', 'https://www.demourl.com/index']"
    )
    # Testing RDF
    args = link_checker.parse_argument(["--local"])
    rdf_obj_list = get_index_rdf(
        args, local_path=constants.TEST_RDF_LOCAL_PATH
    )
    rdf_obj = rdf_obj_list[0]
    base_url = rdf_obj["rdf:about"]
    links_found = get_links_from_rdf(rdf_obj)
    valid_anchors, valid_links, _ = get_scrapable_links(
        args, base_url, links_found, None, False, rdf=True,
    )
    assert str(valid_anchors) == (
        "[<cc:permits "
        'rdf:resource="http://creativecommons.org/ns#DerivativeWorks"/>, '
        "<cc:permits "
        'rdf:resource="http://creativecommons.org/ns#Reproduction"/>, '
        "<cc:permits "
        'rdf:resource="http://creativecommons.org/ns#Distribution"/>, '
        "<cc:jurisdiction "
        'rdf:resource="http://creativecommons.org/international/ch/"/>, '
        "<foaf:logo "
        'rdf:resource="https://i.creativecommons.org/'
        'l/by-nc-sa/2.5/ch/88x31.png"/>, '
        "<foaf:logo "
        'rdf:resource="https://i.creativecommons.org/'
        'l/by-nc-sa/2.5/ch/80x15.png"/>, '
        "<cc:legalcode "
        'rdf:resource="http://creativecommons.org/'
        'licenses/by-nc-sa/2.5/ch/legalcode.de"/>, '
        "<dc:source "
        'rdf:resource="http://creativecommons.org/licenses/by-nc-sa/2.5/"/>, '
        "<dc:creator "
        'rdf:resource="http://creativecommons.org"/>, '
        "<cc:prohibits "
        'rdf:resource="http://creativecommons.org/ns#CommercialUse"/>, '
        "<cc:licenseClass "
        'rdf:resource="http://creativecommons.org/license/"/>, '
        "<cc:requires "
        'rdf:resource="http://creativecommons.org/ns#ShareAlike"/>, '
        "<cc:requires "
        'rdf:resource="http://creativecommons.org/ns#Attribution"/>, '
        "<cc:requires "
        'rdf:resource="http://creativecommons.org/ns#Notice"/>]'
    )
    assert str(valid_links) == (
        "['http://creativecommons.org/ns#DerivativeWorks', "
        "'http://creativecommons.org/ns#Reproduction', "
        "'http://creativecommons.org/ns#Distribution', "
        "'http://creativecommons.org/international/ch/', "
        "'https://i.creativecommons.org/l/by-nc-sa/2.5/ch/88x31.png', "
        "'https://i.creativecommons.org/l/by-nc-sa/2.5/ch/80x15.png', "
        "'http://creativecommons.org/licenses/by-nc-sa/2.5/ch/legalcode.de', "
        "'http://creativecommons.org/licenses/by-nc-sa/2.5/', "
        "'http://creativecommons.org', "
        "'http://creativecommons.org/ns#CommercialUse', "
        "'http://creativecommons.org/license/', "
        "'http://creativecommons.org/ns#ShareAlike', "
        "'http://creativecommons.org/ns#Attribution', "
        "'http://creativecommons.org/ns#Notice']"
    )


def test_exception_handler():
    links_list = [
        "http://invalid-example.creativecommons.org:81",
        "file://C:/Devil",
    ]
    rs = (grequests.get(link, timeout=3) for link in links_list)
    response = grequests.map(rs, exception_handler=exception_handler)
    assert response == ["Connection Error", "Invalid Schema"]


def test_map_links_file(reset_global):
    links = ["link1", "link2", "link1"]
    file_urls = ["file1", "file1", "file3"]
    for idx, link in enumerate(links):
        file_url = file_urls[idx]
        map_links_file(link, file_url)
    assert utils.MAP_BROKEN_LINKS == {
        "link1": ["file1", "file3"],
        "link2": ["file1"],
    }


def test_write_response(tmpdir):
    # Set config
    output_file = tmpdir.join("errorlog.txt")
    args = link_checker.parse_argument(
        ["--output-errors", output_file.strpath]
    )

    # Text to extract valid_anchors
    text = (
        "<a href='http://httpbin.org/status/200'>Response 200</a>,"
        " <a href='file://link3'>Invalid Scheme</a>,"
        " <a href='http://httpbin.org/status/400'>Response 400</a>"
    )
    soup = BeautifulSoup(text, "lxml")
    valid_anchors = soup.find_all("a")

    # Setup function params
    all_links = [
        "http://httpbin.org/status/200",
        "file://link3",
        "http://httpbin.org/status/400",
    ]
    rs = (grequests.get(link) for link in all_links)
    response = grequests.map(rs, exception_handler=exception_handler)
    base_url = "https://baseurl/goes/here"
    license_name = "by-cc-nd_2.0"

    # Set output to external file
    caught_errors = write_response(
        args,
        all_links,
        response,
        base_url,
        license_name,
        valid_anchors,
        license_name,
        False,
    )
    assert caught_errors == 2
    args.output_errors.flush()
    lines = output_file.readlines()
    i = 0
    assert lines[i] == "\n"
    i += 1
    assert lines[i] == "by-cc-nd_2.0\n"
    i += 1
    assert lines[i] == "URL: https://baseurl/goes/here\n"
    i += 1
    assert lines[i] == f'  {"Invalid Schema":<24}file://link3\n'
    i += 1
    assert lines[i] == f'{"":<26}<a href="file://link3">Invalid Scheme</a>\n'
    i += 1
    assert lines[i] == f'  {"400":<24}http://httpbin.org/status/400\n'
    i += 1
    assert lines[i] == (
        f'{"":<26}<a href="http://httpbin.org/status/400">Response 400</a>\n'
    )


def test_get_memoized_result(reset_global):
    text = (
        "<a href='link1'>Link 1</a>,"
        " <a href='link2'>Link 2</a>,"
        " <a href='link3_stored'>Link3 - stored</a>,"
        " <a href='link4_stored'>Link4 - stored</a>"
    )
    soup = BeautifulSoup(text, "lxml")
    valid_anchors = soup.find_all("a")
    valid_links = ["link1", "link2", "link3_stored", "link4_stored"]
    utils.MEMOIZED_LINKS = {"link3_stored": 200, "link4_stored": 404}
    (
        stored_links,
        stored_anchors,
        stored_result,
        check_links,
        check_anchors,
    ) = get_memoized_result(valid_links, valid_anchors)
    assert stored_links == ["link3_stored", "link4_stored"]
    assert str(stored_anchors) == (
        '[<a href="link3_stored">Link3 - stored</a>,'
        ' <a href="link4_stored">Link4 - stored</a>]'
    )
    assert stored_result == [200, 404]
    assert check_links == ["link1", "link2"]
    assert (
        str(check_anchors)
        == '[<a href="link1">Link 1</a>, <a href="link2">Link 2</a>]'
    )


def test_memoize_result(reset_global):
    check_links = [
        # Good response
        "https://httpbin.org/status/200",
        # Bad response
        "https://httpbin.org/status/400",
        # Invalid schema - Caught by exception handler
        "file://hh",
    ]
    rs = (grequests.get(link, timeout=3) for link in check_links)
    response = grequests.map(rs, exception_handler=exception_handler)
    memoize_result(check_links, response)
    assert len(utils.MEMOIZED_LINKS.keys()) == 3
    assert (
        utils.MEMOIZED_LINKS["https://httpbin.org/status/200"].status_code
        == 200
    )
    assert (
        utils.MEMOIZED_LINKS["https://httpbin.org/status/400"].status_code
        == 400
    )
    assert utils.MEMOIZED_LINKS["file://hh"] == "Invalid Schema"


@pytest.mark.parametrize(
    "URL, error",
    [
        ("https://www.google.com:82", "Timeout"),
        ("http://doesnotexist.google.com", "ConnectionError"),
    ],
)
def test_request_text(URL, error):
    with pytest.raises(CheckerError) as e:
        assert request_text(URL)
        assert str(e.value) == (
            "FAILED to retreive source HTML (https://www.google.com:82) due"
            " to {}".format(error)
        )


def test_request_local_text():
    random_string = "creativecommons cc-link-checker"
    with open("test_file.txt", "w") as test_file:
        test_file.write(random_string)
        test_file.close
    # Change local path to current directory
    constants.LICENSE_LOCAL_PATH = "./"
    assert (
        request_local_text(constants.LICENSE_LOCAL_PATH, "test_file.txt")
        == random_string
    )


# TODO: Optimize the test using mock
@pytest.mark.parametrize(
    "errors_total, map_links",
    [(3, {"link1": ["file1", "file3"], "link2": ["file1"]}), (0, {})],
)
def test_output_test_summary(errors_total, map_links, tmpdir):
    utils.MAP_BROKEN_LINKS = map_links
    output_test_summary(errors_total)
    with open("test-summary/junit-xml-report.xml", "r") as test_summary:
        if errors_total != 0:
            test_summary.readline()
            test_summary.readline()
            test_summary.readline()
            test_summary.readline()

            # The following is split up because sometimes message= is first and
            # sometimes type= is first (ex. local macOS dev versus GitHub
            # Actions Linux)
            test_line = test_summary.readline()
            assert test_line.startswith("\t\t\t<failure")
            assert 'message="3 broken links found"' in test_line
            assert 'type="failure"' in test_line
            assert test_line.endswith(">Number of error links: 3\n")

            assert (
                test_summary.readline()
                == "Number of unique broken links: 2</failure>\n"
            )
