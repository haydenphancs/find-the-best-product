from django.shortcuts import render, redirect
from .models import Product
import asyncio

from parse_each_website import scrape_all


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
        if product_name:
            asyncio.run(scrape_all(product_name))

    return redirect('index')


def delete_all_data(request):
    Product.objects.all().delete()
    return redirect('index')
