# Local/library specific
from link_checker import __main__ as link_checker


def test_parse_argument(tmpdir):
    # Test default options
    args = link_checker.parse_argument([])
    assert args.log_level == 30
    assert bool(args.output_errors) is False
    assert args.local is False
    assert args.root_url == "https://creativecommons.org"
    # Test --licenses
    args = link_checker.parse_argument(["--legalcode"])
    assert args.legalcode is True
    args = link_checker.parse_argument(["legalcode"])
    assert args.func.__name__ == "check_legalcode"
    args = link_checker.parse_argument(["legalcode", "--local"])
    assert args.local is True
    # Test --deeds
    args = link_checker.parse_argument(["--deeds"])
    assert args.deeds is True
    args = link_checker.parse_argument(["deeds"])
    assert args.func.__name__ == "check_deeds"
    args = link_checker.parse_argument(["deeds", "--local"])
    assert args.local is True
    # Test --rdf
    args = link_checker.parse_argument(["--rdf"])
    assert args.rdf is True
    args = link_checker.parse_argument(["rdf"])
    assert args.func.__name__ == "check_rdfs"
    args = link_checker.parse_argument(["rdf", "--index"])
    assert args.index is True
    args = link_checker.parse_argument(["rdf", "--local"])
    assert args.local is True
    # Test --index
    args = link_checker.parse_argument(["--index"])
    assert args.index is True
    # Test --local
    args = link_checker.parse_argument(["--local"])
    assert args.local is True
    # Test Logging Levels -q/--quiet
    args = link_checker.parse_argument(["-q"])
    assert args.log_level == 40
    args = link_checker.parse_argument(["-qq"])
    assert args.log_level == 50
    args = link_checker.parse_argument(["-qqq"])
    assert args.log_level == 50
    args = link_checker.parse_argument(["-q", "--quiet"])
    assert args.log_level == 50
    # Test Logging Levels -v/--verbose
    args = link_checker.parse_argument(["-v"])
    assert args.log_level == 20
    args = link_checker.parse_argument(["-vv"])
    assert args.log_level == 10
    args = link_checker.parse_argument(["-vvv"])
    assert args.log_level == 10
    args = link_checker.parse_argument(["-v", "--verbose"])
    assert args.log_level == 10
    # Test Logging Levels with both -v and -q
    args = link_checker.parse_argument(["-vq"])
    assert args.log_level == 30
    args = link_checker.parse_argument(["-vvq"])
    assert args.log_level == 20
    args = link_checker.parse_argument(["-vqq"])
    assert args.log_level == 40
    # Test default value of --output-errors
    args = link_checker.parse_argument(["--output-errors"])
    assert bool(args.output_errors) is True
    assert args.output_errors.name == "errorlog.txt"
    # Test custom value of --output-errors
    output_file = tmpdir.join("errorlog.txt")
    args = link_checker.parse_argument(
        ["--output-errors", output_file.strpath]
    )
    assert bool(args.output_errors) is True
    assert args.output_errors.name == output_file.strpath
