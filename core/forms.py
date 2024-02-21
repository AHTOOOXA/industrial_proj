from datetime import datetime
from django.utils.timezone import now

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import DateInput
from django.forms.models import inlineformset_factory

from django_select2 import forms as s2forms

from core.models import User, ReportEntry, Report, OrderEntry, Order, Detail, Machine, Plan, PlanEntry
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Submit, Button


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
        self.helper.form_id = 'user-form'
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
        self.fields['order'].queryset = Order.objects.order_by('-date')
        # self.fields['order'].widget = s2forms.ModelSelect2Widget(
        #     model=Order,
        #     search_fields=['name__icontains'],
        # )

    class Meta:
        model = Report
        fields = ['user', 'date', 'order', 'step']
        labels = {
            'user': 'Пользователь',
            'date': 'Дата',
            'order': 'Заказ',
            'step': 'Этап',
        }
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            # 'order': forms.Select(attrs={'class': 'form'}),
        }


class ReportEntryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'report-entry-form'
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.render_hidden_fields = True
        # self.fields['detail'].widget = s2forms.ModelSelect2Widget(
        #     model=Detail,
        #     search_fields=['name__icontains'],
        #     dependent_fields={'order': 'order'},
        #     max_results=500,
        # )
        self.helper.layout = Layout(
            Row(
                Field('machine', wrapper_class='form-group col mb-0',
                      hx_get='/htmx/machine_options',
                      hx_include="[name='step']",
                      hx_trigger="change from:#id_step",
                      ),
                Field('detail', wrapper_class='form-group col mb-0',
                      hx_get='/htmx/detail_options',
                      hx_include="[name='order']",
                      hx_trigger="change from:#id_order",
                      ),
                Field('quantity', wrapper_class='form-group col mb-0'),
                Div(Field('DELETE', wrapper_class='form-group col mb-0'), css_class='d-none'),
                Button('cancel', 'x', css_class='form-group col-1 btn btn-danger mb-3',
                       onclick="handleCancelClick(this)",
                       ),
            )
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
    can_delete=True,
)


class OrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'order-form'
        self.helper.form_tag = False
        self.helper.disable_csrf = True

    class Meta:
        model = Order
        fields = ['name', 'number', 'date']
        labels = {
            'name': 'Название',
            'number': 'Заказ №',
            'date': 'Дата',
        }
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local',
                                               # 'value': datetime.now().strftime("%Y-%m-%dT%H:%M")
                                               })
        }


class OrderEntryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'order-entry-form'
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.render_hidden_fields = True
        self.helper.layout = Layout(
            Row(
                Field('detail', wrapper_class='form-group col mb-0'),
                Field('quantity', wrapper_class='form-group col mb-0'),
                Div(Field('DELETE', wrapper_class='form-group col mb-0'), css_class='d-none'),
                Button('cancel', 'x', css_class='form-group col-1 btn btn-danger mb-3',
                       onclick="handleCancelClick(this)",
                       ),
            )
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
    can_delete=True,
)


class DetailForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'detail-form'
        self.helper.add_input(Submit('sumbit', 'Подтвердить'))

    class Meta:
        model = Detail
        fields = ['name']
        labels = {
            'name': 'Название',
        }


class MachineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'machine-form'
        self.helper.add_input(Submit('sumbit', 'Подтвердить'))

    class Meta:
        model = Machine
        fields = ['name', 'step']
        labels = {
            'name': 'Название',
            'step': 'Этап',
        }


# class PlanForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper(self)
#         self.helper.form_id = 'plan-form'
#         self.helper.render_hidden_fields = True
#         self.helper.form_show_labels = False
#         for field in self.fields:
#             new_data = {
#                 'hx-target': 'closest td',
#                 'hx-swap': 'innerHTML',
#                 'hx-post': 'htmx/plan_cell_save',
#                 'hx-trigger': 'change, keyup, changed',  # delay:500ms
#             }
#             self.fields[field].widget.attrs.update(new_data)
#
#     class Meta:
#         model = Plan
#         fields = ['date', 'machine', 'detail', 'quantity']
#         widgets = {
#             'date': forms.HiddenInput(),
#             'machine': forms.HiddenInput(),
#         }


class PlanForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'order-form'
        self.helper.form_tag = False
        self.helper.disable_csrf = True

    class Meta:
        model = Plan
        fields = ['date', 'machine']
        widgets = {
            'date': forms.HiddenInput(),
            'machine': forms.HiddenInput(),
        }


class PlanEntryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'order-entry-form'
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.render_hidden_fields = True
        self.helper.layout = Layout(
            Row(
                Field('detail', wrapper_class='form-group col mb-0'),
                Field('quantity', wrapper_class='form-group col mb-0'),
                Div(Field('DELETE', wrapper_class='form-group col mb-0'), css_class='d-none'),
                Button('cancel', 'x', css_class='form-group col-1 btn btn-danger mb-3',
                       onclick="handleCancelClick(this)",
                       ),
            )
        )

    class Meta:
        model = PlanEntry
        fields = ['detail', 'quantity']
        labels = {
            'detail': 'Деталь №',
            'quantity': 'Количество',
        }


PlanEntryFormset = inlineformset_factory(
    Plan,
    PlanEntry,
    form=PlanEntryForm,
    min_num=1,
    extra=0,
    can_delete=True,
)
