import re
import json
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from show.models import Product
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async


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

save_product_async = sync_to_async(save_product)


# -------------------------------------------------------------------------
# Stealth browser helpers
# -------------------------------------------------------------------------
STEALTH_JS = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
    });
    window.chrome = {runtime: {}};
    const origQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({state: Notification.permission})
            : origQuery(parameters);
"""

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/131.0.0.0 Safari/537.36'
)


async def _create_stealth_page(browser):
    """Create a new browser context + page with stealth settings."""
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent=USER_AGENT,
        locale='en-US',
        timezone_id='America/New_York',
        java_script_enabled=True,
    )
    page = await context.new_page()
    await page.add_init_script(STEALTH_JS)
    return page, context


async def _get_rendered_soup(page, url, wait_selector=None, timeout=30000):
    """Navigate to URL, wait for JS to render, return BeautifulSoup of the
    fully-rendered page."""
    await page.goto(url, wait_until='domcontentloaded', timeout=timeout)
    try:
        await page.wait_for_load_state('networkidle', timeout=timeout)
    except Exception:
        pass  # Continue even if networkidle times out

    if wait_selector:
        try:
            await page.wait_for_selector(wait_selector, timeout=timeout)
        except Exception:
            pass  # Continue even if selector not found – we try fallbacks

    # Let dynamic content settle
    await page.wait_for_timeout(3000)

    html = await page.content()
    return BeautifulSoup(html, 'lxml')


# -------------------------------------------------------------------------
# Get data from Amazon
# -------------------------------------------------------------------------
async def get_data_amazon(browser, search_query):
    print('Find products at Amazon...')
    url = f"https://www.amazon.com/s?k={quote_plus(search_query)}"
    page, context = await _create_stealth_page(browser)
    try:
        soup = await _get_rendered_soup(
            page, url,
            wait_selector='[data-component-type="s-search-result"]',
        )

        # Try multiple selectors for product cards
        results = soup.select('[data-component-type="s-search-result"]')
        if not results:
            results = soup.select('[data-asin]:not([data-asin=""])')
        if not results:
            results = soup.select('div.s-result-item')

        saved = 0
        for item in results[:4]:
            title_el = (
                item.select_one('h2 a span')
                or item.select_one('h2 span')
                or item.select_one('[data-cy="title-recipe"] a span')
            )
            price_el = (
                item.select_one('.a-price .a-offscreen')
                or item.select_one('.a-price-whole')
            )
            link_el = (
                item.select_one('h2 a')
                or item.select_one('a.a-link-normal[href*="/dp/"]')
            )
            img_el = (
                item.select_one('img.s-image')
                or item.select_one('.s-image')
            )

            name = title_el.get_text(strip=True) if title_el else ''
            price = price_el.get_text(strip=True) if price_el else ''
            link = ''
            if link_el and link_el.get('href'):
                href = link_el['href']
                link = href if href.startswith('http') else f"https://www.amazon.com{href}"
            image = img_el.get('src', 'None') if img_el else 'None'

            if name and price and link:
                await save_product_async(name, price, link, image, 'Amazon')
                saved += 1

        print(f'Amazon: Finished! Saved {saved} products.')
    except Exception as e:
        print(f'Amazon: Scraping failed: {e}')
    finally:
        await context.close()


# -------------------------------------------------------------------------
# Get data from Walmart
# -------------------------------------------------------------------------
async def get_data_walmart(browser, search_query):
    print('Find products at Walmart...')
    url = f"https://www.walmart.com/search?q={quote_plus(search_query)}"
    page, context = await _create_stealth_page(browser)
    try:
        soup = await _get_rendered_soup(page, url, timeout=30000)

        saved = 0

        # Strategy 1: Parse __NEXT_DATA__ JSON (Walmart uses Next.js)
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if script_tag and script_tag.string:
            try:
                data = json.loads(script_tag.string)
                search_result = data['props']['pageProps']['initialData']['searchResult']
                items = search_result['itemStacks'][0]['items']
                for item in items[:4]:
                    if item.get('__typename') != 'Product':
                        continue
                    name = item.get('name', '')
                    price_info = item.get('priceInfo', {}).get('currentPrice', {})
                    price_val = price_info.get('price')
                    price = f"${price_val}" if price_val else ''
                    canon = item.get('canonicalUrl', '')
                    link = f"https://www.walmart.com{canon}" if canon else ''
                    image = item.get('imageInfo', {}).get('thumbnailUrl', '') or 'None'

                    if name and price and link:
                        await save_product_async(name, price, link, image, 'Walmart')
                        saved += 1

                if saved > 0:
                    print(f'Walmart: Finished! Saved {saved} products.')
                    return
            except (KeyError, IndexError, TypeError):
                pass

        # Strategy 2: Look for product data in any script tag
        for script in soup.find_all('script'):
            if not script.string or '"itemStacks"' not in script.string:
                continue
            try:
                # Find the full JSON object containing itemStacks
                text = script.string
                start = text.find('"itemStacks"')
                if start == -1:
                    continue
                # Extract product items using regex
                product_matches = re.finditer(
                    r'"name"\s*:\s*"([^"]+)".*?'
                    r'"canonicalUrl"\s*:\s*"([^"]+)".*?'
                    r'"price"\s*:\s*([\d.]+)',
                    text[start:]
                )
                for m in product_matches:
                    if saved >= 4:
                        break
                    name = m.group(1)
                    canon = m.group(2)
                    price_val = m.group(3)
                    link = f"https://www.walmart.com{canon}"
                    price = f"${price_val}"
                    if name and price and link:
                        await save_product_async(name, price, link, 'None', 'Walmart')
                        saved += 1
            except Exception:
                continue

        # Strategy 3: HTML parsing with multiple selector fallbacks
        if saved == 0:
            # Try various selectors Walmart has used
            selectors_to_try = [
                '[data-automation-id="product-title"]',
                'span[data-automation-id="product-title"]',
                'a[link-identifier]',
                'span.lh-title',
                '[data-testid="list-view"] a span',
            ]
            titles = []
            for sel in selectors_to_try:
                titles = soup.select(sel)
                if titles:
                    break

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
                    or card.select_one('div[aria-hidden="true"]')
                )

                link = ''
                if link_el and link_el.get('href'):
                    href = link_el['href']
                    link = (
                        href if href.startswith('http')
                        else f"https://www.walmart.com{href}"
                    )
                image = img_el.get('src', 'None') if img_el else 'None'
                price = ''
                if price_el:
                    match = re.search(r'\$[\d,.]+', price_el.get_text())
                    price = match.group(0) if match else ''

                if name and price and link:
                    await save_product_async(name, price, link, image, 'Walmart')
                    saved += 1

        print(f'Walmart: Finished! Saved {saved} products.')
    except Exception as e:
        print(f'Walmart: Scraping failed: {e}')
    finally:
        await context.close()


# -------------------------------------------------------------------------
# Get data from eBay
# -------------------------------------------------------------------------
async def get_data_ebay(browser, search_query):
    print('Find products at eBay...')
    url = f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(search_query)}"
    page, context = await _create_stealth_page(browser)
    try:
        soup = await _get_rendered_soup(
            page, url,
            wait_selector='.s-item',
        )

        # Try multiple selectors
        results = soup.select('.srp-results .s-item')
        if not results:
            results = soup.select('li.s-item')
        if not results:
            results = soup.select('.srp-river-results .s-item')

        saved = 0
        # Skip first item (often a placeholder on eBay)
        items = results[1:5] if len(results) > 1 else results[:4]
        for item in items:
            title_el = (
                item.select_one('.s-item__title span[role="heading"]')
                or item.select_one('.s-item__title span')
                or item.select_one('.s-item__title')
            )
            price_el = item.select_one('.s-item__price')
            link_el = item.select_one('.s-item__link')
            img_el = (
                item.select_one('.s-item__image-wrapper img')
                or item.select_one('.s-item__image img')
            )

            name = title_el.get_text(strip=True) if title_el else ''
            # Skip the "Shop on eBay" placeholder
            if name.lower().startswith('shop on ebay'):
                continue
            price = price_el.get_text(strip=True) if price_el else ''
            link = link_el['href'] if link_el and link_el.get('href') else ''
            image = 'None'
            if img_el:
                image = (
                    img_el.get('src')
                    or img_el.get('data-src')
                    or 'None'
                )

            if name and price and link:
                await save_product_async(name, price, link, image, 'eBay')
                saved += 1

        print(f'eBay: Finished! Saved {saved} products.')
    except Exception as e:
        print(f'eBay: Scraping failed: {e}')
    finally:
        await context.close()


# -------------------------------------------------------------------------
# Run all scrapers sequentially
# -------------------------------------------------------------------------
async def scrape_all(search_query):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ],
        )
        try:
            await get_data_walmart(browser, search_query)
            await get_data_ebay(browser, search_query)
            await get_data_amazon(browser, search_query)
        finally:
            await browser.close()
