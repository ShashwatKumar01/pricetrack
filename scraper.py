
import os
import requests
import json

from amazon_paapi import AmazonApi, get_asin
from bs4 import BeautifulSoup
from python_flipkart_scraper import ExtractFlipkart
# from python_amazon_scraper import ExtractAmazon

from dotenv import load_dotenv
# async def scrape(url, platform):
#     # print(url,platform)
#     try:
#         if platform == "flipkart":
#             product = ExtractFlipkart(url)
#         elif platform == "amazon":
#             product = ExtractAmazon(url)
#         else:
#             raise ValueError("Unsupported platform")
#
#         price = product.get_price()
#         product_name = product.get_title()
#         print(price,product_name)
#         return product_name, price
#     except Exception as e:
#         print(e)
#         return None, None
load_dotenv()
KEY = os.getenv("KEY")
SECRET= os.getenv("SECRET")  # User-product mapping
TAG = os.getenv("TAG")
COUNTRY=os.getenv("COUNTRY")

# TAG='pgraph-21'

amazon = AmazonApi(KEY, SECRET, TAG, COUNTRY)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
}


async def scrape(url, platform):
    # print(url,platform)
    try:
        if platform == "flipkart":
            product = await fetch_flipkart_price2(url)
        # elif platform == "amazon":
        #     product = ExtractAmazon(url)
        elif platform=='amazon':
            product = await fetch_amazon_price(url)
        elif platform=='ajio':
            product = await fetch_ajio_price(url)
        elif platform=='myntra':
            product = await fetch_myntra_price(url)
        else:
            raise ValueError("Unsupported platform")

        price = product.get('price')
        product_name = product.get('name')
        # print(price,product_name)
        return product_name, price
    except Exception as e:
        print('gg')
        print(e)
        return None, None


async def check_platform(url):
    platform_map = {
        "amazon": "amazon",
        "ajio": "ajio",
        "myntra": "myntra",
        "flipkart": "flipkart",
    }
    for keyword, platform in platform_map.items():
        if keyword in url:
            return platform
    return None
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

async def fetch_flipkart_price(url):
    try:
        response = requests.get(url,headers=headers)
        # print(response.text)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # Find all <script> tags with type="application/ld+json"
            scripts = soup.find_all("script", type="application/ld+json")

            if scripts:
                try:
                    # Extract the JSON data from the second script tag (scripts[1])
                    raw_json = scripts[0].string.strip()

                    # Clean up the JSON string to remove any control characters
                    clean_json = ''.join([char if char.isprintable() else ' ' for char in raw_json])

                    # Now try to load the cleaned JSON
                    data = json.loads(clean_json)
                    if type(data)==list:
                        print('gg')
                        data=data[0]
                    print(data)
                    # Ensure the data is a valid product object
                    # if data.get("@type") == "Product":  # Filter for Product data
                    product_name = data.get("name")
                    product_price = data.get("offers", {}).get("price")
                    price_currency = data.get("offers", {}).get("priceCurrency")
                    product_image = data.get("image")
                    product_description = data.get("description")

                    # Print or return the product details
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
        else:
            print(f"Failed to fetch page, status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching Myntra price: {e}")
        return {"error": f"An error occurred: {str(e)}"}
async def fetch_amazon_price(product_url):
    # product_url=remove_amazon_affiliate_parameters(product_url)
    try:
        asin = get_asin(product_url)
        # print(asin)
        SearchProduct = amazon.get_items(asin)[0]
        amazon_product_name = SearchProduct.item_info.title.display_value
        # print(amazon_product_name)
        img_url = SearchProduct.images.primary.large.url
        # print(img_url)
        # print(SearchProduct)
        if SearchProduct.offers.listings[0].price.amount:
            # print(str(SearchProduct.offers))
            price_element = str(SearchProduct.offers.listings[0].price.display_amount)
            price = price_element.strip().replace("₹", "").replace(",", "")

        else:
            price = 'Currently Unavailable'
        return {"price": price, "name": amazon_product_name, "image_url": img_url}
    except Exception as e:
        print(f"Error fetching amazon price: {e}")
        return {"error": f"An error occurred: {str(e)}"}



async def fetch_myntra_price(url):
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

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
        else:
            print(f"Failed to fetch page, status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching Myntra price: {e}")
        return {"error": f"An error occurred: {str(e)}"}


async def fetch_ajio_price(url):
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # Find all <script> tags with type="application/ld+json"
            scripts = soup.find_all("script", type="application/ld+json")

            if scripts:
                try:
                    # Extract the JSON data from the second script tag (scripts[1])
                    raw_json = scripts[2].string.strip()
                    # print(raw_json)

                    # Clean up the JSON string to remove any control characters
                    clean_json = ''.join([char if char.isprintable() else ' ' for char in raw_json])

                    # Now try to load the cleaned JSON
                    data = json.loads(clean_json)
                    # print(data)


                    # if data.get("@type") == "ProductGroup":  # Filter for Product data
                    product_name = data.get("name")
                    product_price = data.get("offers", {}).get("price")
                    price_currency = data.get("offers", {}).get("priceCurrency")
                    product_image = data.get("image")
                    product_description = data.get("description")

                        # Print or return the product details
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
        else:
            print(f"Failed to fetch page, status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching ajio price: {e}")
        return {"error": f"An error occurred: {str(e)}"}

