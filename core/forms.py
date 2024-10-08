from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout, Submit
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms.models import inlineformset_factory

from core.models import (
    Detail,
    Machine,
    Order,
    OrderEntry,
    Plan,
    PlanEntry,
    Report,
    ReportEntry,
    User,
)


class Row(Div):
    css_class = "row g-3"


class UserCreateAdminForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = "user-form"
        self.helper.add_input(Submit("sumbit", "Подтвердить"))

    class Meta:
        model = User
        fields = ["username", "password1", "password2", "role"]
        labels = {
            "username": "Имя пользователя",
            "password1": "Пароль",
            "password2": "Подтвердите пароль",
            "role": "Роль",
        }


class ReportForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = "report-form"
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.fields["order"].queryset = Order.objects.filter(is_active=True).order_by("-date")

    class Meta:
        model = Report
        fields = ["user", "date", "order", "step"]
        labels = {
            "user": "Пользователь",
            "date": "Дата",
            "order": "Заказ",
            "step": "Этап",
        }
        widgets = {
            "date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class ReportEntryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = "report-entry-form"
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.render_hidden_fields = True
        self.fields["detail"].queryset = Detail.objects.order_by("name")
        self.helper.layout = Layout(
            Row(
                Field(
                    "machine",
                    wrapper_class="form-group col mb-0",
                    hx_get="/htmx/machine_options",
                    hx_include="[name='step'], closest select",
                    hx_trigger="change from:#id_step, load",
                ),
                Field(
                    "detail",
                    wrapper_class="form-group col mb-0",
                    hx_get="/htmx/detail_options",
                    hx_include="[name='order'], closest select",
                    hx_trigger="change from:#id_order, load",
                ),
                Field("quantity", wrapper_class="form-group col mb-0"),
                Div(Field("DELETE", wrapper_class="form-group col mb-0"), css_class="d-none"),
                HTML(
                    """
                    <div class="mb-3 form-group col-1 mb-0 mt-4 me-1">
                    <label class="form-label requiredField"> </label>
                    <a class="btn btn-danger d-flex align-items-center justify-content-center"
                    type="button" onclick="handleCancelClick(this)">
                    <i class="bi bi-trash-fill"></i>
                    </a>
                    </div>
                    """
                ),
            )
        )

    class Meta:
        model = ReportEntry
        fields = ["machine", "detail", "quantity"]
        labels = {
            "machine": "Станок",
            "detail": "Деталь №",
            "quantity": "Количество",
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
        self.helper.form_id = "order-form"
        self.helper.form_tag = False
        self.helper.disable_csrf = True

    class Meta:
        model = Order
        fields = ["name", "number", "date"]
        labels = {
            "name": "Название",
            "number": "Заказ №",
            "date": "Дата",
        }
        widgets = {
            "date": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    # 'value': datetime.now().strftime("%Y-%m-%dT%H:%M")
                }
            )
        }


class OrderEntryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = "order-entry-form"
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.render_hidden_fields = True
        self.fields["detail"].queryset = Detail.objects.order_by("name")
        self.helper.layout = Layout(
            Row(
                Field("detail", wrapper_class="form-group col mb-0"),
                Field("quantity", wrapper_class="form-group col mb-0"),
                Div(Field("DELETE", wrapper_class="form-group col mb-0"), css_class="d-none"),
                HTML(
                    """
                    <div class="mb-3 form-group col-1 mb-0 mt-4 me-1">
                    <label class="form-label requiredField"> </label>
                    <a class="btn btn-danger d-flex align-items-center justify-content-center"
                    type="button" onclick="handleCancelClick(this)">
                    <i class="bi bi-trash-fill"></i>
                    </a>
                    </div>
                    """
                ),
            )
        )

    class Meta:
        model = OrderEntry
        fields = ["detail", "quantity"]
        labels = {
            "detail": "Деталь №",
            "quantity": "Количество",
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
        self.helper.form_id = "detail-form"
        self.helper.add_input(Submit("sumbit", "Подтвердить"))

    class Meta:
        model = Detail
        fields = ["name"]
        labels = {
            "name": "Название",
        }


class MachineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = "machine-form"
        self.helper.add_input(Submit("sumbit", "Подтвердить"))

    class Meta:
        model = Machine
        fields = ["name", "step"]
        labels = {
            "name": "Название",
            "step": "Этап",
        }


class PlanForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = "order-form"
        self.helper.form_tag = False
        self.helper.disable_csrf = True

    class Meta:
        model = Plan
        fields = ["date", "machine"]
        widgets = {
            "date": forms.HiddenInput(),
            "machine": forms.HiddenInput(),
        }


class PlanEntryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = "order-entry-form"
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.render_hidden_fields = True
        self.fields["detail"].queryset = Detail.objects.order_by("name")
        self.fields["order"].queryset = Order.objects.filter(is_active=True).order_by("-date")
        self.helper.layout = Layout(
            Row(
                Field("order", wrapper_class="form-group col mb-0", id="id_order"),
                Field("detail", wrapper_class="form-group col mb-0"),
                Field("quantity", wrapper_class="form-group col mb-0"),
                Div(Field("DELETE", wrapper_class="form-group col mb-0"), css_class="d-none"),
                HTML(
                    """
                    <div class="mb-3 form-group col-1 mb-0 mt-4 me-3">
                    <label class="form-label requiredField"> </label>
                    <a class="btn btn-danger"
                    type="button" onclick="handleCancelClick(this)">
                    <i class="bi bi-trash-fill"></i>
                    </a>
                    </div>
                    """
                ),
            )
        )

    class Meta:
        model = PlanEntry
        fields = ["order", "detail", "quantity"]
        labels = {
            "order": "Заказ №",
            "detail": "Деталь №",
            "quantity": "Количество",
        }


PlanEntryFormset = inlineformset_factory(
    Plan,
    PlanEntry,
    form=PlanEntryForm,
    min_num=1,
    extra=0,
    can_delete=True,
)
