from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.home, name='home'),
    path("report_form", views.report_form, name='report_form'),
    path("htmx/add_report_entry_form", views.add_report_entry_form, name='add_report_entry_form'),
    path("htmx/detail_options", views.detail_options, name='detail_options'),
    path("htmx/machine_options", views.machine_options, name='machine_options'),
    path("report_success/<int:pk>", views.report_success, name='report_success'),
    path("reports", views.reports_view, name='reports_view'),
    path("reports/add", views.reports_add, name='reports_add'),
    path("reports/<int:pk>/edit", views.reports_edit, name='reports_edit'),
    path("reports/<int:pk>/delete", views.reports_delete, name='reports_delete'),
    path("stats", views.stats, name='stats'),
    path("htmx/report_modal", views.report_modal, name='report_modal'),
    path("htmx/plan_modal", views.plan_modal, name='plan_modal'),
    path("stats/shift_table/<slug:value>", views.shift_table, name='shift_table'),
    path("stats/switch_step/<int:step>", views.switch_step, name='switch_step'),
    path("stats/orders/add", views.orders_add, name='orders_add'),
    path("stats/orders/<int:pk>/edit", views.orders_edit, name='orders_edit'),
    path("htmx/add_order_entry_form", views.add_order_entry_form, name='add_order_entry_form'),
    path("stats/orders/delete/<int:pk>", views.orders_delete, name='orders_delete'),
    path("htmx/add_plan_entry_form", views.add_plan_entry_form, name='add_plan_entry_form'),
    path("details", views.details_view, name='details_view'),
    path("details/add", views.details_add, name='details_add'),
    path("details/<int:pk>/edit", views.details_edit, name='details_edit'),
    path("details/<int:pk>/delete", views.details_delete, name='details_delete'),
    path("machines", views.machines_view, name='machines_view'),
    path("machines/add", views.machines_add, name='machines_add'),
    path("machines/<int:pk>/edit", views.machines_edit, name='machines_edit'),
    path("machines/<int:pk>/delete", views.machines_delete, name='machines_delete'),
    path("users", views.users_view, name='users_view'),
    path("users/add", views.users_add, name='users_add'),
    path("users/<int:pk>/edit", views.users_edit, name='users_edit'),
    path("users/<int:pk>/delete", views.users_delete, name='users_delete'),
    path("login", views.login_user, name='login_user'),
    path("logout_user", views.logout_user, name='logout_user'),
]
