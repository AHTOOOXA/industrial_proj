from django import forms
from django.contrib.auth.forms import UserCreationForm
from core.models import User, ReportEntry


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']


class WorkerForm(forms.ModelForm):
    class Meta:
        model = ReportEntry
        fields = ['machine', 'detail', 'quantity']
