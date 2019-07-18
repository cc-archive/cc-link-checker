import pytest
from urllib.parse import urlsplit
import link_checker
from bs4 import BeautifulSoup
import grequests


@pytest.fixture
def reset_global():
    link_checker.verbose = False
    link_checker.output_err = False
    link_checker.memoized_links = {}
    link_checker.map_broken_links = {}
    return


def test_parse_argument(reset_global):
    link_checker.parse_argument(["-v", "--output-error"])
    assert link_checker.verbose is True
    assert link_checker.output_err is True
    assert link_checker.output.name == "errorlog.txt"
    link_checker.verbose = False
    link_checker.output_err = False
    link_checker.parse_argument(
        ["--verbose", "--output-error", "err_file.txt"]
    )
    assert link_checker.verbose is True
    assert link_checker.output_err is True
    assert link_checker.output.name == "err_file.txt"


def test_get_all_license():
    all_links = link_checker.get_all_license()
    assert len(all_links) > 0


@pytest.mark.parametrize(
    "filename, result",
    [
        # 2 part URL
        (
            "by-nc-nd_2.0",
            "https://creativecommons.org/licenses/by-nc-nd/2.0/legalcode",
        ),
        # 3 part URL
        (
            "by-nc-nd_4.0_cs",
            "https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode.cs",
        ),
        # 4 part URL
        (
            "by-nc-nd_3.0_rs_sr-Latn",
            "https://creativecommons.org/licenses/by-nc-nd/3.0/rs/legalcode.sr-Latn",
        ),
        # Special case - samplingplus
        (
            "samplingplus_1.0",
            "https://creativecommons.org/licenses/sampling+/1.0/legalcode",
        ),
        (
            "samplingplus_1.0_br",
            "https://creativecommons.org/licenses/sampling+/1.0/br/legalcode",
        ),
        # Special case - CC0
        (
            "zero_1.0",
            "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
        ),
    ],
)
def test_create_base_link(filename, result):
    baseURL = link_checker.create_base_link(filename)
    assert baseURL == result


def test_verbose_print(capsys, reset_global):
    # verbose = False (default)
    link_checker.verbose_print("Without verbose")
    # Set verbose True
    link_checker.verbose = True
    link_checker.verbose_print("With verbose")
    captured = capsys.readouterr()
    assert captured.out == "With verbose\n"


def test_output_write(reset_global):
    # output_err = False (default)
    link_checker.output_write("Output disabled")
    # Set output_err True
    link_checker.output_err = True
    with open("errorlog.txt", "w+") as output_file:
        link_checker.output = output_file
        link_checker.output_write("Output enabled")
        # Seek to start of buffer
        output_file.seek(0)
        assert output_file.read() == "Output enabled\n"


def test_output_summary(reset_global):
    # Set config
    link_checker.output_err = True
    link_checker.all_links = ["some link"] * 5
    link_checker.map_broken_links = {
        "https://link1.demo": [
            "https://file1.url/here",
            "https://file2.url/goes/here",
        ],
        "https://link2.demo": ["https://file4.url/here"],
    }

    # Open file for writing
    with open("errorlog.txt", "w+") as output_file:
        link_checker.output = output_file
        link_checker.output_summary(3)
        output_file.seek(0)
        assert output_file.readline() == "\n"
        assert output_file.readline() == "\n"
        assert (
            output_file.readline()
            == "***************************************\n"
        )
        assert output_file.readline() == "                SUMMARY\n"
        assert (
            output_file.readline()
            == "***************************************\n"
        )
        assert output_file.readline() == "\n"
        assert str(output_file.readline()).startswith("Timestamp:")
        assert output_file.readline() == "Total files checked: 5\n"
        assert output_file.readline() == "Number of error links: 3\n"
        assert output_file.readline() == "Number of unique broken links: 2\n"
        assert output_file.readline() == "\n"
        assert output_file.readline() == "\n"
        assert (
            output_file.readline()
            == "Broken link - https://link1.demo found in:\n"
        )
        assert output_file.readline() == "https://file1.url/here\n"
        assert output_file.readline() == "https://file2.url/goes/here\n"
        assert output_file.readline() == "\n"
        assert (
            output_file.readline()
            == "Broken link - https://link2.demo found in:\n"
        )
        assert output_file.readline() == "https://file4.url/here\n"

    # Reset non global values
    link_checker.all_links = []


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
    link_checker.base_url = "https://www.demourl.com/dir1/dir2"
    analyze = urlsplit(link)
    res = link_checker.create_absolute_link(analyze)
    assert res == result


def test_get_scrapable_links():
    test_file = "<a name='hello'>without href</a>, <a href='#hello'>internal link</a>, <a href='mailto:abc@gmail.com'>mailto protocol</a>, <a href='https://creativecommons.ca'>Absolute link</a>, <a href='/index'>Relative Link</a>"
    soup = BeautifulSoup(test_file, "lxml")
    test_case = soup.find_all("a")
    link_checker.base_url = "https://www.demourl.com/dir1/dir2"
    valid_anchors, valid_links = link_checker.get_scrapable_links(test_case)
    assert (
        str(valid_anchors)
        == '[<a href="https://creativecommons.ca">Absolute link</a>, <a href="/index">Relative Link</a>]'
    )
    assert (
        str(valid_links)
        == "['https://creativecommons.ca', 'https://www.demourl.com/index']"
    )


def test_exception_handler():
    links_list = ["http://www.google.com:81", "file://C:/Devil"]
    rs = (grequests.get(link, timeout=3) for link in links_list)
    response = grequests.map(
        rs, exception_handler=link_checker.exception_handler
    )
    assert response == ["Timeout Error", "Invalid Schema"]


def test_map_links_file(reset_global):
    links = ["link1", "link2", "link1"]
    file_urls = ["file1", "file1", "file3"]
    for idx, link in enumerate(links):
        file_url = file_urls[idx]
        link_checker.map_links_file(link, file_url)
    assert link_checker.map_broken_links == {
        "link1": ["file1", "file3"],
        "link2": ["file1"],
    }


def test_write_response(reset_global):
    # Set config
    link_checker.output_err = True

    # Text to extract valid_anchors
    text = "<a href='http://httpbin.org/status/200'>Response 200</a>, <a href='file://link3'>Invalid Scheme</a>, <a href='http://httpbin.org/status/400'>Response 400</a>"
    soup = BeautifulSoup(text, "lxml")
    valid_anchors = soup.find_all("a")

    # Setup function params
    all_links = [
        "http://httpbin.org/status/200",
        "file://link3",
        "http://httpbin.org/status/400",
    ]
    rs = (grequests.get(link) for link in all_links)
    response = grequests.map(
        rs, exception_handler=link_checker.exception_handler
    )
    base_url = "https://baseurl/goes/here"
    license_name = "by-cc-nd_2.0"

    # Set output to external file
    with open("errorlog.txt", "w+") as output_file:
        link_checker.output = output_file
        caught_errors = link_checker.write_response(
            all_links, response, base_url, license_name, valid_anchors
        )
        assert caught_errors == 2
        output_file.seek(0)
        assert output_file.readline() == "\n"
        assert output_file.readline() == "by-cc-nd_2.0\n"
        assert output_file.readline() == "URL: https://baseurl/goes/here\n"
        assert (
            output_file.readline()
            == 'Invalid Schema -\t <a href="file://link3">Invalid Scheme</a>\n'
        )
        assert (
            output_file.readline()
            == '400 -\t <a href="http://httpbin.org/status/400">Response 400</a>\n'
        )


def test_get_memoized_result():
    text = "<a href='link1'>Link 1</a>, <a href='link2'>Link 2</a>, <a href='link3_stored'>Link3 - stored</a>, <a href='link4_stored'>Link4 - stored</a>"
    soup = BeautifulSoup(text, "lxml")
    valid_anchors = soup.find_all("a")
    valid_links = ["link1", "link2", "link3_stored", "link4_stored"]
    link_checker.memoized_links = {"link3_stored": 200, "link4_stored": 404}
    stored_links, stored_anchors, stored_result, check_links, check_anchors = link_checker.get_memoized_result(
        valid_links, valid_anchors
    )
    assert stored_links == ["link3_stored", "link4_stored"]
    assert (
        str(stored_anchors)
        == '[<a href="link3_stored">Link3 - stored</a>, <a href="link4_stored">Link4 - stored</a>]'
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
    rs = (grequests.get(link, timeout=1) for link in check_links)
    response = grequests.map(
        rs, exception_handler=link_checker.exception_handler
    )
    link_checker.memoize_result(check_links, response)
    assert len(link_checker.memoized_links.keys()) == 3
    assert (
        link_checker.memoized_links[
            "https://httpbin.org/status/200"
        ].status_code
        == 200
    )
    assert (
        link_checker.memoized_links[
            "https://httpbin.org/status/400"
        ].status_code
        == 400
    )
    assert link_checker.memoized_links["file://hh"] == "Invalid Schema"
