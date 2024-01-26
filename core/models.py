from django.utils.timezone import now

from django.conf import settings
from django.contrib import admin
from django.db import models
from django.contrib.auth.models import AbstractUser, Group


# Create your models here.
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Администратор'
        MODERATOR = 'MODERATOR', 'Модератор'
        WORKER = 'WORKER', 'Рабочий'

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.WORKER)


class ModeratorManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(role=User.Role.MODERATOR)


class WorkerManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(role=User.Role.WORKER)


class Moderator(User):
    objects = ModeratorManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        if not self.pk:
            self.role = User.Role.MODERATOR
        super().save(*args, **kwargs)
        if not self.pk:
            self.groups.add(Group.objects.get(name='Moderators'))


class Worker(User):
    objects = WorkerManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        if not self.pk:
            self.role = User.Role.WORKER
        super().save(*args, **kwargs)
        if not self.pk:
            self.groups.add(Group.objects.get(name='Workers'))


class Machine(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Detail(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Shift(models.Model):
    name = models.CharField(max_length=40)


class Report(models.Model):
    # date time ...
    user = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE)
    date = models.DateTimeField(default=now)
    # shift = models.ForeignKey(Shift, on_delete=models.CASCADE)


class ReportEntry(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, null=True, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, null=True, on_delete=models.CASCADE)
    detail = models.ForeignKey(Detail, null=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


class Order(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    date = models.DateTimeField(default=now)


class OrderEntry(models.Model):
    order = models.ForeignKey(Order, null=True, on_delete=models.CASCADE)
    detail = models.ForeignKey(Detail, null=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
