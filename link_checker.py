import requests
from bs4 import BeautifulSoup
from urllib.parse import *

header = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux i686 on x86_64; rv:10.0) Gecko/20100101 Firefox/10.0'
}

scraped_links = {}


def get_all_license():
    """
    This function scrapes all the license file in the repo 'https://github.com/creativecommons/creativecommons.org/tree/master/docroot/legalcode'.
    """
    url = 'https://github.com/creativecommons/creativecommons.org/tree/master/docroot/legalcode'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    links = soup.table.tbody.find_all("a", class_="js-navigation-open")
    print("No. of files to be checked:", len(links))
    return links


def check_existing(link):
    """
    This function checks if the link is already present in scraped_links.
    """
    href = link['href']
    status = scraped_links.get(href)
    if(status):
        return status
    else:
        status = scrape(link)
        scraped_links[href] = status
        return status


def scrape(link):
    """
    Checks the status of the link and returns the status code 200 or the error encountered.
    """
    href = link['href']
    analyse = urlsplit(href)
    if(analyse.scheme == '' or analyse.scheme in ['https', 'http']):
        if(analyse.scheme == ''):
            analyse = analyse._replace(scheme='https')
        if(analyse.netloc == ''):
            analyse = analyse._replace(netloc='creativecommons.org')
        href = analyse.geturl()
        try:
            res = requests.get(href, headers=header, timeout=10)
        except requests.exceptions.Timeout:
            return "Timeout Error"
        else:
            return res.status_code
    else:
        return "Invalid protocol detected"


all_links = get_all_license()

base = 'https://raw.githubusercontent.com/creativecommons/creativecommons.org/master/docroot/legalcode/'

for licens in all_links:
    check_extension = licens.string.split('.')
    page_url = base + licens.string
    print("\n")
    print("Checking:",  licens.string)
    if(check_extension[-1] == 'txt'):
        print('Encountered txt file -\t skipping', licens.string)
        continue
    source_html = requests.get(page_url, headers=header)
    license_soup = BeautifulSoup(source_html.content, 'lxml')
    links_in_license = license_soup.find_all('a')
    print("No. of links found:", len(links_in_license))
    print("Errors:")
    for link in links_in_license:
        try:
            href = link['href']
        except KeyError:
            # if there exists an <a> tag without href
            print("Found anchor tag without href -\t", link)
            continue
        if(href[0] == '#'):
            print("Skipping internal link -\t", link)
            continue
        status = check_existing(link)
        if(status != 200):
            print(status, "-\t", link)
