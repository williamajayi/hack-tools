#!/usr/bin/env python3

import argparse
import requests
import fileinput
import sys
import json
from bs4 import BeautifulSoup as bsoup
from urllib.parse import urlparse, quote
from colorama import Fore, Back, Style 

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
            allow_redirects=redirects,
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

def main():
    parser = argparse.ArgumentParser(description="HTTP Request Script")
    parser.add_argument("url", nargs="?", help="URL to request")
    parser.add_argument("-f", "--file", help="Read URLs from a file")
    parser.add_argument("-X", "--request", default="GET", help="Specify request method")
    parser.add_argument("-d", "--data", help="HTTP POST data")
    parser.add_argument("-H", "--header", action="append", help="HTTP headers")
    parser.add_argument("-p", "--print", help="Specify output to print, h for header, b for body")
    parser.add_argument("--proxy", help="Set a proxy (e.g., http://localhost:8080)")
    parser.add_argument("--insecure", action="store_true", help="Disable SSL certificate validation")
    parser.add_argument("--noredirects", action="store_true", help="Disable redirects")
    args = parser.parse_args()

    if not args.url and args.file:
        urls = process_urls_from_file(args.file)
    elif not args.url and not args.file and not sys.stdin.isatty():              # If no URLs provided as arguments or as a file, check stdin (piped input)
        urls = sys.stdin
    elif not args.file and args.url:
        urls = [args.url]
    else:
        print("[-] - You must specify a URL or provide a file with URLs.")
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
            print("Invalid request method. Supported methods are GET, POST, PUT, DELETE.")
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
            redirects,
            )

        if response:
            print(f"URL: {encoded_url} - [{response.status_code}]\n")

            if args.print and args.print=='h':        
                for key, value in response.headers.items():
                    print(f"{key}: {value}")
            elif args.print and args.print=='b': 
                soup = bsoup(response.text, 'lxml')
                print(f"\n\n{soup.prettify()}\n")
            else:
                for key, value in response.headers.items():
                    print(f"{key}: {value}")
                soup = bsoup(response.text, 'lxml')
                print(f"\n\n{soup.prettify()}\n")


if __name__ == "__main__":
    main()
