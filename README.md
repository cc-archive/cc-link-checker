
<h1 align="center">Creative Commons Link Checker</h1>
<p align="center">This python script scrapes all the <a href="https://github.com/creativecommons/creativecommons.org/tree/master/docroot/legalcode">license files</a> and automates the task of detecting broken links, timeout error and other link issues</p>

<p align="center">
<img alt="CircleCI" src="https://img.shields.io/circleci/build/github/creativecommons/cc-link-checker.svg"> <a href="./LICENSE"><img alt="Licence: MIT" src="https://img.shields.io/github/license/creativecommons/cc-link-checker.svg"></a> <a href="https://github.com/python/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a> <a href="https://www.codacy.com/app/bhumijgupta/cc-link-checker_2?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=creativecommons/cc-link-checker&amp;utm_campaign=Badge_Grade"><img src="https://api.codacy.com/project/badge/Grade/34a6db79b3d5412d9dadee0db8f3b773"/></a>
</p>

## Code of Conduct

[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md):
> The Creative Commons team is committed to fostering a welcoming community.
> This project and all other Creative Commons open source projects are governed
> by our [Code of Conduct][code_of_conduct]. Please report unacceptable
> behavior to [conduct@creativecommons.org](mailto:conduct@creativecommons.org)
> per our [reporting guidelines][reporting_guide].


[code_of_conduct]:https://creativecommons.github.io/community/code-of-conduct/
[reporting_guide]:https://creativecommons.github.io/community/code-of-conduct/enforcement/

## Pre-requisite

* Python3
* UTF-8 supported console

## Usage

1. Clone the repo
```
git clone https://github.com/creativecommons/cc-link-checker.git
```
2. Install Dependencies
```
pip install -r requirements.txt
```
3. Run the `link_checker.py` file
```
python ./link_checker.py
```

**Note**: If the console is not UTF-8 supported, the script would throw `UnicodeEncodeError`.

## Development

We recommend using [pipenv](https://github.com/pypa/pipenv) to create a virtual environment

1. Clone the repo
```
git clone https://github.com/creativecommons/cc-link-checker.git
```
2. Install Dependencies
```
pipenv install --dev
```
To install last successful environment:
```
pipenv install --dev --ignore-pipfile
```
3. Activate virtual environment
```
pipenv shell
```

## Contributing

We welcome contributions for bug fixes, enhancement and documentation. Please follow [`CONTRIBUTING.md`](CONTRIBUTING.md) while contributing. 

## Troubleshooting

* `UnicodeEncodeError`  
This error is thrown when the console is not UTF-8 supported.

* Failing Build  
Currently we follow [black](https://github.com/python/black) code style. To ensure consistent coding style,format code using black formatter


## License

- [`LICENSE`](LICENSE) (Expat/[MIT][mit] License)

[mit]: http://www.opensource.org/licenses/MIT "The MIT License | Open Source Initiative"
