import asyncio
import json
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
# async def main():
#     y=input('Enter URL: ')
#     # x=await fetch_flipkart_price(y)
#     # x=await fetch_myntra_price('https://myntr.in/r8Xu0a')
#     unshorturl= unshorten_url(y)
#     print(unshorturl)
#     platform=await check_platform(unshorturl)
#     x=await scrape(unshorturl,platform)
#
#     print(x)
# asyncio.run(main())

from python_flipkart_scraper import ExtractFlipkart
async def fetch_flipkart_price2(url):
    try:
        product=ExtractFlipkart(url)
        print(product)
        return ({
                        "name": product.get_title(),
                        "price": product.get_price(),
                        "product_image": product.get_images()[0]
                    })
    except Exception as e:
        print(f"Error fetching flipkart price: {e}")
        return {"error": f"An error occurred: {str(e)}"}
async def main():
    x = input('enter url: ')
    y=await fetch_flipkart_price2(x)
    print(y)
asyncio.run(main())