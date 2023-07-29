from django.db import models
from django.contrib.auth.models import AbstractUser


class Car(models.Model):
    manufacturer = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    

# Create your models here.
class User(AbstractUser):
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True)