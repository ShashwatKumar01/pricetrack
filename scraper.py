import re
import json
import asyncio
import aiohttp
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

PAAPI_KEY = os.getenv("PAAPI_KEY")
PAAPI_SECRET = os.getenv("PAAPI_SECRET")
PAAPI_TAG = os.getenv("PAAPI_TAG")
BUYHATKE_PROXY = os.getenv("BUYHATKE_PROXY")  # e.g. http://user:pass@host:port

_BUYHATKE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xhtml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.google.com/",
}

_DIRECT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
}


async def scrape(url, platform):
    pid = findId(url)
    if pid is None:
        return None, None, None, None, None, None, 'Product ID not Found'

    if platform == 'amazon':
        product = await fetch_amazon_paapi(pid)
    else:
        product = await fetch_buyhatke_price(url)
        if product.get('error'):
            product = await fetch_direct(url, platform)

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
        "meesho": "meesho",
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


async def fetch_amazon_paapi(asin: str) -> dict:
    """Fetches Amazon product data via Product Advertising API v5."""
    if not (PAAPI_KEY and PAAPI_SECRET and PAAPI_TAG):
        return {"error": "PAAPI credentials not configured"}

    def _fetch():
        from amazon.paapi import AmazonApi
        api = AmazonApi(PAAPI_KEY, PAAPI_SECRET, PAAPI_TAG, 'IN')
        products = api.get_products(asin)
        if not products:
            return {"error": "PAAPI: product not found"}
        p = products[0]
        raw_price = getattr(p, 'product_price', None) or getattr(p, 'product_original_price', None)
        if raw_price:
            numeric = re.sub(r'[^\d.]', '', str(raw_price))
            price = str(int(float(numeric))) if numeric else None
        else:
            price = None
        avail = str(getattr(p, 'product_availability', '') or '')
        availability = 'OutofStock' if 'unavailable' in avail.lower() else 'InStock'
        return {
            'name': getattr(p, 'product_title', None),
            'price': price,
            'product_image': getattr(p, 'product_photo', None),
            'availability': availability,
        }

    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch)
    except Exception as e:
        return {"error": f"PAAPI error: {e}"}


async def fetch_buyhatke_price(url: str) -> dict:
    page_url = f"https://buyhatke.com/{url}"
    try:
        async with aiohttp.ClientSession(headers=_BUYHATKE_HEADERS) as session:
            async with session.get(
                page_url,
                proxy=BUYHATKE_PROXY,
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
    idx = html.find("productData:{")
    if idx == -1:
        idx = html.find("productData: {")
    if idx == -1:
        return {"error": "productData not found in BuyHatke response"}

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
        return {"availability": "OutofStock", "error": "Product is out of stock"}

    availability = "InStock" if in_stock and in_stock > 0 else "OutofStock"
    return {
        "name": name or None,
        "price": str(int(cur_price)),
        "product_image": image or None,
        "availability": availability,
    }


async def fetch_direct(url: str, platform: str) -> dict:
    """Dispatches to platform-specific direct scraper."""
    pid = findId(url)

    if platform == 'myntra':
        return await fetch_myntra_direct(url, pid)

    if platform == 'ajio':
        return await fetch_ajio_direct(url)

    # Flipkart, Shopsy, Meesho — parse HTML with JSON-LD
    try:
        async with aiohttp.ClientSession(headers=_DIRECT_HEADERS) as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=25),
                allow_redirects=True,
            ) as resp:
                if resp.status != 200:
                    return {"error": f"{platform} direct HTTP {resp.status}"}
                html = await resp.text(encoding="utf-8", errors="replace")
    except asyncio.TimeoutError:
        return {"error": f"{platform} direct request timed out"}
    except Exception as e:
        return {"error": f"{platform} direct fetch error: {e}"}

    result = _parse_jsonld(html)
    if result:
        return result
    return _parse_platform_fallback(html, platform)


async def fetch_myntra_direct(url: str, pid: str) -> dict:
    """Tries Myntra gateway API, falls back to HTML page parsing."""
    api_url = f"https://www.myntra.com/gateway/v2/product/{pid}"
    headers = {
        **_DIRECT_HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.myntra.com/",
        "Origin": "https://www.myntra.com",
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    body = await resp.text()
                    if body.strip():
                        data = json.loads(body)
                        result = _parse_myntra_api(data)
                        if result.get('price'):
                            return result
    except Exception:
        pass

    # Gateway blocked or empty — fetch product page HTML
    return await _fetch_page_and_parse(url, 'myntra')


def _parse_myntra_api(data: dict) -> dict:
    style = data.get("style", {})
    price_data = style.get("price", {})
    price = price_data.get("discounted") or price_data.get("mrp")
    name = style.get("name")
    albums = style.get("media", {}).get("albums", [])
    images = albums[0].get("images", []) if albums else []
    image = images[0].get("src") if images else None
    sizes = style.get("sizes", [])
    in_stock = any(s.get("sizeType", "").upper() != "OUTOFSTOCK" for s in sizes) if sizes else True
    if not price:
        return {"error": "Myntra: price not found"}
    return {
        "name": name,
        "price": str(int(price)),
        "product_image": image,
        "availability": "InStock" if in_stock else "OutofStock",
    }


async def fetch_ajio_direct(url: str) -> dict:
    """Ajio API blocked by Akamai — scrape HTML and parse GTM dataLayer / JSON-LD / OG."""
    return await _fetch_page_and_parse(url, 'ajio')


async def _fetch_page_and_parse(url: str, platform: str) -> dict:
    """Fetches a product page and tries multiple extraction strategies."""
    headers = {**_DIRECT_HEADERS, "Referer": "https://www.google.com/"}
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=25), allow_redirects=True) as resp:
                if resp.status != 200:
                    return {"error": f"{platform} page HTTP {resp.status}"}
                html = await resp.text(encoding="utf-8", errors="replace")
    except asyncio.TimeoutError:
        return {"error": f"{platform} page timed out"}
    except Exception as e:
        return {"error": f"{platform} page fetch error: {e}"}

    # 1. JSON-LD
    result = _parse_jsonld(html)
    if result and result.get('price'):
        return result

    # 2. GTM dataLayer (both Myntra and Ajio push product data here)
    result = _parse_datalayer(html)
    if result and result.get('price'):
        return result

    # 3. OG meta tags (name + image only; price rarely present)
    return _parse_og_meta(html, platform)


def _parse_datalayer(html: str) -> dict:
    """Extracts product info from window.dataLayer GTM push."""
    m = re.search(r'window\.dataLayer\s*=\s*(\[.*?\])\s*;', html, re.DOTALL)
    if not m:
        m = re.search(r'dataLayer\.push\s*\((\{.*?\})\)', html, re.DOTALL)
        if m:
            raw = '[' + m.group(1) + ']'
        else:
            return {}
    else:
        raw = m.group(1)
    try:
        layers = json.loads(raw)
        for layer in layers if isinstance(layers, list) else [layers]:
            if not isinstance(layer, dict):
                continue
            name = layer.get('productName') or layer.get('name') or layer.get('product_name')
            price = layer.get('productPrice') or layer.get('price') or layer.get('product_price')
            image = layer.get('productImage') or layer.get('image')
            if name and price:
                p = re.sub(r'[^\d.]', '', str(price))
                return {
                    'name': name,
                    'price': str(int(float(p))) if p else None,
                    'product_image': image,
                    'availability': 'InStock',
                }
    except Exception:
        pass
    return {}


def _parse_og_meta(html: str, platform: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')
    name = None
    image = None
    meta = lambda prop: (soup.find('meta', property=prop) or {}).get('content')  # noqa: E731
    name = meta('og:title')
    image = meta('og:image')
    price_val = meta('product:price:amount') or meta('og:price:amount')
    if price_val:
        return {
            'name': name,
            'price': str(int(float(price_val))),
            'product_image': image,
            'availability': 'InStock',
        }
    return {"error": f"{platform}: could not extract price from page"}


def _parse_jsonld(html: str) -> dict | None:
    """Extracts product data from JSON-LD structured data (works on most platforms)."""
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '')
            if isinstance(data, list):
                data = next((d for d in data if isinstance(d, dict) and d.get('@type') == 'Product'), None)
            if not data or data.get('@type') != 'Product':
                continue
            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            price = offers.get('price')
            if not price:
                continue
            name = data.get('name')
            images = data.get('image', [])
            if isinstance(images, list):
                image = images[0] if images else None
            elif isinstance(images, str):
                image = images
            else:
                image = None
            avail = str(offers.get('availability', ''))
            availability = 'InStock' if 'InStock' in avail else 'OutofStock'
            return {
                'name': name,
                'price': str(int(float(price))),
                'product_image': image,
                'availability': availability,
            }
        except Exception:
            continue
    return None


def _parse_platform_fallback(html: str, platform: str) -> dict:
    """Last-resort regex extraction when JSON-LD is missing."""
    if platform == 'flipkart':
        m = re.search(r'"finalPrice"\s*:\s*\{"value"\s*:\s*(\d+)', html)
        if not m:
            m = re.search(r'"price"\s*:\s*(\d{3,6})', html)
        name_m = re.search(r'"title"\s*:\s*"([^"]{10,150})"', html)
        img_m = re.search(r'"imageURL"\s*:\s*"([^"]+)"', html)
        if m:
            return {
                'name': name_m.group(1) if name_m else None,
                'price': m.group(1),
                'product_image': img_m.group(1) if img_m else None,
                'availability': 'InStock',
            }

    if platform in ('myntra', 'ajio', 'meesho', 'shopsy'):
        m = re.search(r'"price"\s*:\s*(\d{3,6})', html)
        name_m = re.search(r'"name"\s*:\s*"([^"]{10,150})"', html)
        img_m = re.search(r'"image"\s*:\s*"(https?://[^"]+)"', html)
        if m:
            return {
                'name': name_m.group(1) if name_m else None,
                'price': m.group(1),
                'product_image': img_m.group(1) if img_m else None,
                'availability': 'InStock',
            }

    return {"error": f"Could not parse {platform} page directly"}
