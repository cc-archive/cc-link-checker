"""Constants File
"""
import time

# Set defaults
START_TIME = time.time()
HEADER = {
    "User-Agent": "Mozilla/5.0 (X11; Linux i686 on x86_64; rv:10.0)"
    " Gecko/20100101 Firefox/10.0"
}
MEMOIZED_LINKS = {}
MAP_BROKEN_LINKS = {}
GOOD_RESPONSE = [200, 300, 301, 302]
REQUESTS_TIMEOUT = 5
LICENSE_GITHUB_BASE = (
    "https://raw.githubusercontent.com/creativecommons/creativecommons.org"
    "/master/docroot/legalcode/"
)
LICENSE_LOCAL_PATH = "../creativecommons.org/docroot/legalcode"
INDEX_RDF_LOCAL_PATH = './index.rdf'
TEST_RDF_LOCAL_PATH = './test.rdf'
DEED_LOCAL_PATH = ""
LANGUAGE_CODE_REGEX = r"[a-zA-Z_-]*"
TEST_ORDER = ["zero", "4.0", "3.0", "2.5", "2.1", "2.0"]
DEFAULT_ROOT_URL = "https://creativecommons.org"
CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
