import time

from dotenv import load_dotenv

load_dotenv()

from datetime import datetime
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from scraper import scrape, check_platform
from dotenv import load_dotenv
load_dotenv()

# MongoDB configuration
dbclient = AsyncIOMotorClient(os.getenv("MONGO_URI"))
database = dbclient[os.getenv("DATABASE")]
collection = database[os.getenv("COLLECTION")]  # User-product mapping
PRODUCTS = database[os.getenv("PRODUCTS")]  # Products collection


async def check_prices(app):
    job=await app.send_message(chat_id='5886397642', text=f'CronJob started')

    start_time=time.time()
    # Process products concurrently
    tasks = []
    async for product in PRODUCTS.find():
        tasks.append(process_product(product, app))

    await asyncio.gather(*tasks)  # Run all tasks concurrently
    print("Price checking completed.")
    end_time = time.time()
    timetaken=end_time-start_time
    await job.edit(f'Price checking completed in {timetaken} Seconds')

semaphore = asyncio.Semaphore(60)
async def process_product(product, app):
    async with semaphore:
        url = product["url"]
        platform = await check_platform(url)
        # _, current_price = await scrape(product["url"])
        await asyncio.sleep(1)
        _,_,_,current_price,_,_= await scrape(url, platform)
        # print(current_price)
        if current_price is not None and current_price != product["price"]:
            # Update the product information in the database
            current_time = datetime.utcnow()
            await PRODUCTS.update_one(
                {"_id": product["_id"]},
                {
                    "$set": {
                        "price": current_price,
                        "previous_price": product["price"],
                        "lower": min(current_price, product["lower"]),
                        "upper": max(current_price, product["upper"]),
                    },
                    "$push": {"price_history": {"date": current_time, "price": current_price}}
                },
            )

            # Notify users about the price change
            await notify_users(product, app)


async def notify_users(product, app):
    cursor = collection.find({"product_id": product["_id"]})
    users = await cursor.to_list(length=None)
    # affurl= await ekconvert(product['url'])
    for user in users:
        current_price = float(product["price"])
        previous_price = float(product["previous_price"])
        platform= product["platform"]
        percentage_change = ((current_price - previous_price) / previous_price) * 100
        text = (
            f"<b>⚠️ Alert! The price of [{product['product_name']}]({product['aff_url']}) has changed.</b>\n\n"
            f"   - Previous Price: ₹{previous_price:.2f}\n"
            f"   - Current Price: ₹{current_price:.2f}\n"
            f"   - Percentage Change: {percentage_change:.2f}%\n"
            f"   - Tracked By <b>@The_PriceTracker_Bot</b>\n\n"
            f"   - <b>[Click here to open in {platform}]({product['aff_url']})</b>\n\n"
            f"     {product['aff_url']}"
        )

        await app.send_message(
            chat_id=user.get("user_id"), text=text, disable_web_page_preview=False)


# Compare prices to identify changed products
async def compare_prices():
    print("Comparing prices...")
    product_with_changes = []
    async for product in PRODUCTS.find():
        if product["price"] != product["previous_price"]:
            product_with_changes.append(product["_id"])
    return product_with_changes

#
#
# dbclient = MongoClient(os.getenv("MONGO_URI"))
# database = dbclient[os.getenv("DATABASE")]
# collection = database[os.getenv("COLLECTION")]
# PRODUCTS = database[os.getenv("PRODUCTS")]
#
#
# async def check_prices(app):
#     print("Checking Price for Products...")
#     for product in PRODUCTS.find():
#         url=product["url"]
#         platform=await check_platform(url)
#         _, current_price = await scrape(url, platform)
#         time.sleep(1)
#         if current_price is not None:
#             if current_price != product["price"]:
#                 current_time = datetime.utcnow()
#                 PRODUCTS.update_one(
#                     {"_id": product["_id"]},
#                     {
#                         "$set": {
#                             "price": current_price,
#                             "previous_price": product["price"],
#                             "lower": current_price
#                             if current_price < product["lower"]
#                             else product["lower"],
#                             "upper": current_price
#                             if current_price > product["upper"]
#                             else product["upper"],
#
#                         },"$push": {"price_history": {"date": current_time, "price": current_price}}
#                     },
#                 )
#     print("Completed")
#     changed_products = await compare_prices()
#     for changed_product in changed_products:
#         cursor = collection.find({"product_id": changed_product})
#         users = list(cursor)
#         for user in users:
#             product = PRODUCTS.find_one({"_id": user.get("product_id")})
#             percentage_change = (
#                 (product["price"] - product["previous_price"])
#                 / product["previous_price"]
#             ) * 100
#             text = (
#                 f"🎉 Good news! The price of {product['product_name']} has changed.\n"
#                 f"   - Previous Price: ₹{product['previous_price']:.2f}\n"
#                 f"   - Current Price: ₹{product['price']:.2f}\n"
#                 f"   - Percentage Change: {percentage_change:.2f}%\n"
#                 f"   - [Check it out here]({product['url']})"
#             )
#             await app.send_message(
#                 chat_id=user.get("user_id"), text=text, disable_web_page_preview=True
#             )
#
#
# async def compare_prices():
#     print("Comparing Prices...")
#     product_with_changes = []
#     for product in PRODUCTS.find():
#         current_price = product.get("price")
#         previous_price = product.get("previous_price")
#         if current_price != previous_price:
#             product_with_changes.append(product.get("_id"))
#
#     return product_with_changes
