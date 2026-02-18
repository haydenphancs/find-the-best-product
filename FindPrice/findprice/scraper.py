import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'findprice_main.settings')
import django
import asyncio
django.setup()
from findprice.parse_each_website import scrape_all


if __name__ == '__main__':
    search_query = input('Search for: ')
    asyncio.run(scrape_all(search_query))
