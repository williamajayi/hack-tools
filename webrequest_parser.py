#!/usr/bin/env python3

import argparse
import requests
import fileinput
import sys
import re
import json
from urllib.parse import urlparse, quote
from colorama import Fore, Back, Style
from bs4 import BeautifulSoup as bsoup

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# Function to handle self-signed certificates
def request_with_self_signed_cert(url, method, headers, data, verify, proxies, redirects):
    try:
        response = requests.request(
            method,
            url,
            headers=headers,
            data=data,
            verify=verify,
            proxies=proxies,
            allow_redirects=redirects
        )
        return response
    except requests.exceptions.SSLError as e:
        print(f"SSL certificate validation error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

def process_urls_from_file(file_path):
    with open(file_path, 'r') as file:
        urls = file.readlines()
    return urls

def search_tags(tags, response):
    s = bsoup(response, 'lxml')
    items = s.find_all(tags)
    for item in items:
        print(item)

def search_page(expr, response):
    s = bsoup(response, 'lxml')
    items = s.find_all(string=re.compile(expr))
    for item in items:
        x = re.search(expr, item)
        print(item)

def search_attribs(attribs, response):
    s = bsoup(response, 'lxml')
    attribute_name = attribs
    tags_with_attribute = s.find_all(attrs={attribute_name: True})
    # print(s.find(attrs={attribute_name: True}).name)
    for tags in tags_with_attribute:
        print(f"{tags.name}/{attribute_name}: {tags[attribute_name]}")

def main():
    parser = argparse.ArgumentParser(description="HTTP Request Parser Script")
    parser.add_argument("url", nargs="?", help="URL to request")
    parser.add_argument("-f", "--file", help="Read URLs from a file")
    parser.add_argument("-t", "--tags", help="Specify tags to parse")
    parser.add_argument("-a", "--attribs", help="Specify attributes to parse")
    parser.add_argument("-X", "--request", default="GET", help="Specify request method")
    parser.add_argument("-d", "--data", help="HTTP POST data")
    parser.add_argument("-s", "--search", help="Parse page for a string or regex")
    parser.add_argument("-H", "--header", action="append", help="HTTP headers")
    parser.add_argument("--proxy", help="Set a proxy (e.g., http://localhost:8080)")
    parser.add_argument("--insecure", action="store_true", help="Disable SSL certificate validation")
    parser.add_argument("--noredirects", action="store_true", help="Disable redirects")
    args = parser.parse_args()

    if not args.url and args.file:
        urls = process_urls_from_file(args.file)
    elif not args.url and not args.file and not sys.stdin.isatty():              # If no URLs provided as arguments or as a file, check stdin (piped input)
        # urls = [line.strip() for line in fileinput.input()]
        urls = sys.stdin
    elif not args.file and args.url:
        urls = [args.url]
    else:
        print("[-] You must specify a URL or provide a file with URLs.")
        return

    for url in urls:
        # Parse and encode the URL
        parsed_url = urlparse(url)
        encoded_url = f"{parsed_url.scheme}://{parsed_url.netloc}{quote(parsed_url.path)}"

        headers = {}
        if args.header:
            for header in args.header:
                key, value = header.split(":", 1)
                headers[key.strip()] = value.strip()

        if args.request not in ("GET", "POST", "PUT", "DELETE"):
            print("[-] Invalid request method. Supported methods are GET, POST, PUT, DELETE.")
            return

        if args.proxy:
            proxies = {"http": args.proxy, "https": args.proxy}
        else:
            proxies = None

        verify_ssl = not args.insecure
        redirects = not args.noredirects

        response = request_with_self_signed_cert(
            encoded_url,
            args.request,
            headers,
            args.data,
            verify_ssl,
            proxies,
            redirects
            )

        if args.tags and response.text:
            search_tags(args.tags, response.text)
        elif args.attribs and response.text:
            search_attribs(args.attribs, response.text)
        elif args.search and response.text:
            search_page(args.search, response.text)
        else:
            print("[-] Please specify HTML tags or attributes to parse!")
            print(f"Status Code: {response.status_code}")

        # if response:
        #     print(f"URL: {url}")
        #     print(f"Status Code: {response.status_code}")        
        #     for key, value in response.headers.items():
        #         print(f"{key}: {value}")
        #     print(f"\n\n{response.text}\n")

if __name__ == "__main__":
    main()
