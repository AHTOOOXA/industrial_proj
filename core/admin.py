from django.contrib import admin
from core.models import User, Machine, Detail, ReportEntry

# Register your models here.
admin.site.register(User)
admin.site.register(Machine)
admin.site.register(Detail)
admin.site.register(ReportEntry)
