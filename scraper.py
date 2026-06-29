import re
import asyncio
import aiohttp

from dotenv import load_dotenv

load_dotenv()

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xhtml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}


async def scrape(url, platform):
    pid = findId(url)
    if pid is None:
        return None, None, None, None, None, 'Product ID not Found'

    product = await fetch_buyhatke_price(url)

    price = product.get('price')
    product_name = product.get('name')
    img_url = product.get('product_image')
    availability = product.get('availability')
    scrap_error = product.get('error')
    return platform, pid, product_name, price, img_url, availability, scrap_error


async def check_platform(url):
    platform_map = {
        "amazon": "amazon",
        "ajio": "ajio",
        "myntra": "myntra",
        "flipkart": "flipkart",
        "shopsy": "shopsy",
        "meesho":"meesho"
    }
    for keyword, platform in platform_map.items():
        if keyword in url:
            return platform
    return None


def findId(url):
    if 'flipkart' in url:
        m = re.search(r"flipkart\.com(?:\/.*\/.*)?\?pid=([\w-]+)", url)
        return m.group(1) if m else None
    elif 'ajio' in url:
        m = re.search(r"https:\/\/www\.ajio\.com(?:.*\/)?p\/([\w-]+)(?=\W|$)", url)
        return m.group(1) if m else None
    elif 'myntra' in url:
        m = re.search(r"https:\/\/www\.myntra\.com(?:\/.*)?\/(\d+)\/?", url)
        return m.group(1) if m else None
    elif 'shopsy' in url:
        m = re.search(r"pid=([^&]+)", url)
        return m.group(1) if m else None
    elif 'amazon' in url:
        m = re.search(r"/product/([A-Za-z0-9]{10})", url)
        if not m:
            m = re.search(r'/dp/([A-Za-z0-9]{10})', url)
        return m.group(1) if m else None
    elif 'meesho' in url:
        m = re.search(r'/p/(\d+)', url)
        return m.group(1) if m else None
    return None


async def fetch_buyhatke_price(url: str) -> dict:
    """
    Fetches price by loading buyhatke.com/<product_url> and extracting
    productData embedded in SvelteKit's SSR script tag.
    """
    page_url = f"https://buyhatke.com/{url}"
    try:
        async with aiohttp.ClientSession(headers=_HEADERS) as session:
            async with session.get(
                page_url,
                timeout=aiohttp.ClientTimeout(total=20),
                allow_redirects=True,
            ) as resp:
                if resp.status != 200:
                    return {"error": f"BuyHatke HTTP {resp.status}"}
                html = await resp.text(encoding="utf-8", errors="replace")
    except asyncio.TimeoutError:
        return {"error": "BuyHatke request timed out"}
    except Exception as e:
        return {"error": f"BuyHatke fetch error: {e}"}

    return _parse_svelte_data(html)


def _parse_svelte_data(html: str) -> dict:
    """
    BuyHatke is SvelteKit SSR. Product data is embedded in the kit.start()
    call inside a <script> tag as a JS object literal. Extract fields with regex.
    """
    # Locate the productData block
    idx = html.find("productData:{")
    if idx == -1:
        idx = html.find("productData: {")
    if idx == -1:
        return {"error": "productData not found in BuyHatke response"}

    # Extract a generous slice around productData for field matching
    chunk = html[idx: idx + 2000]

    def _str_field(key: str) -> str:
        m = re.search(key + r':"([^"]*)"', chunk)
        return m.group(1) if m else ""

    def _num_field(key: str):
        m = re.search(key + r':(-?\d+(?:\.\d+)?)', chunk)
        return float(m.group(1)) if m else None

    name = _str_field("name")
    image = _str_field("image")
    cur_price = _num_field("cur_price")
    in_stock = _num_field("inStock")

    if cur_price is None:
        return {"error": "cur_price not found in BuyHatke productData"}

    if cur_price == 0:
        return {"availability": "OutofStock", "error": "Product is currently out of stock on BuyHatke"}

    price_str = str(int(cur_price))
    availability = "InStock" if in_stock and in_stock > 0 else "OutofStock"

    return {
        "name": name or None,
        "price": price_str,
        "product_image": image or None,
        "availability": availability,
    }
