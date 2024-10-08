import string
from bs4 import BeautifulSoup
import urllib.request
import time
import os
import argparse
import re

API = "https://www.urbandictionary.com/browse.php?character={0}"

MAX_ATTEMPTS = 2
DELAY = 10

NUMBER_SIGN = "#"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
}

# Use the default opener with cookie support
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
urllib.request.install_opener(opener)

def extract_page_entries(letter, html):
    soup = BeautifulSoup(html, "html.parser")

    # Updated parsing logic
    # Find the <ul> element that contains the words
    ul_list = soup.find('ul', {'class': 'mt-3 columns-2 md:columns-3'})
    if not ul_list:
        print("No <ul> with the expected class found.")
        return

    for li in ul_list.find_all('li'):
        a_tag = li.find('a')
        if a_tag and a_tag.text:
            a = a_tag.text.strip()
            if letter == NUMBER_SIGN:
                if not re.match('^[a-zA-Z]', a):
                    yield a
            else:
                if a.lower().startswith(letter.lower()):
                    yield a

def get_next(letter, html):
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.find('a', attrs={"aria-label": "Next page"})
    if next_link:
        href = next_link.get('href')
        return 'https://www.urbandictionary.com' + href
    return None

def extract_letter_entries(letter):
    if letter == NUMBER_SIGN:
        start = '*'  # Urban Dictionary uses '*' for non-alphabetic characters.
    else:
        start = letter
    url = API.format(start)
    attempt = 0
    while url:
        print(f"Fetching URL: {url}")
        try:
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req)
            code = response.getcode()
            if code == 200:
                content = response.read().decode('utf-8')
                entries = list(extract_page_entries(letter, content))
                if entries:
                    yield entries
                else:
                    print(f"No entries found on page: {url}")
                    # Stop fetching next pages if no entries are found
                    break
                url = get_next(letter, content)
                attempt = 0
            else:
                print(f"Trying again, expected response code: 200, got {code}")
                attempt += 1
                if attempt > MAX_ATTEMPTS:
                    break
                time.sleep(DELAY * attempt)
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            attempt += 1
            if attempt > MAX_ATTEMPTS:
                break
            time.sleep(DELAY * attempt)
        time.sleep(DELAY)

def download_letter_entries(letter, file, verbose=False):
    file = file.format(letter)
    directory = os.path.dirname(file)
    if directory:
        os.makedirs(directory, exist_ok=True)
    for entry_set in extract_letter_entries(letter):
        if verbose:
            for word in entry_set:
                print(word)
        with open(file, 'a', encoding='utf-8') as f:
            data = ('\n'.join(entry_set))
            f.write(data + '\n')

def download_entries(letters, file, verbose=False):
    for letter in letters:
        print(f"======= {letter} =======")
        download_letter_entries(letter, file, verbose)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape words from Urban Dictionary.')

    parser.add_argument('--ifile', dest='ifile',
                        help='Input file name. Contains a list of letters separated by a newline', default="input.list")

    parser.add_argument('--out', dest='out',
                        help='Output file name. May be a format string', default="{0}.data")

    parser.add_argument('--verbose', action='store_true',
                        help='Print scraped words to stdout')

    args = parser.parse_args()

    letters = []
    with open(args.ifile, 'r') as ifile:
        for row in ifile:
            letters.append(row.strip())

    download_entries(letters, args.out, verbose=args.verbose)
