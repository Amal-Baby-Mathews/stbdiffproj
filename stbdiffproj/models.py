from django.db import models
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)
class Image(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images/')
    caption=models.CharField(max_length=100)