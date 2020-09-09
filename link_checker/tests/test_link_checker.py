# Local/library specific
from link_checker import __main__ as link_checker


def test_parser_shared():
    subcmds = ["deeds", "legalcode", "rdf", "index", "combined", "canonical"]

    # Test defaults
    for subcmd in subcmds:
        args = link_checker.parse_arguments([subcmd])
        assert args.limit == 0
        assert args.log_level == 30
        assert args.root_url == "https://creativecommons.org"

    # Test arguments
    for subcmd in subcmds:
        # Test --limit
        args = link_checker.parse_arguments([subcmd, "--limit", "10"])
        assert args.limit == 10
        args = link_checker.parse_arguments([subcmd, "--limit=100"])
        assert args.limit == 100
        # Test Logging Levels -q/--quiet
        args = link_checker.parse_arguments([subcmd, "-q"])
        assert args.log_level == 40
        args = link_checker.parse_arguments([subcmd, "-qq"])
        assert args.log_level == 50
        args = link_checker.parse_arguments([subcmd, "-qqq"])
        assert args.log_level == 50
        args = link_checker.parse_arguments([subcmd, "-q", "--quiet"])
        assert args.log_level == 50
        # Test Logging Levels -v/--verbose
        args = link_checker.parse_arguments([subcmd, "-v"])
        assert args.log_level == 20
        args = link_checker.parse_arguments([subcmd, "-vv"])
        assert args.log_level == 10
        args = link_checker.parse_arguments([subcmd, "-vvv"])
        assert args.log_level == 10
        args = link_checker.parse_arguments([subcmd, "-v", "--verbose"])
        assert args.log_level == 10
        # Test Logging Levels with both -v and -q
        args = link_checker.parse_arguments([subcmd, "-vq"])
        assert args.log_level == 30
        args = link_checker.parse_arguments([subcmd, "-vvq"])
        assert args.log_level == 20
        args = link_checker.parse_arguments([subcmd, "-vqq"])
        assert args.log_level == 40
        # Test --root-url
        args = link_checker.parse_arguments(
            [subcmd, "--root-url", "https://pytest.creativecommons.org"]
        )
        assert args.root_url == "https://pytest.creativecommons.org"


def test_parser_shared_licenses():
    subcmds = ["deeds", "legalcode", "rdf", "combined", "canonical"]

    # Test defaults
    for subcmd in subcmds:
        args = link_checker.parse_arguments([subcmd])
        assert args.local is False

    # Test argumetns
    for subcmd in subcmds:
        # Test --local
        args = link_checker.parse_arguments([subcmd, "--local"])
        assert args.local is True


def test_parser_shared_rdf():
    subcmds = ["rdf", "index"]

    # Test defaults
    for subcmd in subcmds:
        args = link_checker.parse_arguments([subcmd])
        assert args.local_index is False

    # Test argumetns
    for subcmd in subcmds:
        # Test --local
        args = link_checker.parse_arguments([subcmd, "--local-index"])
        assert args.local_index is True


def test_parser_shared_reporting(tmpdir):
    subcmds = ["deeds", "legalcode", "rdf", "index", "combined"]

    # Test defaults
    for subcmd in subcmds:
        args = link_checker.parse_arguments([subcmd])
        assert bool(args.output_errors) is False

    # Test arguments
    for subcmd in subcmds:
        # Test --output-errors with default value
        args = link_checker.parse_arguments([subcmd, "--output-errors"])
        assert bool(args.output_errors) is True
        assert args.output_errors.name == "errorlog.txt"
        # Test --output-errors with custom value
        output_file = tmpdir.join("errorlog.txt")
        args = link_checker.parse_arguments(
            [subcmd, "--output-errors", output_file.strpath]
        )
        assert bool(args.output_errors) is True
        assert args.output_errors.name == output_file.strpath
