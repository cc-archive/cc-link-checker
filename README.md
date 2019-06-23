<h1 align="center">Creative Commons Link Checker</h1>
<p align="center">This python script scrapes all the <a href="https://github.com/creativecommons/creativecommons.org/tree/master/docroot/legalcode">license files</a> and automates the task of detecting broken links, timeout error and other link issues</p>

<p align="center">
<a href="https://circleci.com/gh/creativecommons/cc-link-checker"><img alt="CircleCI" src="https://img.shields.io/circleci/build/github/creativecommons/cc-link-checker.svg"></a> <a href="./LICENSE"><img alt="Licence: MIT" src="https://img.shields.io/github/license/creativecommons/cc-link-checker.svg"></a> <a href="https://github.com/python/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

## Table of Contents

- [Pre-requisite](#Pre-requisite)
- [Installation](#Installation)
  - [Local](#Local)
  - [Development](#Development)
- [Usage](#Usage)
  - [`-h` or `--help`](#-h-or---help)
  - [Default mode](#default-mode)
  - [`-v` or `--verbose`](#-v-or---verbose)
  - [`--output-error`](#--output-error)
- [Troubleshooting](#Troubleshooting)
- [Code of Conduct](#Code-of-Conduct)
- [Contributing](#Contributing)
- [License](#License)

## Pre-requisite

- Python3
- UTF-8 supported console

## Installation

There are two suggested ways of installation. Use [Local](#Local), if you are interested in just running the script. Use [Development](#Development), if you are interested in developing the script

### Local

1. Clone the repo

```
git clone https://github.com/creativecommons/cc-link-checker.git
```

2. Install dependencies  
   Using **requirements.txt**: `pip install -r requirements.txt`  
   Using **Pipfile** (requires [pipenv](https://github.com/pypa/pipenv)): `pipenv install`

### Development

We recommend using [pipenv](https://github.com/pypa/pipenv) to create a virtual environment and install dependencies

1. Clone the repo

```
git clone https://github.com/creativecommons/cc-link-checker.git
```

2. Create virtual environment and install all dependencies

```
pipenv install --dev
```

To install last successful environment: `pipenv install --dev --ignore-pipfile`

3. Activate project's virtual environment

```
pipenv shell
```

## Usage

### `-h` or `--help`

It provides the help text related to the script

```
$ python link_checker.py -h
usage: link_checker.py [-h] [-v] [--output-error [output_file]]

Script to check broken links

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Increase verbosity of output
  --output-error [output_file]
                        Outputs all link errors to file (default: errorlog.txt)

```

### Default mode

This mode shows which file is currently being checked along with errors encountered in the links

```
$ python link_checker.py
```

### `-v` or `--verbose`

This flag increases the verbosity of the output. This mode is useful for in-depth debugging

```
$ python link_checker.py -v
```

The output contains:

- File currently being checked
- Errors in the links
- Warnings in the link
- Skipped files and links

### `--output-error`

This flag outputs all the link errors to file. By default, the output is saved in file `errorlog.txt`

```
$ python link_checker.py --output-error
```

The output file can also be explicitly defined by passing a value to the flag

```
$ python link_checker.py --output-error output\results.txt
```

## Troubleshooting

- `UnicodeEncodeError`  
  This error is thrown when the console is not UTF-8 supported.

* Failing **Lint** build  
  Currently we follow customised [black](https://github.com/python/black) code style alongwith [flake8](https://gitlab.com/pycqa/flake8). The [black configuration](pyproject.toml) and [flake8 configuration](.flake8) are present in the repo. Do follow them to pass the CI build

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

We welcome contributions for bug fixes, enhancement and documentation. Please follow [`CONTRIBUTING.md`](CONTRIBUTING.md) while contributing.

## License

- [`LICENSE`](LICENSE) (Expat/[MIT][mit] License)

[mit]: http://www.opensource.org/licenses/MIT "The MIT License | Open Source Initiative"
