import pytest
from urllib.parse import urlsplit
import link_checker
from bs4 import BeautifulSoup
import grequests


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


def test_verbose_print(capsys):
    # verbose = False (default)
    link_checker.verbose_print("Without verbose")
    # Set verbose True
    link_checker.verbose = True
    link_checker.verbose_print("With verbose")
    captured = capsys.readouterr()
    assert captured.out == "With verbose\n"


def test_output_write(capsys):
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


def test_exception_handler():
    links_list = ["http://www.google.com:81", "file://C:/Devil"]
    rs = (grequests.get(link, timeout=3) for link in links_list)
    response = grequests.map(
        rs, exception_handler=link_checker.exception_handler
    )
    assert response == ["Timeout Error", "Invalid Schema"]
