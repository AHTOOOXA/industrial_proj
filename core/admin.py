from django.contrib import admin

from core.models import (
    Detail,
    Machine,
    Order,
    OrderEntry,
    Plan,
    Report,
    ReportEntry,
    Step,
    Table,
    User,
)


class ReportEntryAdmin(admin.ModelAdmin):
    list_display = ["user", "report", "machine", "detail", "quantity"]


class OrderEntryAdmin(admin.ModelAdmin):
    list_display = ["order", "detail", "quantity"]


class MachineAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


# Register your models here.
admin.site.register(User)
admin.site.register(Machine, MachineAdmin)
admin.site.register(Detail)
admin.site.register(Report)
admin.site.register(ReportEntry, ReportEntryAdmin)
admin.site.register(Order)
admin.site.register(OrderEntry, OrderEntryAdmin)
admin.site.register(Table)
admin.site.register(Plan)
admin.site.register(Step)
