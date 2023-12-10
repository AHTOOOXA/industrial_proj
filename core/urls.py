from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name='home'),
    path("report_form", views.report_form, name='report_form'),
    path("htmx/add_report_entry_form", views.add_report_entry_form, name='add_report_entry_form'),
    path("reports", views.reports_view, name='reports_view'),
    path("reports/add", views.reports_add, name='reports_add'),
    path("reports/<int:pk>/edit", views.reports_edit, name='reports_edit'),
    path("reports/<int:pk>/delete", views.reports_delete, name='reports_delete'),
    path("reports/entry_delete/<int:r_pk>/<int:re_pk>", views.report_entries_delete, name='report_entries_delete'),
    path("stats", views.stats, name='stats'),
    path("stats/orders/add", views.orders_add, name='orders_add'),
    path("stats/orders/<int:pk>/edit", views.orders_edit, name='orders_edit'),
    path("htmx/add_order_entry_form", views.add_order_entry_form, name='add_order_entry_form'),
    path("stats/orders/delete/<int:pk>", views.orders_delete, name='orders_delete'),
    path("stats/orders/entry_delete/<int:r_pk>/<int:re_pk>", views.order_entries_delete, name='order_entries_delete'),
    path("login", views.login_user, name='login_user'),
    path("logout_user", views.logout_user, name='logout_user'),
    path("register_user_admin", views.register_user_admin, name='register_user_admin'),
]
