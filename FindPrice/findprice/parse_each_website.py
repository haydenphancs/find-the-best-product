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
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector('.s-main-slot')
        tree = HTMLParser(await page.content())
        if page:
            main_result = tree.css_first('.s-main-slot')
            result_number = 2
            while True:
                selector = f'div[data-cel-widget="search_result_{result_number}"]'
                result = main_result.css_first(selector)

                # Find data to name
                span_element_case_1 = result.css_first('span[class="a-size-base-plus a-color-base"]')
                if span_element_case_1:
                    # Add data to name
                    name_brand = span_element_case_1.text(strip=True)
                    span_element_case_1_b = result.css_first('span[class="a-size-base-plus a-color-base a-text-normal"]')
                    name_title = span_element_case_1_b.text(strip=True)
                    name = name_brand + ' ' + name_title
                else:
                    # Find and add data to name
                    span_element_case_2 = result.css_first('span[class="a-size-medium a-color-base a-text-bold a-text-normal"]')
                    if span_element_case_2:
                        name_brand = span_element_case_2.text(strip=True)
                    else:
                        name_brand = ''
                    span_element_case_2_b = result.css_first('span[class="a-size-medium a-color-base a-text-normal"]')
                    if span_element_case_2_b:
                        name_title = span_element_case_2_b.text(strip=True)
                    else:
                        name_title = ''
                    name = name_brand + ' ' + name_title

                # Find and add data to price
                price_whole_element = result.css_first('.a-price-whole').text(strip=True)
                price_fraction_element = result.css_first('.a-price-fraction').text(strip=True)
                price = '$' + price_whole_element + price_fraction_element

                # Find and add data to get_href
                a_element = result.css_first('.a-link-normal.s-underline-text.s-underline-link-text.s-link-style.a-text-normal')
                href = a_element.attributes.get('href', '')
                get_href = 'amazon.com' + href

                # Find and add data to image_link
                img_element = result.css_first('.s-image.s-image-optimized-rendering')
                image_link = img_element.attributes.get('src', '')
                source = 'Amazon'
                if name and price and href and image_link:
                    #Add all data to database
                    await add_product_data_amazon(name, price, get_href, image_link, source)
                else:
                    print('Entry error!')
                result_number += 1
                if result_number > 5:
                    print('Finished!')
                    break

        else:
            return 'Error parser the page!'

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

    response = requests.get(url, headers=headers)
    if response:
        soup1 = BeautifulSoup(response.content, "html.parser")
        soup2 = BeautifulSoup(soup1.prettify(), "html.parser")
        element = soup2.find("div", id='0', class_="flex flex-column justify-center")
        # find all the names
        product_names = soup2.find_all('span',{'data-automation-id': 'product-title'})
        # find all the prices
        product_prices = element.find_all('div', {'data-automation-id': 'product-price'})
        # find all the links
        product_links = element.find_all('a', class_="absolute w-100 h-100 z-1 hide-sibling-opacity", href=True)
        # find all image links
        product_images = element.find_all('div', class_="relative overflow-hidden")

        counter = 0
        for link in product_links:
            if counter > 4:
                # Adding data to name
                name = product_names[counter].get_text(strip=True)
                # Find and add data to price
                prices = product_prices[counter].find('span', class_='w_iUH7')
                price_string = prices.get_text(strip=True)
                price = extract_price(price_string)
                # Adding data to url
                url = "https://www.walmart.com" + link["href"]
                # Find and Add data to image_url
                image_url = product_images[counter].find('img').get('src')
                image_link = urljoin(url, image_url)
                # Adding them all to database
                source = 'Walmart'
                add_product_data(name, price, url, image_link, source)
            counter += 1
            if counter == 9:
                print('Finished!')
                break

    else:
        print('Walmart Bad')
        return None


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

    response = requests.get(url)
    if response:

        soup1 = BeautifulSoup(response.content, "html.parser")
        soup2 = BeautifulSoup(soup1.prettify(), "html.parser")

        element = soup2.find("div", id="srp-river-results", class_="srp-river-results clearfix")

        # find all the names
        product_names = element.find_all('div',class_="s-item__title")
        # find all the prices
        product_prices = element.find_all('div', class_="s-item__details-section--primary")
        # find all the links
        product_links = element.find_all('a', class_="s-item__link", href=True)
        # find all image links
        product_images = element.find_all('div', class_="s-item__image-wrapper image-treatment")

        counter = 0
        for names in product_names:
            # Adding data to name
            name = names.find('span', {'role': 'heading'}).get_text(strip=True)
            # Find and add data to price
            price = product_prices[counter].find('span', class_='s-item__price').get_text(strip=True)
            # Adding data to url
            url = product_links[counter]["href"]
            # Find and Add data to image_url
            image_url = product_images[counter].find('img').get('src')
            image_link = urljoin(url, image_url)
            # Adding them all to database
            source = 'eBay'
            add_product_data(name, price, url, image_link, source)
            counter += 1
            if counter == 4:
                print('Finished!')
                break
    else:
        print('Ebay Bad')
        return None


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

# For BeautifulSoup to find amazon data
# -------------------------------------------------------------------------
# find data Amazon for each product
# -------------------------------------------------------------------------

# def find_name_amazon(item):
#     name_tag = item.find('span', id='productTitle', class_='a-size-large product-title-word-break').get_text(strip=True)
#     if name_tag:
#         return name_tag
#     return 'None'
#
# def find_price_amazon(item):
#     price1 = item.find('div', id='corePrice_desktop', class_='celwidget')
#     if price1:
#         price_spans = price1.find_all('span', class_='a-offscreen')
#         prices = [price.get_text(strip=True) for price in price_spans]
#         concatenated_prices = ' - '.join(prices)
#         if concatenated_prices:
#             return concatenated_prices
#
#     price1 = item.find('div', id="corePrice_feature_div", class_="celwidget")
#     if price1:
#         price_spans = price1.find('span', class_='a-offscreen').get_text(strip=True)
#         # prices = [price.get_text(strip=True) for price in price_spans]
#         # concatenated_prices2 = ' - '.join(prices)
#         if price_spans:
#             return price_spans
#
#     return 'None'
#
# def find_image_amazon(item, url):
#     image_div = item.find('div', id='imgTagWrapperId', class_="imgTagWrapper")
#     if image_div:
#         img = image_div.find('img')
#         if img:
#             image_url = img.get('src')
#             # Handle relative URLs
#             image_url = urljoin(url, image_url)
#             return image_url
#     return 'None'
#

# -------------------------------------------------------------------------
# Add product to database for Walmart and Ebay
# -------------------------------------------------------------------------
