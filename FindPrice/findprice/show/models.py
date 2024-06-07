from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=512)
    price = models.CharField(max_length=50)
    link = models.URLField()
    delivery_info = models.CharField(max_length=255)

    def __str__(self):
        return self.name

