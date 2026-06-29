# Price Tracker Bot

A Telegram bot that tracks product prices across major Indian e-commerce platforms and alerts you whenever the price changes.

<img src="./demos/priceTrackerbot.gif" alt="Bot Demo" width="40%">
<img src="./demos/ss-pricetracker.jpg" alt="Product Tracking" width="40%">

## Supported Platforms

Amazon · Flipkart · Shopsy · Ajio · Myntra · Meesho

## Features

- **Price Tracking** — Send a product link; the bot scrapes and monitors it automatically
- **Price Change Alerts** — Get notified with the old price, new price, and % change whenever the price moves
- **Product Image** — Alerts and product info include the product image when available
- **Price Graph** — View a chart of tracked price history with `/pricegraph_<id>`
- **Lowest / Highest Price** — See all-time low and high since you started tracking
- **Auto Cleanup** — Price history older than 6 months is pruned automatically

## Commands

| Command | Description |
|---|---|
| `/start` | Start the bot |
| `/help` | Show help |
| `/my_trackings` | List all products you are tracking |
| `/product_<id>` | Get current info and image for a tracked product |
| `/pricegraph_<id>` | View a price history graph for a tracked product |
| `/stop_<id>` | Stop tracking a product and remove it |
| `/stats` | Show bot usage stats |

> **Admin only**
> `/scrap` — Trigger an immediate price check across all tracked products

## Environment Variables

Create a `.env` file (see `.envexample`) with these keys:

```env
BOT_TOKEN=          # Telegram bot token from @BotFather
API_ID=             # Telegram API ID from my.telegram.org
API_HASH=           # Telegram API Hash from my.telegram.org
MONGO_URI=          # MongoDB connection string
DATABASE=           # MongoDB database name
COLLECTION=         # Collection for user-product mappings
PRODUCTS=           # Collection for global product data
ADMIN_ID=           # Your Telegram user ID (for /scrap command)
AUTH_CHANNEL=       # @username or -100xxx (force-join gate, optional)
AUTH_INVITE_LINK=   # Invite link shown to non-members (optional)
EARNKARO_API=       # EarnKaro affiliate API token
AMAZON_AFF_TAG=     # Amazon affiliate tag (optional)
```

## Local Setup

```bash
git clone https://github.com/nuhmanpk/PriceTrackerBot.git
cd PriceTrackerBot

python -m venv .venv
# Linux/Mac
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

## Docker

```bash
docker build -t price-tracker-bot .
docker run --env-file .env price-tracker-bot
```

## Deploy on Render

1. Push your code to a GitHub repository
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your GitHub repo
4. Set **Runtime** to `Docker`
5. Add all environment variables from the table above in the **Environment** tab
6. Set **Health Check Path** to `/`
7. Click **Deploy**

> **Note:** Render's free tier has an ephemeral filesystem. The Pyrogram session file (`PriceTrackerBot.session`) is lost on restart, which forces re-authentication. To avoid this, add a **Render Disk** (paid) mounted at `/app` or use a session string stored in an env var.

## Project Structure

```
PriceTrackerBot/
├── main.py          # Bot handlers, commands, graph generation
├── scheduler.py     # Scheduled price checks, user notifications
├── scraper.py       # URL platform detection, product ID extraction, BuyHatke scraping
├── helpers.py       # MongoDB helpers (add/fetch/delete products, price history)
├── requirements.txt
└── Dockerfile
```

## Support

Open an [issue](https://github.com/nuhmanpk/PriceTrackerBot/issues) for bugs or feature requests.
