from django.shortcuts import render, redirect
from .models import Product
import asyncio

from django.http import HttpResponse
from parse_each_website import get_data_walmart, get_data_ebay, get_data_amazon


# def index(request):
#     products = Product.objects.all()
#     return render(request, 'index.html', {'products': products})

def index(request):
    walmart_products = Product.objects.filter(source='Walmart')[:4]
    ebay_products = Product.objects.filter(source='eBay')[:4]
    amazon_products = Product.objects.filter(source='Amazon')[:4]

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
            get_data_walmart(product_name)
            get_data_ebay(product_name)
            asyncio.run(get_data_amazon(product_name))
            context = {
                'query': product_name,
                'search_results': search_results,
            }
        # Return a response or render a template with results
        return redirect('index')  # redirect to home page or any other page after deletion
    else:
        return redirect('index')  # redirect to home page or any other page after deletion


def delete_all_data(request):
    Product.objects.all().delete()
    return redirect('index')  # redirect to home page or any other page after deletion


