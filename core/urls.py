from django.urls import path
from . import views 


urlpatterns = [
    path("", views.home, name='home'),
    path("worker_form", views.worker_form, name='worker_form'),
    path("table", views.table, name='table'),
    path("login", views.login_user, name='login_user'),
    path("logout_user", views.logout_user, name='logout_user'),
    path("register", views.register_user, name='register_user'),
]
