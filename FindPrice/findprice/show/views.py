from django.shortcuts import render, redirect
from .models import Product
import asyncio

from parse_each_website import get_data_walmart, get_data_ebay, get_data_amazon


def index(request):
    walmart_products = Product.objects.filter(source='Walmart')[:8]
    ebay_products = Product.objects.filter(source='eBay')[:8]
    amazon_products = Product.objects.filter(source='Amazon')[:8]

    context = {
        'walmart_products': walmart_products,
        'ebay_products': ebay_products,
        'amazon_products': amazon_products,
    }

    return render(request, 'index.html', context)

def search_results(request):
    if request.method == 'GET':
        product_name = request.GET.get('product_name', '')

        # Perform scraping for each website based on user input
        if product_name:
            try:
                get_data_walmart(product_name)
            except Exception as e:
                print(f'Walmart scraper error: {e}')

            try:
                get_data_ebay(product_name)
            except Exception as e:
                print(f'eBay scraper error: {e}')

            try:
                asyncio.run(get_data_amazon(product_name))
            except Exception as e:
                print(f'Amazon scraper error: {e}')

    return redirect('index')


def delete_all_data(request):
    Product.objects.all().delete()
    return redirect('index')  # redirect to home page or any other page after deletion


