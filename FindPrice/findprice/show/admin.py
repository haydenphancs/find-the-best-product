from django.contrib import admin
from .models import Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'link', 'image_link', 'source')


admin.site.register(Product, ProductAdmin)
