<h1 align="center">Creative Commons Link Checker</h1>
<p align="center">This python script scrapes all the <a href="https://github.com/creativecommons/creativecommons.org/tree/master/docroot/legalcode">license files</a> and automates the task of detecting broken links, timeout error and other link issues</p>

<p align="center">
<a href="https://github.com/creativecommons/cc-link-checker/actions"><img src="https://github.com/creativecommons/cc-link-checker/workflows/unitAndLint/badge.svg" alt="unitAndLint"></a> <a href="./LICENSE"><img alt="Licence: MIT" src="https://img.shields.io/github/license/creativecommons/cc-link-checker.svg"></a> <a href="https://github.com/python/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a> <a href="https://opensource.creativecommons.org/community/#slack"><img alt="chat: on Slack" src="https://img.shields.io/badge/chat-on%20Slack-blue"></a>
</p>


## Table of Contents

-   [Pre-requisite](#Pre-requisite)
-   [Installation](#Installation)
    -   [User](#User)
    -   [Development](#Development)
-   [Usage](#Usage)
    -   [deeds](#deeds)
    -   [legalcode](#legalcode)
    -   [rdf](#rdf)
    -   [index](#index)
    -   [combined](#combined)
    -   [canonical](#canonical)
-   [Integrating with CI](#Integrating-with-CI)
-   [Unit Testing](#Unit-Testing)
-   [Troubleshooting](#Troubleshooting)
-   [Code of Conduct](#Code-of-Conduct)
-   [Contributing](#Contributing)
-   [License](#License)


## Pre-requisite

-   Python3
-   UTF-8 supported console


## Installation

There are two suggested ways of installation. Use [User](#User), if you are
interested in just running the script. Use [Development](#Development), if you
are interested in developing the script


### User

1. Clone the repo
    ```shell
    git clone https://github.com/creativecommons/cc-link-checker.git
    ```
2. Install dependencies
   Using **Pipfile** (requires [pipenv](https://github.com/pypa/pipenv)): `pipenv install`


### Development

We recommend using [pipenv](https://github.com/pypa/pipenv) to create a virtual
environment and install dependencies

1. Clone the repo
    ```shell
    git clone https://github.com/creativecommons/cc-link-checker.git
    ```
2. Create virtual environment and install all dependencies
   - Normal
        ```shell
        pipenv install --dev
        ```
    - Use `sync` to install last successful environment. For example:
        ```shell
        pipenv sync --dev
        ```
3. Run the script:
    ```shell
    pipenv run link_checker
    ```


## Usage

```shell
pipenv run link_checker -h
```
```
usage: link_checker [-h] {deeds,legalcode,rdf,index,combined,canonical} ...

Check for broken links in Creative Commons license deeds, legalcode, and rdf

optional arguments:
  -h, --help            show this help message and exit

subcommands (a single subcomamnd is required):
  {deeds,legalcode,rdf,index,combined,canonical}
    deeds               check the links for each license's deed
    legalcode           check the links for each license's legalcode
    rdf                 check the links for each license's RDF
    index               check the links within index.rdf
    combined            Combined check (deeds, legalcode, rdf, and index)
    canonical           print canonical license URLs

Also see the help output each subcommand
```


### deeds

```shell
pipenv run link_checker deeds -h
```
```
usage: link_checker deeds [-h] [-q] [--root-url ROOT_URL] [--limit LIMIT] [-v]
                          [--local] [--output-errors [output_file]]

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           decrease verbosity (can be specified multiple times)
  --root-url ROOT_URL   set root URL (default: 'https://creativecommons.org')
  --limit LIMIT         Limit check lists to specified integer (default: 10)
  -v, --verbose         increase verbosity (can be specified multiple times)
  --local               process local filesystem legalcode files to determine
                        valid license paths (uses LICENSE_LOCAL_PATH environment
                        variable and falls back to default:
                        '../creativecommons.org/docroot/legalcode')
  --output-errors [output_file]
                        output all link errors to file (default: errorlog.txt) and
                        create junit-xml type summary (test-summary/junit-xml-
                        report.xml)
```


### legalcode

```shell
pipenv run link_checker legalcode -h
```
```
usage: link_checker legalcode [-h] [-q] [--root-url ROOT_URL] [--limit LIMIT] [-v]
                              [--local] [--output-errors [output_file]]

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           decrease verbosity (can be specified multiple times)
  --root-url ROOT_URL   set root URL (default: 'https://creativecommons.org')
  --limit LIMIT         Limit check lists to specified integer (default: 10)
  -v, --verbose         increase verbosity (can be specified multiple times)
  --local               process local filesystem legalcode files to determine
                        valid license paths (uses LICENSE_LOCAL_PATH environment
                        variable and falls back to default:
                        '../creativecommons.org/docroot/legalcode')
  --output-errors [output_file]
                        output all link errors to file (default: errorlog.txt) and
                        create junit-xml type summary (test-summary/junit-xml-
                        report.xml)
```


### rdf

```shell
pipenv run link_checker rdf -h
```
```
usage: link_checker rdf [-h] [-q] [--root-url ROOT_URL] [--limit LIMIT] [-v]
                        [--local] [--local-index] [--output-errors [output_file]]

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           decrease verbosity (can be specified multiple times)
  --root-url ROOT_URL   set root URL (default: 'https://creativecommons.org')
  --limit LIMIT         Limit check lists to specified integer (default: 10)
  -v, --verbose         increase verbosity (can be specified multiple times)
  --local               process local filesystem legalcode files to determine
                        valid license paths (uses LICENSE_LOCAL_PATH environment
                        variable and falls back to default:
                        '../creativecommons.org/docroot/legalcode')
  --local-index         process local filesystem index.rdf (uses
                        INDEX_RDF_LOCAL_PATH environment variable and falls back
                        to default: './index.rdf')
  --output-errors [output_file]
                        output all link errors to file (default: errorlog.txt) and
                        create junit-xml type summary (test-summary/junit-xml-
                        report.xml)
```


### index

```shell
pipenv run link_checker index -h
```
```
usage: link_checker index [-h] [-q] [--root-url ROOT_URL] [--limit LIMIT] [-v]
                          [--local-index] [--output-errors [output_file]]

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           decrease verbosity (can be specified multiple times)
  --root-url ROOT_URL   set root URL (default: 'https://creativecommons.org')
  --limit LIMIT         Limit check lists to specified integer (default: 10)
  -v, --verbose         increase verbosity (can be specified multiple times)
  --local-index         process local filesystem index.rdf (uses
                        INDEX_RDF_LOCAL_PATH environment variable and falls back
                        to default: './index.rdf')
  --output-errors [output_file]
                        output all link errors to file (default: errorlog.txt) and
                        create junit-xml type summary (test-summary/junit-xml-
                        report.xml)
```


### combined

```shell
pipenv run link_checker combined -h
```
```
usage: link_checker combined [-h] [-q] [--root-url ROOT_URL] [--limit LIMIT] [-v]
                             [--local] [--local-index]
                             [--output-errors [output_file]]

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           decrease verbosity (can be specified multiple times)
  --root-url ROOT_URL   set root URL (default: 'https://creativecommons.org')
  --limit LIMIT         Limit check lists to specified integer (default: 10)
  -v, --verbose         increase verbosity (can be specified multiple times)
  --local               process local filesystem legalcode files to determine
                        valid license paths (uses LICENSE_LOCAL_PATH environment
                        variable and falls back to default:
                        '../creativecommons.org/docroot/legalcode')
  --local-index         process local filesystem index.rdf (uses
                        INDEX_RDF_LOCAL_PATH environment variable and falls back
                        to default: './index.rdf')
  --output-errors [output_file]
                        output all link errors to file (default: errorlog.txt) and
                        create junit-xml type summary (test-summary/junit-xml-
                        report.xml)
```


### canonical

```shell
pipenv run link_checker canonical -h
```
```
usage: link_checker canonical [-h] [-q] [--root-url ROOT_URL] [--limit LIMIT] [-v]
                              [--local] [--include-gnu]

optional arguments:
  -h, --help           show this help message and exit
  -q, --quiet          decrease verbosity (can be specified multiple times)
  --root-url ROOT_URL  set root URL (default: 'https://creativecommons.org')
  --limit LIMIT        Limit check lists to specified integer
  -v, --verbose        increase verbosity (can be specified multiple times)
  --local              process local filesystem legalcode files to determine valid
                       license paths (uses LICENSE_LOCAL_PATH environment variable
                       and falls back to default:
                       '../creativecommons.org/docroot/legalcode')
  --include-gnu        include GNU licenses in addition to Creative Commons
                       licenses
```


## Integrating with CI

Due to the script capability to scrape licenses from local storage, it can be
used as CI in 2 easy steps:

1. Clone this repo in the CI container

    ```shell
    git clone https://github.com/creativecommons/cc-link-checker.git ~/cc-link-checker
    ```

2. Run the `link_checker.py` in local(`--local`) and
   output error(`--output-error`) mode
    ```shell
    python link_checker.py --local --output-errors
    ```

The configuration for **GitHub Actions**, for example, is present
[here](.github/workflows/unitAndLint.yaml).


## Unit Testing

Unit tests have been written using [pytest](https://docs.pytest.org/en/latest/)
framework. The tests can be run using:

1. Install dev dependencies
   - macOS with Homebrew
        ```shell
        pipenv install --dev --python /usr/local/opt/python@3.7/libexec/bin/python
        ```
   - General
        ```shell
        pipenv install --dev
        ```
2. Run unit tests
    ```shell
    pipenv run pytest -v
    ```

### Tooling

- **[Python Guidelines — Creative Commons Open Source][ccospyguide]**
- [Black][black]: the uncompromising Python code formatter
- [flake8][flake8]: a python tool that glues together pep8, pyflakes, mccabe,
  and third-party plugins to check the style and quality of some python code.
- [isort][isort]: A Python utility / library to sort imports.

[ccospyguide]: https://opensource.creativecommons.org/contributing-code/python-guidelines/
[black]: https://github.com/psf/black
[flake8]: https://gitlab.com/pycqa/flake8
[isort]: https://pycqa.github.io/isort/


## Troubleshooting

-   `UnicodeEncodeError`:

    This error is thrown when the console is not UTF-8 supported.

-   Failing **Lint** build:

    Ensure style/syntax is correct:
    ```shell
    pipenv run black .
    ```
    ```shell
    pipenv run isort .
    ```
    ```
    pipenv run flake8 .
    ```


## Code of conduct

[`CODE_OF_CONDUCT.md`][org-coc]:
> The Creative Commons team is committed to fostering a welcoming community.
> This project and all other Creative Commons open source projects are governed
> by our [Code of Conduct][code_of_conduct]. Please report unacceptable
> behavior to [conduct@creativecommons.org](mailto:conduct@creativecommons.org)
> per our [reporting guidelines][reporting_guide].

[org-coc]: https://github.com/creativecommons/.github/blob/main/CODE_OF_CONDUCT.md
[code_of_conduct]: https://opensource.creativecommons.org/community/code-of-conduct/
[reporting_guide]: https://opensource.creativecommons.org/community/code-of-conduct/enforcement/


## Contributing

We welcome contributions for bug fixes, enhancement and documentation. Please see [`CONTRIBUTING.md`][org-contrib] while contributing..

[org-contrib]: https://github.com/creativecommons/.github/blob/main/CONTRIBUTING.md


## License

-   [`LICENSE`](LICENSE) (Expat/[MIT][mit] License)

[mit]: http://www.opensource.org/licenses/MIT "The MIT License | Open Source Initiative"
