from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests


search_query = "Acer Aspire 3 15.6 inch Laptop AMD"


def get_url_amazon():
    url = f"https://www.amazon.com/s?k={search_query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
        "Accept-Encoding": "gzip, deflate", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "DNT": "1", "Connection": "close", "Upgrade-Insecure-Requests": "1"}

    response = requests.get(url, headers=headers)
    if response:
        soup1 = BeautifulSoup(response.content, "html.parser")
        soup2 = BeautifulSoup(soup1.prettify(), "html.parser")

        product_link = soup2.find_all('a', class_="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal")
        urls = []
        counter = 0
        for link in product_link:
            counter += 1
            urls.append("https://www.amazon.com" + link["href"])
            if counter == 3:
                break
        return urls
    else:
        return None


def get_data_walmart():
    url = f"https://www.walmart.com/search/?query={search_query.replace(' ', '%20')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
        "Accept-Encoding": "gzip, deflate", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "DNT": "1", "Connection": "close", "Upgrade-Insecure-Requests": "1"}

    response = requests.get(url, headers=headers)

    print('Find products at Walmart...')
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
                price = prices.get_text(strip=True)
                # Adding data to url
                url = "https://www.walmart.com" + link["href"]
                # Find and Add data to image_url
                image_url = product_images[counter].find('img').get('src')
                image_link = urljoin(url, image_url)
                # Adding them all to database
                add_product_data(name, price, url, image_link)
            counter += 1
            if counter == 8:
                print('Finished!')
                break

    else:
        print('Walmart Bad')
        return None


# -------------------------------------------------------------------------
# Get data from Ebay
# -------------------------------------------------------------------------
def get_data_ebay():
    url = f"https://www.ebay.com/sch/i.html?_nkw={search_query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
        "Accept-Encoding": "gzip, deflate", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "DNT": "1", "Connection": "close", "Upgrade-Insecure-Requests": "1"}

    response = requests.get(url)
    print('Find products at Ebay...')
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
            add_product_data(name, price, url, image_link)
            counter += 1
            if counter == 3:
                print('Finished!')
                break
    else:
        print('Ebay Bad')
        return None


# -------------------------------------------------------------------------
# find data Amazon for each product
# -------------------------------------------------------------------------

def find_name_amazon(item):
    name_tag = item.find('span', id='productTitle', class_='a-size-large product-title-word-break').get_text(strip=True)
    if name_tag:
        return name_tag
    return 'None'


def find_price_amazon(item):
    price1 = item.find('div', id='corePrice_desktop', class_='celwidget')
    if price1:
        price_spans = price1.find_all('span', class_='a-offscreen')
        prices = [price.get_text(strip=True) for price in price_spans]
        concatenated_prices = ' - '.join(prices)
        if concatenated_prices:
            return concatenated_prices

    price1 = item.find('div', id="corePrice_feature_div", class_="celwidget")
    if price1:
        price_spans = price1.find('span', class_='a-offscreen').get_text(strip=True)
        # prices = [price.get_text(strip=True) for price in price_spans]
        # concatenated_prices2 = ' - '.join(prices)
        if price_spans:
            return price_spans

    return 'None'


def find_image_amazon(item, url):
    image_div = item.find('div', id='imgTagWrapperId', class_="imgTagWrapper")
    if image_div:
        img = image_div.find('img')
        if img:
            image_url = img.get('src')
            # Handle relative URLs
            image_url = urljoin(url, image_url)
            return image_url
    return 'None'


# -------------------------------------------------------------------------
# Add product to database for Walmart and Ebay
# -------------------------------------------------------------------------
def add_product_data(get_name, get_price, get_link, get_image_link):
    from findprice.scraper import save_to_db
    products = []
    try:
        name = get_name
        prices = get_price
        link = get_link
        image_link = get_image_link
        products.append({
            'name': name,
            'price': prices,
            'link': link,
            'delivery_info': image_link,
        })
    except Exception as e:
        print(f"Error passing data to product database: {e}")
    save_to_db(products)
