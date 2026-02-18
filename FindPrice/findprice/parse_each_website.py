from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
from show.models import Product
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async
from selectolax.parser import HTMLParser
import re



# -------------------------------------------------------------------------
# Get data from Amazon
# Use Playwright method
# -------------------------------------------------------------------------
async def get_data_amazon(search_query):
    print('Find products at Amazon...')
    url = f"https://www.amazon.com/s?k={search_query}"
    browser = None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_selector('.s-main-slot', timeout=10000)
            tree = HTMLParser(await page.content())
            main_result = tree.css_first('.s-main-slot')
            if not main_result:
                print('Amazon: Could not find main result container.')
                return

            for result_number in range(2, 6):
                try:
                    selector = f'div[data-cel-widget="search_result_{result_number}"]'
                    result = main_result.css_first(selector)
                    if not result:
                        continue

                    # Find data to name
                    name = ''
                    span_element_case_1 = result.css_first('span[class="a-size-base-plus a-color-base"]')
                    if span_element_case_1:
                        name_brand = span_element_case_1.text(strip=True)
                        span_element_case_1_b = result.css_first('span[class="a-size-base-plus a-color-base a-text-normal"]')
                        name_title = span_element_case_1_b.text(strip=True) if span_element_case_1_b else ''
                        name = (name_brand + ' ' + name_title).strip()
                    else:
                        span_element_case_2 = result.css_first('span[class="a-size-medium a-color-base a-text-bold a-text-normal"]')
                        name_brand = span_element_case_2.text(strip=True) if span_element_case_2 else ''
                        span_element_case_2_b = result.css_first('span[class="a-size-medium a-color-base a-text-normal"]')
                        name_title = span_element_case_2_b.text(strip=True) if span_element_case_2_b else ''
                        name = (name_brand + ' ' + name_title).strip()

                    # Find and add data to price
                    price_whole_el = result.css_first('.a-price-whole')
                    price_fraction_el = result.css_first('.a-price-fraction')
                    if not price_whole_el:
                        continue
                    price = '$' + price_whole_el.text(strip=True) + (price_fraction_el.text(strip=True) if price_fraction_el else '00')

                    # Find and add data to get_href
                    a_element = result.css_first('.a-link-normal.s-underline-text.s-underline-link-text.s-link-style.a-text-normal')
                    if not a_element:
                        continue
                    href = a_element.attributes.get('href', '')
                    get_href = 'https://www.amazon.com' + href

                    # Find and add data to image_link
                    img_element = result.css_first('.a-section.aok-relative.s-image-tall-aspect img')
                    image_link = img_element.attributes.get('src', '') if img_element else 'None'

                    source = 'Amazon'
                    if name and price and href:
                        await add_product_data_amazon(name, price, get_href, image_link, source)

                except Exception as e:
                    print(f'Amazon: Error parsing result #{result_number}: {e}')

            print('Amazon: Finished!')

    except Exception as e:
        print(f'Amazon: Scraping failed: {e}')
    finally:
        if browser:
            await browser.close()


# -------------------------------------------------------------------------
# Get data from Walmart
# Use BeautifulSoup method
# -------------------------------------------------------------------------
def get_data_walmart(search_query):
    print('Find products at Walmart...')
    url = f"https://www.walmart.com/search/?query={search_query.replace(' ', '%20')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
        "Accept-Encoding": "gzip, deflate", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "DNT": "1", "Connection": "close", "Upgrade-Insecure-Requests": "1"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException as e:
        print(f'Walmart: Request failed: {e}')
        return None

    if not response or response.status_code != 200:
        print(f'Walmart: Bad response (status {response.status_code if response else "None"})')
        return None

    soup1 = BeautifulSoup(response.content, "html.parser")
    soup2 = BeautifulSoup(soup1.prettify(), "html.parser")
    element = soup2.find("div", id='0', class_="flex flex-column justify-center")

    if not element:
        print('Walmart: Could not find main product container. Site structure may have changed.')
        return None

    # find all the names
    product_names = soup2.find_all('span', {'data-automation-id': 'product-title'})
    # find all the prices
    product_prices = element.find_all('div', {'data-automation-id': 'product-price'})
    # find all the links
    product_links = element.find_all('a', class_="w-100 h-100 z-1 hide-sibling-opacity absolute", href=True)
    # find all image links
    product_images = element.find_all('div', class_="relative overflow-hidden")

    counter = 0
    for link in product_links:
        if counter > 4:
            try:
                if counter >= len(product_names) or counter >= len(product_prices) or counter >= len(product_images):
                    break
                # Adding data to name
                name = product_names[counter].get_text(strip=True)
                # Find and add data to price

                prices = product_prices[counter].find('span', class_='w_iUH7')
                if not prices:
                    counter += 1
                    continue
                price_string = prices.get_text(strip=True)
                price = extract_price(price_string)
                if not price:
                    counter += 1
                    continue
                # Adding data to url
                product_url = "https://www.walmart.com" + link["href"]
                # Find and Add data to image_url
                img_tag = product_images[counter].find('img')
                if not img_tag:
                    counter += 1
                    continue
                image_url = img_tag.get('src')
                image_link = urljoin(product_url, image_url)
                # Adding them all to database
                source = 'Walmart'
                add_product_data(name, price, product_url, image_link, source)
            except Exception as e:
                print(f'Walmart: Error parsing product #{counter}: {e}')
        counter += 1
        if counter == 9:
            print('Walmart: Finished!')
            break


# -------------------------------------------------------------------------
# Get data from Ebay
# Use BeautifulSoup method
# -------------------------------------------------------------------------
def get_data_ebay(search_query):
    print('Find products at eBay...')
    url = f"https://www.ebay.com/sch/i.html?_nkw={search_query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
        "Accept-Encoding": "gzip, deflate", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "DNT": "1", "Connection": "close", "Upgrade-Insecure-Requests": "1"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
    except requests.RequestException as e:
        print(f'eBay: Request failed: {e}')
        return None

    if not response or response.status_code != 200:
        print(f'eBay: Bad response (status {response.status_code if response else "None"})')
        return None

    soup1 = BeautifulSoup(response.content, "html.parser")
    soup2 = BeautifulSoup(soup1.prettify(), "html.parser")

    element = soup2.find("div", id="srp-river-results", class_="srp-river-results clearfix")

    if not element:
        print('eBay: Could not find main product container. Site structure may have changed.')
        return None

    # find all the names
    product_names = element.find_all('div', class_="s-item__title")
    # find all the prices
    product_prices = element.find_all('div', class_="s-item__details-section--primary")
    # find all the links
    product_links = element.find_all('a', class_="s-item__link", href=True)
    # find all image links
    product_images = element.find_all('div', class_="s-item__image-wrapper image-treatment")

    counter = 0
    for names in product_names:
        try:
            if counter >= len(product_prices) or counter >= len(product_links) or counter >= len(product_images):
                break
            # Adding data to name
            heading = names.find('span', {'role': 'heading'})
            if not heading:
                counter += 1
                continue
            name = heading.get_text(strip=True)
            # Find and add data to price
            price_el = product_prices[counter].find('span', class_='s-item__price')
            if not price_el:
                counter += 1
                continue
            price = price_el.get_text(strip=True)
            # Adding data to url
            product_url = product_links[counter]["href"]
            # Find and Add data to image_url
            img_tag = product_images[counter].find('img')
            if not img_tag:
                counter += 1
                continue
            image_url = img_tag.get('src')
            image_link = urljoin(product_url, image_url)
            # Adding them all to database
            source = 'eBay'
            add_product_data(name, price, product_url, image_link, source)
        except Exception as e:
            print(f'eBay: Error parsing product #{counter}: {e}')
        counter += 1
        if counter == 4:
            print('eBay: Finished!')
            break


# -------------------------------------------------------------------------
# Add data to a product for Walmart and Ebay
# -------------------------------------------------------------------------
def add_product_data(get_name, get_price, get_link, get_image_link, get_source):
    Product.objects.create(
        name=get_name,
        price=get_price,
        link=get_link,
        image_link=get_image_link,
        source=get_source
    )


# -------------------------------------------------------------------------
# Add directly data to database for Amazon
# -------------------------------------------------------------------------
def save_to_db_amazon(get_name, get_price, get_link, get_image_link, get_source):
    Product.objects.create(
        name=get_name,
        price=get_price,
        link=get_link,
        image_link=get_image_link,
        source=get_source
    )

# Wrap the synchronous function with sync_to_async
add_product_data_amazon = sync_to_async(save_to_db_amazon)


# -------------------------------------------------------------------------
# Only get the price (number) of a string
# -------------------------------------------------------------------------
def extract_price(price_string):
    # Use regular expression to find all parts of the string that match the pattern for a price
    match = re.search(r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?', price_string)
    if match:
        return match.group(0)
    return None
