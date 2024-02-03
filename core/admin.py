from django.contrib import admin
from core.models import User, Machine, Detail, Report, ReportEntry, Order, OrderEntry, Table


# class ReportAdmin(admin.ModelAdmin):
#     list_display = ['user']


class ReportEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'report', 'machine', 'detail', 'quantity']


class OrderEntryAdmin(admin.ModelAdmin):
    list_display = ['order', 'detail', 'quantity']


# Register your models here.
admin.site.register(User)
admin.site.register(Machine)
admin.site.register(Detail)
admin.site.register(Report)
admin.site.register(ReportEntry, ReportEntryAdmin)
admin.site.register(Order)
admin.site.register(OrderEntry, OrderEntryAdmin)
admin.site.register(Table)
