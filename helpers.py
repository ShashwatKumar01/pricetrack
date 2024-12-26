import json
import re
import urllib

import requests
from pymongo import MongoClient
import os
from bson import ObjectId
from unshortenit import UnshortenIt

dbclient = MongoClient(os.getenv("MONGO_URI"))
database = dbclient[os.getenv("DATABASE")]
collection = database[os.getenv("COLLECTION")]
PRODUCTS = database[os.getenv("PRODUCTS")]
apitoken=os.getenv('EARNKARO_API')

async def fetch_all_products(user_id):
    try:
        cursor = collection.find({"user_id": user_id})
        products = list(cursor)
        # print(products)
        global_products = []
        for product in products:
            global_product = PRODUCTS.find_one({"_id": product.get("product_id")})
            global_product["product_id"] = product.get("_id")
            global_products.append(global_product)

        return global_products

    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        return []


async def fetch_one_product(_id):
    try:
        product = collection.find_one({"_id": ObjectId(_id)})
        global_product = PRODUCTS.find_one({"_id": product.get("product_id")})
        return global_product

    except Exception as e:
        print(f"Error fetching product: {str(e)}")
        return None

async def fetchstats():
    x=collection.distinct('user_id')
    usernos=len(x)
    y=PRODUCTS.find()
    pnos=len(list(y))
    return usernos,pnos


async def add_new_product(user_id, product_name, product_url, initial_price):
    try:
        existing_global_product = PRODUCTS.find_one({"product_name": product_name})
        if not existing_global_product:
            aff_url = await ekconvert(product_url)

            global_new_product = {
                "product_name": product_name,
                "url": product_url,
                "price": initial_price,
                "previous_price": initial_price,
                "upper": initial_price,
                "lower": initial_price,
                "aff_url": aff_url
            }
            insert_result = PRODUCTS.insert_one(global_new_product)
            existing_global_product = {"_id": insert_result.inserted_id}

        existing_product = collection.find_one(
            {"user_id": user_id, "product_id": existing_global_product["_id"]}
        )

        if existing_product:
            print("Product already exists.")
            return existing_product["_id"]

        new_local_product = {
            "user_id": user_id,
            "product_id": existing_global_product["_id"],
        }

        result = collection.insert_one(new_local_product)

        return result.inserted_id

    except Exception as e:
        print(f"Error adding product: {str(e)}")
        return None



async def update_product_price(id, new_price):
    try:
        global_product = PRODUCTS.find_one(
            {"_id": id},
        )

        if global_product:
            upper_price = global_product.get("upper", new_price)
            lower_price = global_product.get("lower", new_price)

            if new_price > upper_price:
                upper_price = new_price
            elif new_price < lower_price:
                lower_price = new_price

            PRODUCTS.update_one(
                {"_id": id},
                {
                    "$set": {
                        "price": new_price,
                        "upper": upper_price,
                        "lower": lower_price,
                    }
                },
            )
            print("Global product prices updated successfully.")
    except Exception as e:
        print(f"Error updating product price: {str(e)}")


async def delete_one(_id, user_id):
    try:
        product = collection.find_one({"_id": ObjectId(_id)})

        if product and product.get("user_id") == int(user_id):
            collection.delete_one({"_id": ObjectId(_id)})
            return True
        else:
            return None

    except Exception as e:
        print(f"Error deleting product: {str(e)}")
        return None

def extract_link_from_text(text):
    # Regular expression pattern to match a URL
    url_pattern = r'https?://\S+'

    # Find all URLs in the text
    urls = re.findall(url_pattern, text)
    if len(urls)>1:
        return None

    return urls[0] if urls else None
# async def unshorten_url(url):
#     try:
#         async with async_playwright() as p:
#             browser = await p.chromium.launch(headless=True)
#             page = await browser.new_page()
#             await page.goto(url)
#             final_url = page.url
#             await browser.close()
#             return final_url
#     except Exception as e:
#         print(f"Error: {e}")
#         return None
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

async def ekconvert(text):
    url = "https://ekaro-api.affiliaters.in/api/converter/public"

    # inputtext = input('enter deal: ')
    payload = json.dumps({
        "deal": f"{text}",
        "convert_option": "convert_only"
    })
    headers = {
        'Authorization': f'Bearer {apitoken}',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    # print(response.text)
    response_dict = json.loads(response.text)

    # Extract the "data" part from the dictionary
    data_value = response_dict.get('data')

    return(data_value)

