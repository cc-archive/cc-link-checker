<h1 align="center">Creative Commons Link Checker</h1>
<p align="center">This python script scrapes all the <a href="https://github.com/creativecommons/creativecommons.org/tree/master/docroot/legalcode">license files</a> and automates the task of detecting broken links, timeout error and other link issues</p>

<p align="center">
<a href="https://circleci.com/gh/creativecommons/cc-link-checker"><img alt="CircleCI" src="https://img.shields.io/circleci/build/github/creativecommons/cc-link-checker.svg"></a> <a href="./LICENSE"><img alt="Licence: MIT" src="https://img.shields.io/github/license/creativecommons/cc-link-checker.svg"></a> <a href="https://github.com/python/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a> <a href="https://opensource.creativecommons.org/community/#slack"><img alt="chat: on Slack" src="https://img.shields.io/badge/chat-on%20Slack-blue"></a>
</p>

## Table of Contents

-   [Pre-requisite](#Pre-requisite)
-   [Installation](#Installation)
    -   [User](#User)
    -   [Development](#Development)
-   [Usage](#Usage)
    -   [`-h` or `--help`](#-h-or---help)
    -   [Default mode](#default-mode)
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
   Using **requirements.txt**: `pip install -r requirements.txt`  
   Using **Pipfile** (requires [pipenv](https://github.com/pypa/pipenv)): `pipenv install`

### Development

We recommend using [pipenv](https://github.com/pypa/pipenv) to create a virtual environment and install dependencies

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

### `-h` or `--help`

It provides the help text related to the script

```
$ python link_checker.py -h
Script to check broken links in CC licenses

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Increase verbosity of output
  --output-error [output_file]
                        Outputs all link errors to file (default:
                        errorlog.txt) and creates junit-xml type summary(test-
                        summary/junit-xml-report.xml)
  --local               Scrapes license files from local file system
```

### Default mode

This mode shows which file is currently being checked along with errors
encountered in the links

```shell
pipenv run link_checker.py
```

### `-v` or `--verbose`

This flag increases the verbosity of the output. This mode is useful for
in-depth debugging

```shell
pipenv run link_checker.py -v
```

The output contains:

-   File currently being checked
-   Errors in the links
-   Warnings in the link
-   Skipped files and links

### `--output-error`

This flag outputs all the link errors to file. By default, the output is saved
in file `errorlog.txt`

```shell
pipenv run link_checker.py --output-error
```

The output file can also be explicitly defined by passing a value to the flag

```shell
pipenv run link_checker.py --output-error output\results.txt
```

This flag also creates a `junit-xml` format summary of script run containing number of error links and number of unique error links.

The location of this file will be `test-summary/junit-xml-report.xml`. This xml file can be passed to CI to show failure result.

### `--local`

This flag allows script to test license files stored locally rather than fetching each license file from Github.

The relative directory structure should be:

```
/
├── cc-link-checker/
│   ├── link_checker.py
│   ├── Pipfile
│   ├── Pipfile.lock
│   .
|   .
|
├── creativecommons.org/
│   ├── docroot
|   |   ├── legalcode
|   |   |   ├── by-nc-nd_4.0.html
│   .   .   .
|   .   .   .
|
```

This mode can be helpful for using script as a CI.

**Note:** You can manually change the relative local path by changing `LICENSE_LOCAL_PATH` global variable in the script.

## Integrating with CI

Due to the script capability to scrape licenses from local storage, it can be used as CI in 2 easy steps:-

1. Clone this repo in the CI container

    ```shell
    git clone https://github.com/creativecommons/cc-link-checker.git ~/cc-link-checker
    ```

2. Run the `link_checker.py` in local(`--local`) and output error(`--output-error`) mode
    ```shell
    python link_checker.py --local --output-errors
    ```

The example configuration for **CircleCI** is present [here](examples/CircleCI/config.yml).

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

-   `UnicodeEncodeError`  
    This error is thrown when the console is not UTF-8 supported.

-   Failing **Lint** build  
    Currently we follow customised [black](https://github.com/python/black) code
    style alongwith [flake8](https://gitlab.com/pycqa/flake8). The [black
    configuration](pyproject.toml) and [flake8 configuration](.flake8) are
    present in the repo. Do follow them to pass the CI build

## Code of Conduct

[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md):

> The Creative Commons team is committed to fostering a welcoming community.
> This project and all other Creative Commons open source projects are governed
> by our [Code of Conduct][code_of_conduct]. Please report unacceptable
> behavior to [conduct@creativecommons.org](mailto:conduct@creativecommons.org)
> per our [reporting guidelines][reporting_guide].

[code_of_conduct]: https://creativecommons.github.io/community/code-of-conduct/
[reporting_guide]: https://creativecommons.github.io/community/code-of-conduct/enforcement/

## Contributing

We welcome contributions for bug fixes, enhancement and documentation. Please
follow [`CONTRIBUTING.md`](CONTRIBUTING.md) while contributing.

## License

-   [`LICENSE`](LICENSE) (Expat/[MIT][mit] License)

[mit]: http://www.opensource.org/licenses/MIT "The MIT License | Open Source Initiative"
