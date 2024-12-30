import asyncio
import logging
import threading
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import Message
# from dotenv import load_dotenv
import os
import schedule
import time
import pytz
from quart import Quart

from scraper import scrape,check_platform
from scheduler import check_prices
from helpers import fetch_all_products, add_new_product, fetch_one_product, delete_one ,extract_link_from_text,unshorten_url,fetchstats
# from regex_patterns import flipkart_url_patterns, amazon_url_patterns, all_url_patterns

# load_dotenv()

timezone = pytz.timezone("Asia/Kolkata")
bot_token = os.getenv("BOT_TOKEN")
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot = Quart(__name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@bot.route('/')
async def hello():
    return 'Hello, world!'
app = Client("PriceTrackerBot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)


@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    text = (
        f"Hello {message.chat.username}! 🌟\n\n"
        "I'm PriceTrackerBot, your personal assistant for tracking product prices. 💸\n\n"
        "To get started, use the /my_trackings command to start tracking a product. "
        "Simply send the url:\n"
        "For example:\n"
        "I'll keep you updated on any price changes for the products you're tracking. "
        "Feel free to ask for help with the /help command at any time. Happy tracking! 🚀"
    )

    await message.reply_text(text, quote=True)


@app.on_message(filters.command("help") & filters.private)
async def help(_, message: Message):
    text = (
        "🤖 **Price Tracker Bot Help**\n\n"
        "Here are the available commands:\n"
        "1. `/my_trackings`: View all the products you are currently tracking.\n"
        "2. `/stop < product_id >`: Stop tracking a specific product. Replace `<product_id>` with the product ID you want to stop tracking.\n"
        "3. `/product < product_id >`: Get detailed information about a specific product. Replace `<product_id>` with the product ID you want information about.\n"
        "\n\n**How It Works:**\n\n"
        "1. Send the product link from flipkart,ajio,amazon,myntra\n"
        "2. The bot will automatically scrape and track the product.\n"
        "3. If there is a price change, the bot will notify you with the updated information.\n"
        "Feel free to use the commands and start tracking your favorite products!\n"
    )
    await message.reply_text(text, quote=True)


@app.on_message(filters.command("my_trackings") & filters.private)
async def track(_, message):
    try:
        chat_id = message.chat.id
        text = await message.reply_text("Fetching Your Products...")
        products = await fetch_all_products(chat_id)
        if products:
            products_message = "Your Tracked Products:\n\n"

            for i, product in enumerate(products, start=1):
                _id = product.get("product_id")
                product_name = product.get("product_name")
                product_url = product.get("aff_url")
                product_price = product.get("price")

                products_message += (
                    f"🏷️ **Product {i}**: <b>[{product_name}]({product_url})</b>\n\n"
                )
                products_message += f"💰 **Current Price**: {product_price}\n"
                products_message += f"🔗 **Product LINK** : {product_url}\n"
                products_message += f"🕵️ Use `/product {_id}` for more details\n"
                products_message += f"❌ Use `/stop {_id}` to Stop tracking\n\n\n"

            await text.edit(products_message, disable_web_page_preview=True)
        else:
            await text.edit("No products added yet")
    except Exception as e:
        print(e)


# @app.on_message(filters.regex("|".join(all_url_patterns)))




@app.on_message(filters.command("product") & filters.private)
async def track_product(_, message):
    try:
        __, id = message.text.split()
        status = await message.reply_text("Getting Product Info....")
        if id:
            product = await fetch_one_product(id)
            if product:
                product_name = product.get("product_name")
                product_url = product.get("aff_url")
                product_price = product.get("price")
                maximum_price = product.get("upper")
                minimum_price = product.get("lower")

                products_message = (
                    f"🛍 **Product:** <b>[{product_name}]({product_url})</b>\n\n"
                    f"💲 **Current Price:** {product_price}\n"
                    f"📉 **Lowest Price:** {minimum_price}\n"
                    f"📈 **Highest Price:** {maximum_price}\n\n"
                    f"🔗 **Product Link:** {product_url}"
                    f"\n\n\nTo Stop Tracking, use `/stop {id}`"
                )

                await status.edit(products_message, disable_web_page_preview=False)
            else:
                await status.edit("Product Not Found")
        else:
            await status.edit("Failed to fetch the product")
    except Exception as e:
        print(e)


@app.on_message(filters.command("stop") & filters.private)
async def delete_product(_, message):
    try:
        __, id = message.text.split()
        status = await message.reply_text("Deleting Product....")
        chat_id = message.chat.id
        if id:
            is_deleted = await delete_one(id, chat_id)
            if is_deleted:
                await status.edit("Product Deleted from Your Tracking List")
            else:
                await status.edit("Failed to Delete the product")
        else:
            await status.edit("Failed to Delete the product")
    except Exception as e:
        print(e)
@app.on_message(filters.command("stats") & filters.private)
async def status(_, message):
    status = await message.reply_text("Getting stats....")
    usercount,pnos=await fetchstats()

    stats_message = (
        f"🛍 **Bot is Running**\n\n"
        f"🛍️ **Total Products Monitoring:**   {pnos}\n"
        f"👨‍👩‍👧‍👦 **Total Users currently Using:** {usercount}\n"
    )
    await status.edit(stats_message)

@app.on_message(filters.private)
async def track_url(_, message):
    try:
        text = message.caption if message.caption else message.text
        if 'Livegram'in text or 'You cannot forward someone' in text:
            await message.delete()
            return None
        a = await message.reply_text("Please Wait....!!")
        url= extract_link_from_text(text).strip()
        if ('dl.flipkart' in url):
            url=unshorten_url(url)
        if(('amazon' not in url) and ('ajio' not in url) and ('myntra' not in url) and ('flipkart'not in url)):
            url= unshorten_url(url)
        platform=await check_platform(url)
        if platform==None:
            await a.edit('Unsupported platform, Only amazon,flipkart,myntra ,ajio')
            return
        try:
            platform,pid,product_name, price,img_url,scrap_error= await scrape(url, platform)
            print(platform,pid,product_name, price,img_url,scrap_error)
            if product_name and price:
                status = await message.reply_text("Adding Your Product...")
                id = await add_new_product(
                    message.chat.id, product_name, url, price,img_url,pid,platform
                )
                await status.edit(
                    f'Tracking your product "{product_name}"!\n'
                    f'Current Price: {price}\n\n'
                    f"You can use\n <b>`/product {id}`</b> to get more information about it."
                )
                await a.delete()
            if scrap_error:
                await app.send_message(chat_id='5886397642', text=f'New Error from a user\n\n{scrap_error},\n\n{url}',disable_web_page_preview=True)
                await app.send_message(chat_id=message.chat.id,text="Failed to scrape your product !!!")
                await a.delete()


        except Exception as e:
            await app.send_message(chat_id='5886397642',text=e)
    except Exception as e:
        await app.send_message(chat_id='5886397642', text=e)

# schedule.every().day.at("00:00").do(lambda: asyncio.create_task(check_prices(app))).tag(
#     "daily_job"
# )
# schedule.every(1).hour.do(lambda: asyncio.create_task(check_prices(app))).tag("hourly_job")
# schedule.every(1).minute.do(lambda: asyncio.run(check_prices(app))).tag("minute_job")

# def run_schedule():
#     while True:
#         schedule.run_pending()
#         time.sleep(5)
# def main():
#     schedule_thread = threading.Thread(target=run_schedule)
#     schedule_thread.start()
#
#     app.run(print("Bot Running"))
# Run schedule in a separate thread

def run_schedule(loop):
    # Set the event loop for this thread
    asyncio.set_event_loop(loop)

    while True:
        schedule.run_pending()
        time.sleep(1)
    # Main async function

async def main():
    # Start the schedule runner in a separate thread


    # Bind the application to a specific port
    schedule_thread = threading.Thread(target=run_schedule,args=(loop,))
    schedule_thread.daemon = True  # Ensure the thread stops when the program exits
    schedule_thread.start()

    schedule.every(30).minutes.do(lambda: asyncio.ensure_future(check_prices(app))).tag("minute_job")

    # Run the app (Pyrogram client)
    await app.start()
    print("Bot started...")

    # Keep the bot running
    # await app.idle()

if __name__ == "__main__":
    # Use asyncio.run to start the main async function and manage the event loop
    loop = asyncio.get_event_loop()
    loop.create_task(bot.run_task(host='0.0.0.0', port=8000))
    loop.create_task(main())
    loop.run_forever()