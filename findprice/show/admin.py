from django.contrib import admin
from .models import Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'link', 'delivery_info')


admin.site.register(Product, ProductAdmin)
