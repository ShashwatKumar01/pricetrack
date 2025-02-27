
import os
import re

import requests
import json

from amazon_paapi import AmazonApi, get_asin
from bs4 import BeautifulSoup
# from python_flipkart_scraper import ExtractFlipkart
# from python_amazon_scraper import ExtractAmazon

from dotenv import load_dotenv

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
    # try:
    pid=findId(url)
    if pid==None:
        return None,None,None,None,None,'Product ID not Found'
    if platform == "flipkart":
        product = await fetch_flipkart_price(url)
    # elif platform == "amazon":
    #     product = ExtractAmazon(url)
    elif platform=='amazon':
        product = await fetch_amazon_price(url)
    elif platform=='ajio':
        product = await fetch_ajio_price(url)
    elif platform=='myntra':
        product = await fetch_myntra_price(url)
    elif platform=='shopsy':
        product = await fetch_shopsy_price(url)
    elif platform=='meesho':
        product = await fetch_meesho_price(url)
    else:
        # scrap_error='Unsupported platform'
        raise ValueError("Unsupported platform")


    price = product.get('price')
    product_name = product.get('name')
    img_url=product.get('product_image')
    availability=product.get('availability')
    scrap_error=product.get('error')
    return platform,pid,product_name, price,img_url,availability,scrap_error
    # except Exception as e:
    #     print(e)
    #     return None, None


async def check_platform(url):
    platform_map = {
        "amazon": "amazon",
        "ajio": "ajio",
        "myntra": "myntra",
        "flipkart": "flipkart",
        "shopsy":"shopsy",
        "meesho":"meesho"
    }
    for keyword, platform in platform_map.items():
        if keyword in url:
            return platform
    return None

def findId(url):
    flipkart_pattern = r"flipkart\.com(?:\/.*\/.*)?\?pid=([\w-]+)"
    ajio_pattern = r"https:\/\/www\.ajio\.com(?:.*\/)?p\/([\w-]+)(?=\W|$)"
    myntra_pattern = r"https:\/\/www\.myntra\.com(?:\/.*)?\/(\d+)\/?"
    shopsy_pattern = r"pid=([^&]+)"
    meesho_pattern = r"\/p\/([a-zA-Z0-9]+)"

    # flipkart_match = re.match(flipkart_pattern, url)
    # ajio_match = re.match(ajio_pattern, url)
    # myntra_match = re.match(myntra_pattern, url)
    if 'flipkart' in url:
        flipkart_match = re.search(flipkart_pattern, url)
        if flipkart_match:
            return flipkart_match.group(1)

    elif 'ajio' in url:
        ajio_match = re.search(ajio_pattern, url)
        if ajio_match:
            return ajio_match.group(1)
    elif 'myntra' in url:
        myntra_match = re.search(myntra_pattern, url)
        if myntra_match:
            return myntra_match.group(1)
    elif 'shopsy' in url:
        shopsy_match = re.search(shopsy_pattern, url)
        if shopsy_match:
            return shopsy_match.group(1)
    elif 'meesho' in url:
        meesho_match = re.search(meesho_pattern, url)
        if meesho_match:
            return meesho_match.group(1)
    elif 'amazon' in url:
        product_code_match = re.search(r"/product/([A-Za-z0-9]{10})", url)
        product_code_match2 = re.search(r'/dp/([A-Za-z0-9]{10})', url)
        product_code = product_code_match.group(1) if product_code_match else product_code_match2.group(1)
        return product_code

# async def fetch_flipkart_price2(url):
#     try:
#         product=ExtractFlipkart(url)
#
#         availability='InStock' if (product.is_available()) else 'OutofStock'
#         if 'month' in product.get_price():
#             x=await fetch_flipkart_price2(url)
#             price=x.get('price')
#
#         else:
#             price=product.get_price()
#         return ({
#                         "name": product.get_title(),
#                         "price": price,
#                         "availability": availability,
#                         "product_image": product.get_images()[0]
#                     })
#     except Exception as e:
#         return {"error": f"An error occurred: {str(e)}"}

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
                        data=data[0]
                    # print(data)
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
                    return {"error": f"An error occurred: {str(e)}"}
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    return {"error": f"An Unexpected error occurred: {str(e)}"}
            else:
                print("No JSON-LD script found")
                return {"error": f"An error occurred: No JSON-LD script found"}
        else:
            print(f"Failed to fetch page, status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching flipkart price: {e}")
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
        try:
            if SearchProduct.offers.listings[0].price.amount:
                price_element = str(SearchProduct.offers.listings[0].price.display_amount)
                price = price_element.split(' ')[0].strip().replace("₹", "").replace(",", "")
                # print(SearchProduct.offers)
                availability=str(SearchProduct.offers.listings[0].availability.message)
                availability='InStock' if 'In stock' in availability else 'OutofStock'

        except Exception as err:
            price = None
            availability='OutofStock'
        return {"price": price, "name": amazon_product_name, "product_image": img_url,"availability":availability}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)} url: {product_url}"}



async def fetch_myntra_price(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
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
                    availability=data.get("offers", {}).get('availability')

                    availability='InStock' if 'InStock' in availability else 'OutofStock'


                    # Print or return the product details
                    if product_name == None:
                        return {'error':'Unable to find the product'}
                    return ({
                        "name": product_name,
                        "price": f"{product_price}",
                        "product_image": product_image,
                        "availability": availability,
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
                    availability=data.get("offers", {}).get('availability')
                    availability='InStock' if 'InStock' in availability else 'OutofStock'

                    if product_name == None:
                        return {'error':'Unable to find the product'}
                        # Print or return the product details
                    return ({
                        "name": product_name,
                        "price": f"{product_price}",
                        "product_image": product_image,
                        "availability": availability,
                        "product_description": product_description
                    })
                    # else:
                    #     print("No product data found.")
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    return {"error": f"An error occurred: {str(e)}"}
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    return {"error": f"An error occurred: {str(e)}"}
            else:
                print("No JSON-LD script found")
                return {"error": f"An error occurred: No JSON-LD script found"}
        else:
            print(f"Failed to fetch page, status code: {response.status_code}")
            return {"error": f"An error occurred:status code: {response.status_code} "}
    except Exception as e:
        print(f"Error fetching ajio price: {e}")
        return {"error": f"An error occurred: {str(e)}"}

async def fetch_myntra_price2(url):
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
                    availability=data.get("offers", {}).get('availability')
                    availability='InStock' if 'InStock' in availability else 'OutofStock'

                    # Print or return the product details
                    return ({
                        "name": product_name,
                        "price": f"{product_price}",
                        "product_image": product_image,
                        "availability": availability,
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

async def fetch_shopsy_price(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            scripts = soup.find_all("script", type="application/ld+json")

            if scripts:
                try:
                    raw_json = scripts[0].string.strip()

                    clean_json = ''.join([char if char.isprintable() else ' ' for char in raw_json])

                    data = json.loads(clean_json)
                    data=data[0]
                    product_name = data.get("name")

                    product_price = data.get("offers", {}).get("price")
                    price_currency = data.get("offers", {}).get("priceCurrency")
                    product_image = data.get("image")
                    product_description = data.get("description")
                    availability=data.get("offers", {}).get('availability')
                    availability='InStock' if 'InStock' in availability else 'OutofStock'

                    # Print or return the product details
                    if product_name == None:
                        return {'error':'Unable to find the product'}
                    return ({
                        "name": product_name,
                        "price": f"{product_price}",
                        "product_image": product_image,
                        "availability":availability,
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
        print(f"Error fetching Shopsy price: {e}")
        return {"error": f"An error occurred: {str(e)}"}
async def fetch_meesho_price(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # print(soup)
            # print(response.text)
            # Find all <script> tags with type="application/ld+json"
            scripts = soup.find_all("script", type="application/ld+json")
            # print(scripts)
            if scripts:
                try:
                    raw_json = scripts[1].string.strip()

                    clean_json = ''.join([char if char.isprintable() else ' ' for char in raw_json])

                    data = json.loads(clean_json)
                    product_name = data.get("name")
                    product_price = data.get("offers", {}).get("price")
                    price_currency = data.get("offers", {}).get("priceCurrency")
                    product_image = data.get("image")[0]
                    product_description = data.get("description")
                    availability=data.get("offers", {}).get('availability')

                    availability='InStock' if 'InStock' in availability else 'OutofStock'

                    # Print or return the product details
                    if product_name == None:
                        return {'error':'Unable to find the product'}
                    return ({
                        "name": product_name,
                        "price": f"{product_price}",
                        "product_image": product_image,
                        "availability": availability,
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
        print(f"Error fetching Meesho price: {e}")
        return {"error": f"An error occurred: {str(e)}"}