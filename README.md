# cc-link-checker

Creative Commons Link Checker  
This is a python script which detects broken links in license/deeds files.

![CircleCI](https://img.shields.io/circleci/build/github/creativecommons/cc-link-checker.svg) ![GitHub](https://img.shields.io/github/license/creativecommons/cc-link-checker.svg) <a href="https://github.com/python/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

## Code of Conduct

[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md):
> The Creative Commons team is committed to fostering a welcoming community.
> This project and all other Creative Commons open source projects are governed
> by our [Code of Conduct][code_of_conduct]. Please report unacceptable
> behavior to [conduct@creativecommons.org](mailto:conduct@creativecommons.org)
> per our [reporting guidelines][reporting_guide].


[code_of_conduct]:https://creativecommons.github.io/community/code-of-conduct/
[reporting_guide]:https://creativecommons.github.io/community/code-of-conduct/enforcement/


## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Pre-requisite

* Python3
* UTF-8 supported console

## Install

1. Clone the repo: `git clone https://github.com/creativecommons/cc-link-checker.git`
2. Run: `pip install -r requirements.txt`
3. Run: `python ./link_checker.py`

**Note**: If the console is not UTF-8 supported, the script would throw `UnicodeEncodeError`.

## License

- [`LICENSE`](LICENSE) (Expat/[MIT][mit] License)

[mit]: http://www.opensource.org/licenses/MIT "The MIT License | Open Source Initiative"
