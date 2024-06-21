import requests
from bs4 import BeautifulSoup
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findprice_main.settings')
import django
import asyncio
django.setup()
from show.models import Product
from findprice.parse_each_website import get_data_walmart, get_data_ebay, get_data_amazon

# admin: haiphan
# pw: 1234

# def get_html(url):
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
#         "Accept-Encoding": "gzip, deflate", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#         "DNT": "1", "Connection": "close", "Upgrade-Insecure-Requests": "1"}
#
#     try:
#         response = requests.get(url, headers=headers)
#         return response
#     except requests.RequestException as e:
#         print(f"Error fetching the HTML: {e}")
#         return None
#
#
# def parse_html(url):
#     html = get_html(url)
#     if html:
#         soup1 = BeautifulSoup(html.content, 'html.parser')
#         soup2 = BeautifulSoup(soup1.prettify(), "html.parser")
#         product = []
#         try:
#             name = find_name_amazon(soup2)
#             price = find_price_amazon(soup2)
#             link = url
#             image_link = find_image_amazon(soup2, url)
#             product.append({
#                 'name': name,
#                 'price': price,
#                 'link': link,
#                 'delivery_info': image_link,
#             })
#         except Exception as e:
#             print(f"Error parsing HTML: {e}")
#     return product
#
#
# def scrape_website(url):
#   #  html = get_html(url)
#    # if html:
#     products = parse_html(url)
#     save_to_db(products)
#    # else:
#    #     print('Failed to retrieve the web page')
#


# def save_to_db(products):
#     for product in products:
#         Product.objects.create(
#             name=product['name'],
#             price=product['price'],
#             link=product['link'],
#             delivery_info=product['delivery_info']
#         )


if __name__ == '__main__':
    #get_data_walmart()
    #get_data_ebay()
    #asyncio.run(get_data_amazon(search_query))
    print('Okay')
