import string
from bs4 import BeautifulSoup
import urllib.request
import time
import os
import argparse
import re

API = "https://www.urbandictionary.com/browse.php?character={0}"

MAX_ATTEMPTS = 4
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
    columnist = soup.find(id="columnist")
    if not columnist:
        return
    ul_list = columnist.find('ul')
    if not ul_list:
        return
    for li in ul_list.find_all('li'):
        a_tag = li.find('a')
        if a_tag and a_tag.string:
            a = a_tag.string
            if letter == NUMBER_SIGN:
                if not re.match('[a-zA-Z]', a):
                    yield a
            else:
                if a.lower().startswith(letter.lower()):
                    yield a

def get_next(letter, html):
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.find('a', {"rel": "next"})
    if next_link:
        href = next_link['href']
        return 'https://www.urbandictionary.com' + href
    return None

def extract_letter_entries(letter):
    if letter == NUMBER_SIGN:
        start = '*'  # URL-encoded '#'
    else:
        start = letter + 'a'
    url = API.format(start)
    attempt = 0
    while url:
        print(url)
        try:
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req)
            code = response.getcode()
            if code == 200:
                content = response.read().decode('utf-8')
                yield list(extract_page_entries(letter, content))
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
            break
        time.sleep(DELAY)

def download_letter_entries(letter, file):
    file = file.format(letter)
    directory = os.path.dirname(file)
    if directory:
        os.makedirs(directory, exist_ok=True)
    for entry_set in extract_letter_entries(letter):
        with open(file, 'a', encoding='utf-8') as f:
            data = ('\n'.join(entry_set))
            f.write(data + '\n')

def download_entries(letters, file):
    for letter in letters:
        print(f"======={letter}=======")
        download_letter_entries(letter, file)

parser = argparse.ArgumentParser(description='Process some integers.')

parser.add_argument('--ifile', dest='ifile',
                    help='Input file name. Contains a list of letters separated by a newline', default="input.list")

parser.add_argument('--out', dest='out',
                    help='Output file name. May be a format string', default="data/{0}.data")

args = parser.parse_args()

letters = []
with open(args.ifile, 'r') as ifile:
    for row in ifile:
        letters.append(row.strip())

download_entries(letters, args.out)
