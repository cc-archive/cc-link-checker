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
    -   [`-h` or `--help`](#-h-or---help)
    -   [Default mode](#default-mode)
    -   [`-q` or `--quiet`](#-q-or---quiet)
    -   [`-v` or `--verbose`](#-v-or---verbose)
    -   [`--output-error`](#--output-error)
    -   [`--local`](#--local)
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

    ```shell
    pipenv install --dev
    ```

    - To install last successful environment:
      `pipenv install --dev --ignore-pipfile`

3. Either:
    - Activate project's virtual environment:
        ```shell
        pipenv shell
        ```
    - Run the script:
        ```shell
        pipenv run link_checker.py
        ```


## Usage

```shell
pipenv run link_checker -h
```

```
usage: link_checker.py [-h] [--legalcode] [--deeds] [--rdf] [--index] [--local]
                       [--output-errors [output_file]] [-q] [--root-url ROOT_URL]
                       [-v]
                       {legalcode,deeds,rdf} ...

Check for broken links in Creative Commons license deeds, legalcode, and rdf

positional arguments:
  {legalcode,deeds,rdf}
                        sub-command help
    legalcode           legalcode help
    deeds               deeds help
    rdf                 rdf help

optional arguments:
  -h, --help            show this help message and exit
  --legalcode           Runs link_checker for legalcode only. (Note: --licenses is
                        deprecated and will be dropped from a future release.
                        Please use --legalcode instead.)
  --deeds               Runs link_checker for deeds only (the legalcode files will
                        still be scraped, but not checked for broken links)
  --rdf                 Runs link_checker for rdf only
  --index               Runs link_checker for index.rdf only
  --local               Scrapes legalcode files from local file system
  --output-errors [output_file]
                        Outputs all link errors to file (default: errorlog.txt)
                        and creates junit-xml type summary(test-summary/junit-xml-
                        report.xml)
  -q, --quiet           Decrease verbosity. Can be specified multiple times.
  --root-url ROOT_URL   Set root URL (default: https://creativecommons.org)
  -v, --verbose         Increase verbosity. Can be specified multiple times.
```

### legalcode

```shell
pipenv run link_checker legalcode -h
```
```
usage: link_checker.py legalcode [-h] [--local]

optional arguments:
  -h, --help  show this help message and exit
  --local     Scrapes legalcode files from local file system. Add
              'LICENSE_LOCAL_PATH' to your environment, otherwise this tool will
              search for legalcode files in
              '../creativecommons.org/docroot/legalcode'.
```


### deeds

```shell
pipenv run link_checker deeds -h
```
```
usage: link_checker.py deeds [-h] [--local]

optional arguments:
  -h, --help  show this help message and exit
  --local     Scrapes deed files based on the legalcode files found on the local
              file system. Add 'LICENSE_LOCAL_PATH' to your environment, otherwise
              this tool will search for legalcode files in
              '../creativecommons.org/docroot/legalcode'.
```


### rdf

```shell
pipenv run link_checker rdf -h
```
```
usage: link_checker.py rdf [-h] [--local] [--index]

optional arguments:
  -h, --help  show this help message and exit
  --local     Scrapes rdf files based on the legalcode files found on the local
              file system. Add 'LICENSE_LOCAL_PATH' to your environment, otherwise
              this tool will search for legalcode files in
              '../creativecommons.org/docroot/legalcode'.
  --index     Checks index.rdf file instead of checking rdf files. If you want to
              check the index.rdf file locally add 'INDEX_RDF_LOCAL_PATH' to your
              environment; otherwise this variable defaults to './index.rdf'.
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
    ```shell
    pipenv install --dev
    ```
2. Run unit tests
    ```shell
    pipenv run pytest -v
    ```


## Troubleshooting

-   `UnicodeEncodeError`:

    This error is thrown when the console is not UTF-8 supported.

-   Failing **Lint** build:

    Currently we follow customised [black](https://github.com/python/black) code
    style alongwith [flake8](https://gitlab.com/pycqa/flake8). The [black
    configuration](pyproject.toml) and [flake8 configuration](.flake8) are
    present in the repo. Do follow them to pass the CI build:
    ```shell
    black ./
    ```
    ```
    flake8 ./
    ```


## Code of Conduct

[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md):

> The Creative Commons team is committed to fostering a welcoming community.
> This project and all other Creative Commons open source projects are governed
> by our [Code of Conduct][code_of_conduct]. Please report unacceptable
> behavior to [conduct@creativecommons.org](mailto:conduct@creativecommons.org)
> per our [reporting guidelines][reporting_guide].

[code_of_conduct]: https://opensource.creativecommons.org/community/code-of-conduct/
[reporting_guide]: https://opensource.creativecommons.org/community/code-of-conduct/enforcement/


## Contributing

We welcome contributions for bug fixes, enhancement and documentation. Please
follow [`CONTRIBUTING.md`](CONTRIBUTING.md) while contributing.


## License

-   [`LICENSE`](LICENSE) (Expat/[MIT][mit] License)

[mit]: http://www.opensource.org/licenses/MIT "The MIT License | Open Source Initiative"
