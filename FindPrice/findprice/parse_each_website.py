from urllib.parse import quote_plus
from show.models import Product
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async

# -------------------------------------------------------------------------
# Save product to database (Moved to top for cleaner access)
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
# Get data from Amazon using Playwright
# -------------------------------------------------------------------------
async def get_data_amazon(search_query):
    print('Find products at Amazon...')
    url = f"https://www.amazon.com/s?k={quote_plus(search_query)}"
    browser = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until='domcontentloaded')
            await page.wait_for_selector('[data-component-type="s-search-result"]', timeout=15000)

            products = await page.evaluate('''() => {
                const results = document.querySelectorAll('[data-component-type="s-search-result"]');
                const items = [];
                for (let i = 0; i < Math.min(results.length, 4); i++) {
                    const el = results[i];
                    const titleEl = el.querySelector('h2 a span');
                    const priceEl = el.querySelector('.a-price .a-offscreen');
                    const linkEl = el.querySelector('h2 a');
                    const imgEl = el.querySelector('img.s-image');
                    items.push({
                        name: titleEl ? titleEl.textContent.trim() : '',
                        price: priceEl ? priceEl.textContent.trim() : '',
                        link: linkEl ? linkEl.href : '',
                        image: imgEl ? imgEl.src : '',
                    });
                }
                return items;
            }''')

            saved = 0
            for p in products:
                if p['name'] and p['price'] and p['link']:
                    await save_product_async(
                        p['name'], p['price'], p['link'], p['image'] or 'None', 'Amazon'
                    )
                    saved += 1
            print(f'Amazon: Finished! Saved {saved} products.')

    except Exception as e:
        print(f'Amazon: Scraping failed: {e}')
    finally:
        if browser:
            await browser.close()


# -------------------------------------------------------------------------
# Get data from Walmart using Playwright
# -------------------------------------------------------------------------
async def get_data_walmart(search_query):
    print('Find products at Walmart...')
    url = f"https://www.walmart.com/search?q={quote_plus(search_query)}"
    browser = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set User Agent to avoid immediate blocking
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })

            await page.goto(url, wait_until='domcontentloaded')
            await page.wait_for_selector('[data-automation-id="product-title"]', timeout=15000)

            products = await page.evaluate('''() => {
                const titles = document.querySelectorAll('[data-automation-id="product-title"]');
                const items = [];
                for (let i = 0; i < Math.min(titles.length, 4); i++) {
                    const titleEl = titles[i];
                    // Walk up to find the product card container
                    let card = titleEl.closest('[data-item-id]')
                        || titleEl.closest('[data-testid]')
                        || titleEl.closest('li');
                    
                    if (!card) {
                        card = titleEl;
                        // Fallback search up the tree
                        for (let j = 0; j < 8; j++) {
                            if (card.parentElement) card = card.parentElement;
                            if (card.querySelector('img') && card.querySelector('a[href*="/ip/"]')) break;
                        }
                    }

                    const linkEl = card.querySelector('a[href*="/ip/"]') || titleEl.closest('a');
                    const imgEl = card.querySelector('img');
                    const priceEl = card.querySelector('[data-automation-id="product-price"]')
                        || card.querySelector('[itemprop="price"]');

                    let price = '';
                    if (priceEl) {
                        const match = priceEl.textContent.trim().match(/\\$[\\d,.]+/);
                        price = match ? match[0] : '';
                    }

                    items.push({
                        name: titleEl.textContent.trim(),
                        price: price,
                        link: linkEl ? linkEl.href : '',
                        image: imgEl ? imgEl.src : '',
                    });
                }
                return items;
            }''')

            saved = 0
            for p in products:
                if p['name'] and p['price'] and p['link']:
                    await save_product_async(
                        p['name'], p['price'], p['link'], p['image'] or 'None', 'Walmart'
                    )
                    saved += 1
            print(f'Walmart: Finished! Saved {saved} products.')

    except Exception as e:
        print(f'Walmart: Scraping failed: {e}')
    finally:
        if browser:
            await browser.close()


# -------------------------------------------------------------------------
# Get data from eBay using Playwright
# -------------------------------------------------------------------------
async def get_data_ebay(search_query):
    print('Find products at eBay...')
    url = f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(search_query)}"
    browser = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until='domcontentloaded')
            await page.wait_for_selector('.srp-results .s-item', timeout=15000)

            products = await page.evaluate('''() => {
                const items_el = document.querySelectorAll('.srp-results .s-item');
                const items = [];
                // Skip first item (often a placeholder)
                for (let i = 1; i < Math.min(items_el.length, 5); i++) {
                    const el = items_el[i];
                    const titleEl = el.querySelector('.s-item__title span[role="heading"]')
                        || el.querySelector('.s-item__title');
                    const priceEl = el.querySelector('.s-item__price');
                    const linkEl = el.querySelector('.s-item__link');
                    const imgEl = el.querySelector('.s-item__image-wrapper img');
                    items.push({
                        name: titleEl ? titleEl.textContent.trim() : '',
                        price: priceEl ? priceEl.textContent.trim() : '',
                        link: linkEl ? linkEl.href : '',
                        image: imgEl ? imgEl.src : '',
                    });
                }
                return items;
            }''')

            saved = 0
            for p in products:
                if p['name'] and p['price'] and p['link']:
                    await save_product_async(
                        p['name'], p['price'], p['link'], p['image'] or 'None', 'eBay'
                    )
                    saved += 1
            print(f'eBay: Finished! Saved {saved} products.')

    except Exception as e:
        print(f'eBay: Scraping failed: {e}')
    finally:
        if browser:
            await browser.close()


# -------------------------------------------------------------------------
# Run all scrapers sequentially
# -------------------------------------------------------------------------
async def scrape_all(search_query):
    try:
        await get_data_walmart(search_query)
    except Exception as e:
        print(f'Walmart scraper error: {e}')
    try:
        await get_data_ebay(search_query)
    except Exception as e:
        print(f'eBay scraper error: {e}')
    try:
        await get_data_amazon(search_query)
    except Exception as e:
        print(f'Amazon scraper error: {e}')