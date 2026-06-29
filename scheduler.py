import time

from dotenv import load_dotenv
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
from datetime import datetime, timezone
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


ADMIN_ID = int(os.getenv("ADMIN_ID", "5886397642"))

async def check_prices(app):
    job=await app.send_message(chat_id=ADMIN_ID, text=f'Price checking Started.  ')

    start_time=time.time()
    # Process products concurrently
    tasks = []
    print("Price checking Started.")

    async for product in PRODUCTS.find():
        tasks.append(process_product(product, app))
        # print('hi')


    await asyncio.gather(*tasks)  # Run all tasks concurrently
    print("Price checking completed.")
    end_time = time.time()
    timetaken=end_time-start_time
    await job.edit(f'Price checking completed in {timetaken} Seconds')

semaphore = asyncio.Semaphore(10)
async def process_product(product, app):
    async with semaphore:
        url = product["url"]
        platform = await check_platform(url)
        _, _, _, current_price, _, current_availability, _ = await scrape(url, platform)
        if current_price is None or current_availability == 'OutofStock':
            return
        try:
            cp = float(current_price)
            pp = float(product["price"])
        except (ValueError, TypeError):
            return
        if cp == pp:
            return
        current_time = datetime.now(timezone.utc)
        lower = min(cp, float(product.get("lower", cp)))
        upper = max(cp, float(product.get("upper", cp)))
        await PRODUCTS.update_one(
            {"_id": product["_id"]},
            {
                "$set": {
                    "price": current_price,
                    "previous_price": product["price"],
                    "lower": str(int(lower)),
                    "upper": str(int(upper)),
                },
                "$push": {"price_history": {"date": current_time, "price": current_price}}
            },
        )
        updated_product = await PRODUCTS.find_one({"_id": product["_id"]})
        await notify_users(updated_product, app)


async def notify_users(product, app):
    cursor = collection.find({"product_id": product["_id"]})
    users = await cursor.to_list(length=None)
    img_url = product.get("img_url")
    for user in users:
        current_price = float(product["price"])
        previous_price = float(product["previous_price"])
        platform = product["platform"]
        percentage_change = ((current_price - previous_price) / previous_price) * 100
        text = (
            f"<b>📉📈 Alert! The price of [{product['product_name']}]({product['aff_url']}) has changed.</b>\n\n"
            f"   - Previous Price: ₹{previous_price:.2f}\n"
            f"   - Current Price: ₹{current_price:.2f}\n"
            f"   - Percentage Change: {percentage_change:.2f}%\n"
            f"   - Buy LINK : {product['aff_url']}\n\n"
            f"   - <b>[Click here to open in {platform}]({product['aff_url']})</b>\n\n"
            f"ℹ️ /product_{user['_id']} — more info\n"
            f"📊 /pricegraph_{user['_id']} — price graph\n"
            f"🔴 /stop_{user['_id']} — stop tracking"
        )
        Join = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🎟️ Buy Now", url=f"{product['aff_url']}")],
             [InlineKeyboardButton("🛍️ Today's Deals", url="https://t.me/+HeHY-qoy3vsxYWU1")],
             [InlineKeyboardButton("🕵️ Report ISSUES", url="https://t.me/imovies_contact_bot")]])

        sent = False
        if img_url:
            try:
                await app.send_photo(
                    chat_id=user.get("user_id"), photo=img_url, caption=text, reply_markup=Join)
                sent = True
            except Exception:
                pass
        if not sent:
            await app.send_message(
                chat_id=user.get("user_id"), text=text, reply_markup=Join, disable_web_page_preview=False)


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
#                 current_time = datetime.now(timezone.utc)
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
