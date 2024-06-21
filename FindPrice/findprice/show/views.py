from django.shortcuts import render, redirect
from .models import Product
#from django.contrib.auth.decorators import login_required
#from django.apps import apps
#from django.db import transaction
#from django.contrib.admin.views.decorators import staff_member_required
import asyncio
import sys
import os
from django.http import HttpResponse
from parse_each_website import get_data_walmart, get_data_ebay, get_data_amazon


def index(request):
    products = Product.objects.all()
    return render(request, 'index.html', {'products': products})


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


