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

from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

def fetch_myntra_price(url):
    with sync_playwright() as p:
        browser =  p.chromium.launch(headless=True)
        page =  browser.new_page()
        page.goto(url,wait_until="load")


        soup = BeautifulSoup( page.content(), "html.parser")
        print(soup)
        # Scrape product details from visible HTML
        product_name = soup.find("h1", {"class": "pdp-title"}).text.strip()
        product_price = soup.find("span", {"class": "pdp-price"}).text.strip()
        product_image = soup.find("img", {"class": "image-zoom"})["src"]

        browser.close()

        return {
            "name": product_name,
            "price": product_price,
            "image": product_image,
        }
async def fetch_myntra_price2(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.myntra.com/"
        }
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            print(response.text)
            # Find all <script> tags with type="application/ld+json"
            scripts = soup.find_all("script", type="application/ld+json")

            if scripts:
                try:
                    # Extract the JSON data from the second script tag (scripts[1])
                    raw_json = scripts[1].string.strip()

                    # Clean up the JSON string to remove any control characters
                    clean_json = ''.join([char if char.isprintable() else ' ' for char in raw_json])

                    # Now try to load the cleaned JSON
                    data = json.loads(clean_json)

                    # Ensure the data is a valid product object
                    # if data.get("@type") == "Product":  # Filter for Product data
                    product_name = data.get("name")
                    product_price = data.get("offers", {}).get("price")
                    price_currency = data.get("offers", {}).get("priceCurrency")
                    product_image = data.get("image")
                    product_description = data.get("description")

                    # Print or return the product details
                    if product_name == None:
                        return {'error':'Unable to find the product'}
                    return ({
                        "name": product_name,
                        "price": f"{product_price}",
                        "product_image": product_image,
                        "product_description": product_description
                    })
                    # else:
                    #     print("No product data found.")

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                except Exception as e:
                    print(f"Unexpected error: {e}")
            else:
                print("No JSON-LD script found")
                return {"error": f"An error occurred: No JSON-LD script found"}
        else:
            print(f"Failed to fetch page, status code: {response.status_code}")
            return {"error": f"Unable to fetch status code: {response.status_code}"}
    except Exception as e:
        print(f"Error fetching Myntra price: {e}")
        return {"error": f"An error occurred: {str(e)}"}
async def main():

    x=await fetch_myntra_price2('https://www.myntra.com/headphones/realme/realme-buds-wireless-3-neo-with-134mm-driver-32-hrs-playback--dual-connection-headset/29655054/buy')
    print(x)
asyncio.run(main())
