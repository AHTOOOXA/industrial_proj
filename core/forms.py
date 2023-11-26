from django import forms
from django.contrib.auth.forms import UserCreationForm

from core.models import User, Car


class UserCreateForm(UserCreationForm):
    car = forms.ModelChoiceField(
        queryset=Car.objects.filter(country__in=['Germany', 'Italy'])
    )

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'car')
