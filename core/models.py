from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, Group


# Create your models here.
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        MODERATOR = 'MODERATOR', 'Moderator'
        WORKER = 'WORKER', 'Worker'

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


class ReportEntry(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    machine = models.ForeignKey(Machine, null=True, on_delete=models.CASCADE)
    detail = models.ForeignKey(Detail, null=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'ReportEntry {self.pk} by {self.user.username}'


# class Report(models.Model):
#     # date time ...
#     pass
