import asyncio
import json
import re
import time
import urllib
from unshortenit import UnshortenIt

from scraper import *
apitoken=os.getenv('EARNKARO_API')
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


async def main():

    url=unshorten_url(input('enter url: '))
    plat=await check_platform(url)
    prduct=await scrape(url,plat)
    print(prduct)

asyncio.run(main())



