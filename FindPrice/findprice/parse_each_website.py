import re
import json
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from show.models import Product


# -------------------------------------------------------------------------
# Save product to database
# -------------------------------------------------------------------------
def save_product(name, price, link, image_link, source):
    Product.objects.create(
        name=name,
        price=price,
        link=link,
        image_link=image_link,
        source=source
    )


def _make_session():
    """Create a requests session with realistic browser headers."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/131.0.0.0 Safari/537.36'
        ),
        'Accept': (
            'text/html,application/xhtml+xml,application/xml;'
            'q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
        ),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    })
    return session


# -------------------------------------------------------------------------
# Get data from Amazon
# -------------------------------------------------------------------------
def get_data_amazon(search_query):
    print('Find products at Amazon...')
    url = f"https://www.amazon.com/s?k={quote_plus(search_query)}"
    try:
        session = _make_session()
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        results = soup.select('[data-component-type="s-search-result"]')
        saved = 0
        for item in results[:4]:
            title_el = item.select_one('h2 a span') or item.select_one('h2 span')
            price_el = item.select_one('.a-price .a-offscreen')
            link_el = item.select_one('h2 a')
            img_el = item.select_one('img.s-image')

            name = title_el.get_text(strip=True) if title_el else ''
            price = price_el.get_text(strip=True) if price_el else ''
            link = ''
            if link_el and link_el.get('href'):
                href = link_el['href']
                link = href if href.startswith('http') else f"https://www.amazon.com{href}"
            image = img_el['src'] if img_el and img_el.get('src') else 'None'

            if name and price and link:
                save_product(name, price, link, image, 'Amazon')
                saved += 1

        print(f'Amazon: Finished! Saved {saved} products.')
    except Exception as e:
        print(f'Amazon: Scraping failed: {e}')


# -------------------------------------------------------------------------
# Get data from Walmart
# -------------------------------------------------------------------------
def get_data_walmart(search_query):
    print('Find products at Walmart...')
    url = f"https://www.walmart.com/search?q={quote_plus(search_query)}"
    try:
        session = _make_session()
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        saved = 0

        # Strategy 1: Parse __NEXT_DATA__ JSON (Walmart uses Next.js)
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if script_tag and script_tag.string:
            try:
                data = json.loads(script_tag.string)
                search_result = data['props']['pageProps']['initialData']['searchResult']
                items = search_result['itemStacks'][0]['items']
                for item in items[:4]:
                    if item.get('__typename') not in ('Product',):
                        continue
                    name = item.get('name', '')
                    price_info = item.get('priceInfo', {}).get('currentPrice', {})
                    price_val = price_info.get('price')
                    price = f"${price_val}" if price_val else ''
                    canon = item.get('canonicalUrl', '')
                    link = f"https://www.walmart.com{canon}" if canon else ''
                    image = item.get('imageInfo', {}).get('thumbnailUrl', '') or 'None'

                    if name and price and link:
                        save_product(name, price, link, image, 'Walmart')
                        saved += 1

                if saved > 0:
                    print(f'Walmart: Finished! Saved {saved} products.')
                    return
            except (KeyError, IndexError, TypeError):
                pass

        # Strategy 2: Look for embedded JSON in any script tag
        for script in soup.find_all('script'):
            if not script.string:
                continue
            if '"searchResult"' in script.string or '"itemStacks"' in script.string:
                try:
                    match = re.search(
                        r'"itemStacks"\s*:\s*\[(\{.*?\})\]',
                        script.string
                    )
                    if not match:
                        continue
                    # Try to find product data patterns
                    matches = re.findall(
                        r'\{"__typename"\s*:\s*"Product".*?\}(?=,\s*\{|\])',
                        script.string
                    )
                    for m in matches[:4]:
                        try:
                            item = json.loads(m)
                            name = item.get('name', '')
                            price_val = (
                                item.get('priceInfo', {})
                                .get('currentPrice', {})
                                .get('price')
                            )
                            price = f"${price_val}" if price_val else ''
                            canon = item.get('canonicalUrl', '')
                            link = (
                                f"https://www.walmart.com{canon}" if canon else ''
                            )
                            image = (
                                item.get('imageInfo', {}).get('thumbnailUrl', '')
                                or 'None'
                            )
                            if name and price and link:
                                save_product(name, price, link, image, 'Walmart')
                                saved += 1
                        except (json.JSONDecodeError, KeyError):
                            continue
                except Exception:
                    continue

        # Strategy 3: Fall back to HTML parsing
        if saved == 0:
            titles = soup.select('[data-automation-id="product-title"]')
            if not titles:
                titles = soup.select('span.lh-title')
            if not titles:
                titles = soup.select('[link-identifier]')

            for title_el in titles[:4]:
                name = title_el.get_text(strip=True)
                # Walk up DOM to find parent card
                card = title_el
                for _ in range(10):
                    if card.parent:
                        card = card.parent
                        if card.name in ('div', 'li') and card.find('img'):
                            break

                link_el = (
                    card.select_one('a[href*="/ip/"]')
                    or title_el.find_parent('a')
                )
                img_el = card.select_one('img')
                price_el = (
                    card.select_one('[data-automation-id="product-price"]')
                    or card.select_one('[itemprop="price"]')
                )

                link = ''
                if link_el and link_el.get('href'):
                    href = link_el['href']
                    link = (
                        href if href.startswith('http')
                        else f"https://www.walmart.com{href}"
                    )
                image = img_el['src'] if img_el and img_el.get('src') else 'None'
                price = ''
                if price_el:
                    match = re.search(r'\$[\d,.]+', price_el.get_text())
                    price = match.group(0) if match else ''

                if name and price and link:
                    save_product(name, price, link, image, 'Walmart')
                    saved += 1

        print(f'Walmart: Finished! Saved {saved} products.')
    except Exception as e:
        print(f'Walmart: Scraping failed: {e}')


# -------------------------------------------------------------------------
# Get data from eBay
# -------------------------------------------------------------------------
def get_data_ebay(search_query):
    print('Find products at eBay...')
    url = f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(search_query)}"
    try:
        session = _make_session()
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')

        results = soup.select('.srp-results .s-item')
        saved = 0
        # Skip first item (often a placeholder on eBay)
        for item in results[1:5]:
            title_el = (
                item.select_one('.s-item__title span[role="heading"]')
                or item.select_one('.s-item__title')
            )
            price_el = item.select_one('.s-item__price')
            link_el = item.select_one('.s-item__link')
            img_el = item.select_one('.s-item__image-wrapper img')

            name = title_el.get_text(strip=True) if title_el else ''
            price = price_el.get_text(strip=True) if price_el else ''
            link = link_el['href'] if link_el and link_el.get('href') else ''
            image = 'None'
            if img_el:
                image = (
                    img_el.get('src') or img_el.get('data-src') or 'None'
                )

            if name and price and link:
                save_product(name, price, link, image, 'eBay')
                saved += 1

        print(f'eBay: Finished! Saved {saved} products.')
    except Exception as e:
        print(f'eBay: Scraping failed: {e}')


# -------------------------------------------------------------------------
# Run all scrapers sequentially
# -------------------------------------------------------------------------
def scrape_all(search_query):
    try:
        get_data_walmart(search_query)
    except Exception as e:
        print(f'Walmart scraper error: {e}')
    try:
        get_data_ebay(search_query)
    except Exception as e:
        print(f'eBay scraper error: {e}')
    try:
        get_data_amazon(search_query)
    except Exception as e:
        print(f'Amazon scraper error: {e}')
