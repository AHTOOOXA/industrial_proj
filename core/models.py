from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from django.conf import settings
from django.contrib import admin
from django.db import models
from django.contrib.auth.models import AbstractUser, Group


# Create your models here.
class MyValidator(UnicodeUsernameValidator):
    regex = r'^[\w.@+\- ]+$'


class User(AbstractUser):
    username_validator = MyValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

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


class Step(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Machine(models.Model):
    name = models.CharField(max_length=200)
    step = models.ForeignKey(Step, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class Detail(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Order(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    number = models.CharField(max_length=200, default=0)
    date = models.DateTimeField()

    def __str__(self):
        return str(self.number)


class OrderEntry(models.Model):
    order = models.ForeignKey(Order, null=True, on_delete=models.CASCADE)
    detail = models.ForeignKey(Detail, null=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


class Report(models.Model):
    # date time ...
    user = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE)
    date = models.DateTimeField()
    order = models.ForeignKey(Order, null=True, blank=False, on_delete=models.CASCADE)
    step = models.ForeignKey(Step, null=False, blank=False, on_delete=models.CASCADE)

    def __str__(self):
        return "ОТЧЕТ " + str(self.user) + ": " + str(self.date)


class ReportEntry(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    report = models.ForeignKey(Report, null=True, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, null=True, on_delete=models.CASCADE)
    detail = models.ForeignKey(Detail, null=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


class Plan(models.Model):
    date = models.DateTimeField()
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    step = models.ForeignKey(Step, null=False, blank=False, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.date) + ' ' + str(self.step) + ' ' + str(self.machine)


class PlanEntry(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    detail = models.ForeignKey(Detail, null=True, blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(null=True, blank=True)


class Table(models.Model):
    current_date = models.DateTimeField(default=now)
    current_step = models.ForeignKey(Step, null=True, on_delete=models.SET_NULL)
