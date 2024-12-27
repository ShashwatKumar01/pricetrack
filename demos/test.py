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
def fetch_myntra_price2(url):
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            print(soup)
            ptitle=soup.find_all('div',class_='pdp-price-info')
            pname = soup.find_all('h1', class_='pdp-name')
            price = soup.find_all('h1', class_='pdp-price')
            print (ptitle,pname,price)
    except Exception as e:
        print(e)
url='https://www.myntra.com/casual-shoes/highlander/highlander-men-lace-up-sneakers/21232226/buy'
fetch_myntra_price2(url)
list1={}
print(list1.get('gg'))