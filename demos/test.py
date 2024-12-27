import asyncio
import json
import re
import time
import urllib

from unshortenit import UnshortenIt

from scraper import *
def unshorten_url(short_url):
    unshortener = UnshortenIt()
    shorturi =  unshortener.unshorten(short_url)
    if ('linkredirect') in shorturi:
        parsed_url = urllib.parse.urlparse(shorturi)
        # Extract query parameters
        query_params = urllib.parse.parse_qs(parsed_url.query)
        # Get the 'dl' parameter, which contains the original link
        original_link = query_params.get('dl', [None])[0]
        shorturi=urllib.parse.unquote(original_link)
    # print(shorturi)
    return shorturi

def findid(url):
    url=unshorten_url(url)
    flipkart_pattern = r"flipkart\.com(?:\/.*\/.*)?\?pid=([\w-]+)"
    ajio_pattern = r"https:\/\/www\.ajio\.com(?:.*\/)?p\/([\w-]+)(?=\W|$)"
    myntra_pattern = r"https:\/\/www\.myntra\.com(?:\/.*)?\/(\d+)\/?"

    # flipkart_match = re.match(flipkart_pattern, url)
    # ajio_match = re.match(ajio_pattern, url)
    # myntra_match = re.match(myntra_pattern, url)
    if 'flipkart' in url:
        flipkart_match = re.search(flipkart_pattern, url)
        if flipkart_match:
            return {"platform": "flipkart", "product_id": flipkart_match.group(1)}

    elif 'ajio' in url:
        ajio_match = re.search(ajio_pattern, url)
        if ajio_match:
            return {"platform": "ajio", "product_id": ajio_match.group(1)}
    elif 'myntra' in url:
        myntra_match = re.search(myntra_pattern, url)
        if myntra_match:
            return {"platform": "myntra", "product_id": myntra_match.group(1)}
    elif 'amazon' in url:
        product_code_match = re.search(r"/product/([A-Za-z0-9]{10})", url)
        product_code_match2 = re.search(r'/dp/([A-Za-z0-9]{10})', url)
        product_code = product_code_match.group(1) if product_code_match else product_code_match2.group(1)
        return {"platform": "myntra", "product_id": product_code}
for i in range(1):
    x=input('enter: ')
    print(findid(x))