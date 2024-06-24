from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=512)
    price = models.CharField(max_length=50)
    link = models.URLField()
    image_link = models.URLField()
    source = models.CharField(max_length=100)  # Field for source (Walmart, eBay, Amazon)


    def __str__(self):
        return self.name

