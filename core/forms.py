from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms.models import inlineformset_factory

from core.models import User, ReportEntry, Report, OrderEntry, Order
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Submit, Button, Hidden


class Row(Div):
    css_class = 'row g-3'


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']


class UserCreateAdminForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'user-create-admin-form'
        self.helper.attrs = {
            'hx-post': 'register_user_admin',
            'hx-target': '#user-create-admin-form',
            'hx-swap': 'outerHTML',
        }
        self.helper.add_input(Submit('sumbit', 'Подтвердить'))

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'role']
        labels = {
            'username': 'Имя пользователя',
            'password1': 'Пароль',
            'password2': 'Подтвердите пароль',
            'role': 'Роль',
        }


class ReportForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'report-form'
        self.helper.form_tag = False
        self.helper.disable_csrf = True

    class Meta:
        model = Report
        fields = ['user', 'date']
        labels = {
            'user': 'Пользователь',
            'date': 'Дата',
        }
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime'})
        }


class ReportEntryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'report-entry-form'
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.render_hidden_fields = True
        self.helper.layout = Layout(
            Row(
                Field('machine', wrapper_class='form-group col-md-3 mb-0'),
                Field('detail', wrapper_class='form-group col-md-3 mb-0'),
                Field('quantity', wrapper_class='form-group col-md-3 mb-0'),
                # Button('cancel', 'Cancel', css_class='form-group col-md-3 mb-0 btn btn-danger mb-3'),
            ),
        )

    class Meta:
        model = ReportEntry
        fields = ['machine', 'detail', 'quantity']
        labels = {
            'machine': 'Станок',
            'detail': 'Деталь №',
            'quantity': 'Количество',
        }


ReportEntryFormset = inlineformset_factory(
    Report,
    ReportEntry,
    form=ReportEntryForm,
    min_num=1,
    extra=0,
)


class NewReportForm(forms.ModelForm):

    extra_field = ReportEntryFormset()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'report-form'
        self.helper.form_tag = False
        self.helper.disable_csrf = True

    class Meta:
        model = Report
        fields = ['user', 'date']
        labels = {
            'user': 'Пользователь',
            'date': 'Дата',
        }
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime'})
        }


class OrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'order-form'
        self.helper.form_tag = False
        self.helper.disable_csrf = True

    class Meta:
        model = Order
        fields = ['name', 'date']
        labels = {
            'name': 'Название',
            'date': 'Дата',
        }


class OrderEntryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'order-entry-form'
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                Field('detail', wrapper_class='form-group col-md-3 mb-0'),
                Field('quantity', wrapper_class='form-group col-md-3 mb-0'),
                # Button('cancel', 'Cancel', css_class='form-group col-md-3 mb-0 btn btn-danger mb-3'),
            ),
        )

    class Meta:
        model = OrderEntry
        fields = ['detail', 'quantity']
        labels = {
            'detail': 'Деталь №',
            'quantity': 'Количество',
        }


OrderEntryFormset = inlineformset_factory(
    Order,
    OrderEntry,
    form=OrderEntryForm,
    min_num=1,
    extra=0,
)
