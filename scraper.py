

import re
import requests
from bs4 import BeautifulSoup


# ── Shared headers to mimic a real browser ────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _clean_price(raw: str) -> float | None:
    """
    Remove currency symbols, commas, spaces and return float.
    e.g. 'Rs. 1,89,000' → 189000.0
         '$ 299.99'      → 299.99
    """
    if not raw:
        return None
    # Keep only digits and decimal point
    cleaned = re.sub(r"[^\d.]", "", raw.strip())
    # Remove leading/trailing dots
    cleaned = cleaned.strip(".")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def scrape_daraz(url: str) -> dict:
    """Scrape product name and price from Daraz (daraz.pk)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Price — Daraz uses these selectors (inspect page if they break)
        price = None
        for selector in [
            "span.pdp-price.pdp-price_type_normal",
            "span.pdp-price",
            "[class*='pdp-price']",
            "span[class*='price']",
        ]:
            tag = soup.select_one(selector)
            if tag:
                price = _clean_price(tag.get_text())
                if price:
                    break

        # Product name
        name = None
        name_tag = soup.select_one("h1.pdp-mod-product-badge-title") or \
                   soup.select_one("span[class*='title']") or \
                   soup.find("h1")
        if name_tag:
            name = name_tag.get_text(strip=True)

        return {"price": price, "name": name, "error": None if price else "Price element not found on Daraz page."}

    except requests.exceptions.ConnectionError:
        return {"price": None, "name": None, "error": "Could not connect. Check your internet connection."}
    except requests.exceptions.Timeout:
        return {"price": None, "name": None, "error": "Request timed out. Try again."}
    except Exception as e:
        return {"price": None, "name": None, "error": str(e)}


def scrape_amazon(url: str) -> dict:
    """Scrape product name and price from Amazon."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Amazon price selectors
        price = None
        for selector in [
            "span.a-price-whole",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "span[class*='a-price'] span[class*='a-offscreen']",
            ".a-price .a-offscreen",
        ]:
            tag = soup.select_one(selector)
            if tag:
                price = _clean_price(tag.get_text())
                if price:
                    break

        # Product name
        name = None
        name_tag = soup.select_one("#productTitle")
        if name_tag:
            name = name_tag.get_text(strip=True)

        return {"price": price, "name": name, "error": None if price else "Price not found. Amazon may be blocking scraping — try adding the price manually."}

    except requests.exceptions.ConnectionError:
        return {"price": None, "name": None, "error": "Could not connect. Check your internet connection."}
    except requests.exceptions.Timeout:
        return {"price": None, "name": None, "error": "Request timed out. Try again."}
    except Exception as e:
        return {"price": None, "name": None, "error": str(e)}


def scrape_flipkart(url: str) -> dict:
    """Scrape product name and price from Flipkart."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        price = None
        for selector in [
            "div._30jeq3._16Jk6d",
            "div._30jeq3",
            "[class*='_30jeq3']",
        ]:
            tag = soup.select_one(selector)
            if tag:
                price = _clean_price(tag.get_text())
                if price:
                    break

        name = None
        name_tag = soup.select_one("span.B_NuCI") or soup.find("h1")
        if name_tag:
            name = name_tag.get_text(strip=True)

        return {"price": price, "name": name, "error": None if price else "Price element not found on Flipkart page."}

    except Exception as e:
        return {"price": None, "name": None, "error": str(e)}


def scrape_generic(url: str) -> dict:
    """
    Generic fallback scraper.
    Tries common price-related patterns used across many e-commerce sites.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        price = None
        # Try common class/id patterns
        for selector in [
            "[class*='price']",
            "[id*='price']",
            "[class*='Price']",
            "[itemprop='price']",
            "meta[itemprop='price']",
        ]:
            for tag in soup.select(selector)[:5]:  # check first 5 matches
                # meta tags store price in content attribute
                val = tag.get("content") or tag.get_text()
                price = _clean_price(val)
                if price and price > 0:
                    break
            if price:
                break

        name = None
        name_tag = soup.find("h1")
        if name_tag:
            name = name_tag.get_text(strip=True)

        return {"price": price, "name": name, "error": None if price else "Could not detect price automatically. Please enter it manually."}

    except Exception as e:
        return {"price": None, "name": None, "error": str(e)}


# ── Main public function ───────────────────────────────────────
def scrape_product(url: str) -> dict:
    """
    Detect platform from URL and scrape price + name.

    Returns:
        {
            "price": float or None,
            "name":  str or None,
            "error": str or None   (None means success)
        }

    Usage in app.py:
        from scraper import scrape_product
        result = scrape_product("https://www.daraz.pk/products/...")
        if result["price"]:
            base = result["price"]
        else:
            flash(result["error"])
    """
    url = url.strip()

    if not url or url == "#":
        return {"price": None, "name": None, "error": "No URL provided."}

    url_lower = url.lower()

    if "daraz.pk" in url_lower or "daraz." in url_lower:
        return scrape_daraz(url)

    elif "amazon." in url_lower:
        return scrape_amazon(url)

    elif "flipkart.com" in url_lower:
        return scrape_flipkart(url)

    else:
        # Try generic for other platforms
        return scrape_generic(url)


# ── Refresh price for existing product ────────────────────────
def refresh_price(url: str) -> float | None:
    """
    Used by the scheduled price refresh task.
    Returns just the updated price float, or None if scraping failed.
    """
    result = scrape_product(url)
    return result.get("price")
