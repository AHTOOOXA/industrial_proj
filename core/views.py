import datetime
import logging

import pandas as pd
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.timezone import make_naive, now

from core.forms import (
    DetailForm,
    MachineForm,
    OrderEntryFormset,
    OrderForm,
    PlanEntryFormset,
    PlanForm,
    ReportEntryFormset,
    ReportForm,
    UserCreateAdminForm,
)

from .decorators import allowed_user_roles, toast_message, unauthenticated_user
from .models import (
    Detail,
    Machine,
    Order,
    Plan,
    PlanEntry,
    Report,
    ReportEntry,
    Step,
    Table,
    User,
)
from .scripts import (
    TableCell,
    get_orders_display,
    get_reports_results,
    get_reports_summary,
    get_reports_view,
    get_shifts_table,
    get_surplus_data,
)

logger = logging.getLogger(__name__)


@login_required(login_url="login_user")
def home(request):
    return render(request, "core/home.html")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def stats(request):
    steps, orders, leftovers, orders_stats = get_orders_display(is_active=True)

    current_date = Table.objects.all().first().current_date
    today = now()
    today = today - datetime.timedelta(days=5)
    today = today.replace(
        hour=current_date.hour % 12,
        minute=current_date.minute,
        second=current_date.second,
        microsecond=current_date.microsecond,
    )
    Table.objects.all().update(current_date=today)
    active_step_pk, machines, table = get_shifts_table()
    context = {
        "orders": orders,
        "leftovers": leftovers,
        "orders_stats": orders_stats,
        "steps": steps,
        "active_step_pk": active_step_pk,
        "machines": machines,
        "table": table,
    }
    return render(request, "core/stats.html", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def stats_orders_view_active(request):
    steps, orders, leftovers, orders_stats = get_orders_display(is_active=True)
    context = {
        "orders": orders,
        "leftovers": leftovers,
        "steps": steps,
        "orders_stats": orders_stats,
    }
    return HttpResponse(
        render_to_string("core/stats.html#order-button-sm-active")
        + (render_to_string("core/partials/orders_list.html", context, request))
    )


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def stats_orders_view_inactive(request):
    steps, orders, leftovers, orders_stats = get_orders_display(is_active=False)
    context = {
        "orders": orders,
        "leftovers": leftovers,
        "steps": Step.objects.all(),
        "orders_stats": orders_stats,
    }
    return HttpResponse(
        render_to_string("core/stats.html#order-button-sm-inactive")
        + (render_to_string("core/partials/orders_list.html", context, request))
    )


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def shift_table(request, value):
    current_date = Table.objects.all()[0].current_date
    new_date = current_date + int(value) * datetime.timedelta(hours=12)
    Table.objects.all().update(current_date=new_date)

    active_step_pk, machines, table = get_shifts_table()
    context = {"steps": Step.objects.all(), "active_step_pk": active_step_pk, "machines": machines, "table": table}
    return render(request, "core/stats.html#table", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def switch_step(request, step):
    Table.objects.all().update(current_step=step)

    active_step_pk, machines, table = get_shifts_table()
    context = {"steps": Step.objects.all(), "active_step_pk": active_step_pk, "machines": machines, "table": table}
    response = render(request, "core/stats.html#table", context)
    response["HX-Trigger-After-Settle"] = "scroll-table"
    return response


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def order_to_plan_drop(request):
    detail_id = request.POST.get("detail_id")
    order_id = request.POST.get("order_id")
    plan_id = request.POST.get("plan_id")
    leftover = int(request.POST.get("leftover", 0))  # Get leftover from the request

    plan = Plan.objects.get(id=plan_id)

    # Set the quantity as the minimum of leftover and 400
    leftover = max(-leftover, 0)
    quantity = min(leftover, 400)

    plan_entry = PlanEntry(plan=plan, order_id=order_id, detail_id=detail_id, quantity=quantity)
    plan_entry.save()

    cell = TableCell()
    cell.plan = plan
    context = {
        "cell": cell.get_display(),
        "new_plan_entry_id": plan_entry.id,
    }
    steps, order, leftovers, orders_stats = get_orders_display(order_id=order_id)
    order_context = {
        "steps": steps,
        "order": order,
        "leftovers": leftovers,
        "orders_stats": orders_stats,
        "hx_swap_oob": True,
    }
    response = HttpResponse(
        render_to_string("core/stats.html#plan_cell_inner", context, request)
        + render_to_string("core/partials/orders_list.html#order_card", order_context, request)
    )
    return response


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def plan_to_plan_drop(request):
    plan_entry_id = request.POST.get("plan_entry_id")
    plan_id = request.POST.get("plan_id")
    plan = Plan.objects.get(id=plan_id)
    plan_entry = PlanEntry.objects.get(id=plan_entry_id)
    old_plan_id = plan_entry.plan_id
    plan_entry.plan_id = plan_id
    plan_entry.save()
    cell = TableCell(plan=plan)
    context = {
        "cell": cell.get_display(),
    }
    old_plan = Plan.objects.get(id=old_plan_id)
    old_cell = TableCell(plan=old_plan)
    old_context = {
        "cell": old_cell.get_display(),
        "hx_swap_oob": True,
    }
    response = HttpResponse(
        render_to_string("core/stats.html#plan_cell_inner", context, request)
        + render_to_string("core/stats.html#plan_cell_inner", old_context, request)
    )
    return response


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def orders_view(request):
    steps, orders, leftovers, orders_stats = get_orders_display(is_active=True)
    context = {
        "orders": orders,
        "leftovers": leftovers,
        "steps": steps,
        "orders_stats": orders_stats,
    }
    return render(request, "core/orders.html", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def orders_view_active(request):
    steps, orders, leftovers, orders_stats = get_orders_display(is_active=True)
    context = {
        "orders": orders,
        "leftovers": leftovers,
        "steps": steps,
        "orders_stats": orders_stats,
    }
    return HttpResponse(
        render_to_string("core/orders.html#order-button-active")
        + (render_to_string("core/partials/orders_list.html", context, request))
    )


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def orders_view_inactive(request):
    steps, orders, leftovers, orders_stats = get_orders_display(is_active=False)
    context = {
        "orders": orders,
        "leftovers": leftovers,
        "steps": steps,
        "orders_stats": orders_stats,
    }
    return HttpResponse(
        render_to_string("core/orders.html#order-button-inactive")
        + (render_to_string("core/partials/orders_list.html", context, request))
    )


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
# TODO: fix toast message
# @toast_message(success_message="Заказ успешно добавлен", error_message="Ошибка при добавлении заказа")
def orders_add(request):
    if request.method == "GET":
        form = OrderForm(initial={"date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")})
        formset = OrderEntryFormset()
        context = {
            "form": form,
            "formset": formset,
        }
        return render(request, "core/order_add.html", context)
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            report_instance = form.save(commit=False)
            report_instance.save()

            entry_formset = OrderEntryFormset(request.POST, request.FILES, instance=report_instance)
            if entry_formset.is_valid():
                for entry_form in entry_formset:
                    if entry_form.cleaned_data["DELETE"] is not True:
                        entry_form.save()
        return redirect("stats")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def orders_set_active(request, pk):
    order = Order.objects.get(pk=pk)
    order.is_active = True
    order.save()
    return HttpResponse("")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def orders_set_inactive(request, pk):
    order = Order.objects.get(pk=pk)
    order.is_active = False
    order.save()
    return HttpResponse("")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def orders_edit(request, pk):
    order = Order.objects.get(pk=pk)
    if request.method == "GET":
        form = OrderForm(instance=order, initial={"date": make_naive(order.date).strftime("%Y-%m-%dT%H:%M")})
        formset = OrderEntryFormset(instance=order)
        context = {
            "order": order,
            "form": form,
            "formset": formset,
        }
        return render(request, "core/orders_edit.html", context)
    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)
        # print(form.is_valid())
        if form.is_valid():
            order_instance = form.save(commit=False)
            order_instance.save()

            entry_formset = OrderEntryFormset(request.POST, request.FILES, instance=order_instance)
            # print(entry_formset.is_valid())
            # print(entry_formset.errors)
            if entry_formset.is_valid():
                for entry_form in entry_formset:
                    if entry_form.cleaned_data["DELETE"] is not True:
                        entry_form.save()
                    else:
                        # print(entry_form.cleaned_data)
                        if entry_form.cleaned_data["id"] is not None:
                            entry_form.cleaned_data["id"].delete()
        return redirect("stats")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def add_order_entry_form(request):
    if request.method == "GET":
        new_formset = OrderEntryFormset()
        form_number = int(request.GET.get("totalForms"))
        new_form = new_formset.empty_form
        new_form.prefix = new_form.prefix.replace("__prefix__", str(form_number))
        context = {
            "new_form": new_form,
            "new_total_forms_count": form_number + 1,
        }
        return render(request, "core/partials/order_entry_form.html", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def orders_delete(request, pk):
    Order.objects.get(pk=pk).delete()
    return HttpResponse("")


@unauthenticated_user
def login_user(request):
    if request.method == "GET":
        return render(request, "core/login.html", {})
    elif request.method == "HEAD":
        response = HttpResponse()
        response["Content-Type"] = "text/html; charset=utf-8"
        return response
    elif request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == "WORKER":
                return redirect("report_form")
            else:
                return redirect("stats")
        else:
            messages.error(request, "Ошибка при входе, попробуйте еще раз")
            return redirect("login_user")
    else:
        return HttpResponseNotAllowed(["GET", "POST"])


def logout_user(request):
    logout(request)
    messages.success(request, ("Вы вышли из системы"))
    return redirect("home")


@login_required(login_url="login_user")
def report_form(request):
    if request.method == "GET":
        # form = ReportForm(initial={'user': request.user, 'date': now()})
        form = ReportForm(initial={"user": request.user, "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")})
        form.fields["user"].disabled = True
        form.fields["date"].disabled = True
        formset = ReportEntryFormset()
        context = {
            "form": form,
            "formset": formset,
        }
        return render(request, "core/report_form.html", context)
    if request.method == "POST":
        # these weird copying required to process disabled fields
        POST = request.POST.copy()
        POST["user"] = request.user
        POST["date"] = now()
        form = ReportForm(POST)
        if form.is_valid():
            report_instance = form.save(commit=False)
            report_instance.save()

            entry_formset = ReportEntryFormset(request.POST, request.FILES, instance=report_instance)
            if entry_formset.is_valid():
                for entry_form in entry_formset:
                    if "DELETE" in entry_form.cleaned_data and entry_form.cleaned_data["DELETE"] is not True:
                        entry_form.save()
                messages.success(request, "Отчет успешно отправлен!")
            logout(request)
            return redirect("login_user")
        return redirect("report_form")


@login_required(login_url="login_user")
def report_confirmation(request):
    POST = request.POST.copy()
    if "user" not in POST:
        POST["user"] = request.user
    if "date" not in POST:
        POST["date"] = now()
    if request.method == "POST":
        form = ReportForm(POST)
        if form.is_valid():
            report_instance = form.save(commit=False)
            entry_formset = ReportEntryFormset(POST, request.FILES, instance=report_instance)
            if entry_formset.is_valid():
                report_entries = []
                for entry_form in entry_formset:
                    if "DELETE" in entry_form.cleaned_data and entry_form.cleaned_data["DELETE"] is not True:
                        entry = entry_form.save(commit=False)
                        report_entries.append(entry)
                context = {
                    "report": report_instance,
                    "report_entries": report_entries,
                }
                return render(request, "core/partials/report_confirmation.html", context)
            else:
                context = {
                    "errors": entry_formset.errors,
                }
                return render(request, "core/partials/report_confirmation_error.html", context)
        else:
            context = {
                "errors": form.errors,
            }
            return render(request, "core/partials/report_confirmation_error.html", context)


@login_required(login_url="login_user")
def add_report_entry_form(request):
    if request.method == "GET":
        new_formset = ReportEntryFormset()
        form_number = int(request.GET.get("totalForms"))
        new_form = new_formset.empty_form
        new_form.prefix = new_form.prefix.replace("__prefix__", str(form_number))
        context = {
            "new_form": new_form,
            "new_total_forms_count": form_number + 1,
        }
        return render(request, "core/partials/report_entry_form.html", context)


@login_required(login_url="login_user")
def detail_options(request):
    order = request.GET.get("order")
    details = []
    if order:
        details = Detail.objects.filter(orderentry__order=order)
        # entries = OrderEntry.objects.filter(order__pk=request.GET.get('order')).all()
        # for entry in entries:
        #     details.append({
        #         'id': entry.detail.id,
        #         'name': entry.detail.name,
        #     })
    else:
        details = Detail.objects.all().order_by("name")
    cur_value = next(request.GET.values())
    if cur_value != "":
        cur_value = int(cur_value)
    context = {
        "details": details,
        "cur_value": cur_value,
    }
    return render(request, "core/partials/detail_options.html", context)


@login_required(login_url="login_user")
def machine_options(request):
    step = request.GET.get("step")
    if step:
        machines = Machine.objects.filter(step__pk=step).all()
    else:
        machines = Machine.objects.all()
    cur_value = next(request.GET.values())
    if cur_value != "":
        cur_value = int(cur_value)
    context = {
        "machines": machines,
        "cur_value": cur_value,
    }
    return render(request, "core/partials/machines_options.html", context)


def report_success(request, pk):
    report = Report.objects.get(pk=pk)
    context = {
        "report": report,
    }
    return render(request, "core/report_success.html", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def reports_view(request):
    user_pk = request.GET.get("user_pk")
    month = request.GET.get("month")
    step_pk = request.GET.get("step_pk")

    # If no month is selected, default to current month
    if not month:
        month = datetime.datetime.now().strftime("%Y-%m")

    _, reports_by_day = get_reports_view(user_pk=user_pk, month=month, step_pk=step_pk)

    if request.htmx:
        context = {
            "reports_by_day": reports_by_day,
            "user_pk": user_pk,
            "step_pk": step_pk,
        }
        return render(request, "core/reports.html#reports_shifts", context)
    else:
        # initial page load
        users = User.objects.all().order_by("username")
        all_steps = Step.objects.all()
        context = {
            "reports_by_day": reports_by_day,
            "users": users,
            "all_steps": all_steps,
            "current_month": month,
            "user_pk": user_pk,
            "step_pk": step_pk,
        }
        return render(request, "core/reports.html", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def reports_add(request):
    if request.method == "GET":
        form = ReportForm(initial={"date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")})
        formset = ReportEntryFormset()
        context = {
            "form": form,
            "formset": formset,
        }
        return render(request, "core/report_form.html", context)
    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report_instance = form.save(commit=False)
            report_instance.save()

            entry_formset = ReportEntryFormset(request.POST, request.FILES, instance=report_instance)
            if entry_formset.is_valid():
                for entry_form in entry_formset:
                    if entry_form.cleaned_data["DELETE"] is not True:
                        entry_form.save()
                messages.success(request, "Отчет успешно отправлен!")
        return redirect("reports_view")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def reports_edit(request, pk):
    report = Report.objects.get(pk=pk)
    if request.method == "GET":
        form = ReportForm(instance=report, initial={"date": make_naive(report.date).strftime("%Y-%m-%dT%H:%M")})
        formset = ReportEntryFormset(instance=report)
        context = {
            "report": report,
            "form": form,
            "formset": formset,
        }
        return render(request, "core/reports_edit.html", context)
    if request.method == "POST":
        form = ReportForm(request.POST, instance=report)
        # print(form.is_valid())
        if form.is_valid():
            report_instance = form.save(commit=False)
            report_instance.save()

            entry_formset = ReportEntryFormset(request.POST, request.FILES, instance=report_instance)
            # print(entry_formset.is_valid())
            # print(entry_formset.errors)
            if entry_formset.is_valid():
                for entry_form in entry_formset:
                    if entry_form.cleaned_data["DELETE"] is not True:
                        entry_form.save()
                    else:
                        # print(entry_form.cleaned_data)
                        if entry_form.cleaned_data["id"] is not None:
                            entry_form.cleaned_data["id"].delete()
                messages.success(request, "Отчет успешно изменен!")
        return redirect("reports_view")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def reports_delete(request, pk):
    Report.objects.get(pk=pk).delete()
    return HttpResponse("")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def details_view(request):
    details = Detail.objects.all().order_by("-id")
    context = {
        "details": details,
    }
    return render(request, "core/details.html", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def details_add(request):
    if request.method == "GET":
        form = DetailForm()
        context = {
            "form": form,
        }
        return render(request, "core/detail_form.html", context)
    if request.method == "POST":
        form = DetailForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Деталь успешно дбавлена")
        return redirect("details_view")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def details_edit(request, pk):
    detail = Detail.objects.get(pk=pk)
    if request.method == "GET":
        form = DetailForm(instance=detail)
        context = {
            "detail": detail,
            "form": form,
        }
        return render(request, "core/details_edit.html", context)
    if request.method == "POST":
        form = DetailForm(request.POST, instance=detail)
        if form.is_valid():
            form.save()
            messages.success(request, "Деталь успешно изменена")
        return redirect("details_view")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def details_delete(request, pk):
    Detail.objects.get(pk=pk).delete()
    return HttpResponse("")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def machines_view(request):
    steps = Step.objects.all()
    steps_machines = {}
    for step in steps:
        step_machines = Machine.objects.filter(step=step).order_by("-id")
        steps_machines[step.id] = step_machines
    context = {
        "steps": steps,
        "steps_machines": steps_machines,
    }
    return render(request, "core/machines.html", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def machines_add(request):
    if request.method == "GET":
        form = MachineForm()
        context = {
            "form": form,
        }
        return render(request, "core/machine_form.html", context)
    if request.method == "POST":
        form = MachineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Станок успешно добавлен")
        return redirect("machines_view")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def machines_edit(request, pk):
    machine = Machine.objects.get(pk=pk)
    if request.method == "GET":
        form = MachineForm(instance=machine)
        context = {
            "machine": machine,
            "form": form,
        }
        return render(request, "core/machines_edit.html", context)
    if request.method == "POST":
        form = MachineForm(request.POST, instance=machine)
        if form.is_valid():
            form.save()
            messages.success(request, "Станок успешно изменен")
        return redirect("machines_view")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def machines_delete(request, pk):
    Machine.objects.get(pk=pk).delete()
    return HttpResponse("")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def users_view(request):
    users = User.objects.all().order_by("username")
    context = {
        "users": users,
    }
    return render(request, "core/users.html", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def users_add(request):
    if request.method == "GET":
        context = {"form": UserCreateAdminForm()}
        return render(request, "core/user_form.html", context)
    if request.method == "POST":
        form = UserCreateAdminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Сотрудник успешно зарегистрирован")
            return redirect("users_view")
        else:
            messages.error(request, "Ошибка")
            return redirect("users_add")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def users_edit(request, pk):
    user = User.objects.get(pk=pk)
    if request.method == "GET":
        form = UserCreateAdminForm(instance=user)
        context = {
            "user": user,
            "form": form,
        }
        return render(request, "core/users_edit.html", context)
    if request.method == "POST":
        form = UserCreateAdminForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Станок упешно изменен")
        return redirect("users_view")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def users_delete(request, pk):
    User.objects.get(pk=pk).delete()
    return HttpResponse("")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def report_modal(request):
    pk = int(str(request.GET.get("pk")))
    report = ReportEntry.objects.get(pk=pk).report
    context = {"report": report}
    return render(request, "core/partials/report_modal.html", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def add_plan_entry_form(request):
    if request.method == "GET":
        new_formset = PlanEntryFormset()
        form_number = int(request.GET.get("totalForms"))
        new_form = new_formset.empty_form
        new_form.prefix = new_form.prefix.replace("__prefix__", str(form_number))
        context = {
            "new_form": new_form,
            "new_total_forms_count": form_number + 1,
        }
        return render(request, "core/partials/plan_entry_form.html", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
# TODO: fix toast message
# @toast_message(success_message="План успешно обновлен", error_message="Ошибка при обновлении плана")
def plan_modal(request):
    if request.method == "GET":
        pk = int(str(request.GET.get("pk")))
        plan = Plan.objects.get(pk=pk)
        hx_target = "#" + TableCell(plan=plan).get_display()["id"]
        form = PlanForm(instance=plan)
        formset = PlanEntryFormset(instance=plan)
        context = {
            "plan": plan,
            "form": form,
            "formset": formset,
            "hx_target": hx_target,
        }
        return render(request, "core/partials/plan_modal.html", context)
    if request.method == "POST":
        pk = int(str(request.POST.get("pk")))
        plan = Plan.objects.get(pk=pk)
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            plan_instance = form.save(commit=False)
            plan_instance.save()

            entry_formset = PlanEntryFormset(request.POST, request.FILES, instance=plan_instance)
            # print(entry_formset.is_valid())
            # print(entry_formset.errors)
            if entry_formset.is_valid():
                for entry_form in entry_formset:
                    if entry_form.cleaned_data["DELETE"] is not True:
                        entry_form.save()
                    else:
                        # print(entry_form.cleaned_data)
                        if entry_form.cleaned_data["id"] is not None:
                            entry_form.cleaned_data["id"].delete()
        cell = TableCell(plan=plan)
        context = {
            "cell": cell.get_display(),
        }
        steps, orders, leftovers, orders_stats = get_orders_display()
        orders_context = {
            "steps": steps,
            "orders": orders,
            "leftovers": leftovers,
            "orders_stats": orders_stats,
            "hx_swap_oob": True,
        }
        return HttpResponse(
            render_to_string("core/stats.html#plan_cell_inner", context=context, request=request)
            + render_to_string("core/partials/orders_list.html#order_list", context=orders_context, request=request)
        )


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
@toast_message(
    success_message="Количество обновлено: '{detail_name}' ({old_quantity} → {new_quantity})",
    error_message="Ошибка при обновении количества для '{detail_name}'",
)
def update_plan_entry_quantity(request):
    if request.method == "POST":
        plan_entry_id = request.POST.get("plan_entry_id")
        new_quantity = request.POST.get("quantity")

        plan_entry = get_object_or_404(PlanEntry, id=plan_entry_id)
        old_quantity = plan_entry.quantity
        plan_entry.quantity = new_quantity
        plan_entry.save()

        steps, orders, leftovers, orders_stats = get_orders_display()
        orders_context = {
            "steps": steps,
            "orders": orders,
            "leftovers": leftovers,
            "orders_stats": orders_stats,
            "hx_swap_oob": True,
        }

        response = HttpResponse(render_to_string("core/partials/orders_list.html#order_list", orders_context, request))
        response.toast_data = {
            "detail_name": plan_entry.detail.name,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
        }
        return response

    return HttpResponseBadRequest("Invalid request method")


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def reports_summary(request):
    user_pk = request.GET.get("user_pk")
    month = request.GET.get("month")
    step_pk = request.GET.get("step_pk")
    force = request.GET.get("force") == "true"

    # If no month is selected, default to current month
    if not month:
        month = datetime.datetime.now().strftime("%Y-%m")

    # Only fetch data if a specific user is selected or force is True
    if user_pk or force:
        summary_list = get_reports_summary(user_pk=user_pk, month=month, step_pk=step_pk)
        total_quantity = sum(item["total_quantity"] for item in summary_list)
    else:
        summary_list = []
        total_quantity = 0

    if request.htmx:
        context = {
            "summary_list": summary_list,
            "total_quantity": total_quantity,
            "user_pk": user_pk,
            "step_pk": step_pk,
            "current_month": month,
            "force": force,  # Pass force to template
        }
        return render(request, "core/reports_summary.html#reports_summary", context)
    else:
        # initial page load
        users = User.objects.all().order_by("username")
        all_steps = Step.objects.all()
        context = {
            "summary_list": summary_list,
            "total_quantity": total_quantity,
            "users": users,
            "all_steps": all_steps,
            "current_month": month,
            "user_pk": user_pk,
            "step_pk": step_pk,
            "force": force,  # Pass force to template
        }
        return render(request, "core/reports_summary.html", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def reports_summary_download(request):
    user_pk = request.GET.get("user_pk")
    month = request.GET.get("month")
    step_pk = request.GET.get("step_pk")

    summary_list = get_reports_summary(user_pk=user_pk, month=month, step_pk=step_pk)

    # Convert summary data to pandas DataFrame
    data = []
    for item in summary_list:
        data.append(
            {
                "Пользователь": item["user"].username if item["user"] else "Без пользователя",
                "Этап": item["step"].name,
                "Деталь": item["detail"].name,
                "Количество": item["total_quantity"],
            }
        )

    df = pd.DataFrame(data)

    # Add total row
    total_quantity = sum(item["total_quantity"] for item in summary_list)
    total_row = pd.DataFrame([{"Пользователь": "ИТОГО", "Этап": "", "Деталь": "", "Количество": total_quantity}])
    df = pd.concat([total_row, df], ignore_index=True)

    # Create response
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f"attachment; filename=reports_summary_{month}.xlsx"

    # Write to excel
    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Сводка")
        worksheet = writer.sheets["Сводка"]

        # Adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception as e:
                    logger.error(e)
            adjusted_width = max_length + 2
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

    return response


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def reports_results(request):
    user_pk = request.GET.get("user_pk")
    month = request.GET.get("month")
    step_pk = request.GET.get("step_pk")

    # If no month is selected, default to current month
    if not month:
        month = datetime.datetime.now().strftime("%Y-%m")

    results_list, total_quantity, avg_per_user, active_users_count = get_reports_results(
        user_pk=user_pk, month=month, step_pk=step_pk
    )

    if request.htmx:
        context = {
            "results_list": results_list,
            "total_quantity": total_quantity,
            "avg_per_user": avg_per_user,
            "active_users_count": active_users_count,
            "user_pk": user_pk,
            "step_pk": step_pk,
        }
        return render(request, "core/reports_results.html#reports_results", context)
    else:
        users = User.objects.all().order_by("username")
        all_steps = Step.objects.all()
        context = {
            "results_list": results_list,
            "total_quantity": total_quantity,
            "avg_per_user": avg_per_user,
            "active_users_count": active_users_count,
            "users": users,
            "all_steps": all_steps,
            "current_month": month,
            "user_pk": user_pk,
            "step_pk": step_pk,
        }
        return render(request, "core/reports_results.html", context)


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def reports_results_download(request):
    user_pk = request.GET.get("user_pk")
    month = request.GET.get("month")

    results_list, total_quantity, avg_per_user, active_users_count = get_reports_results(user_pk=user_pk, month=month)

    # Convert to pandas DataFrame
    data = []
    for item in results_list:
        data.append(
            {
                "Пользователь": item["username"] if item["username"] else "Без пользователя",
                "Общее количество": item["total_quantity"],
                "% от общего": f"{item['percentage']:.1f}%",
            }
        )

    df = pd.DataFrame(data)

    # Add statistics rows
    stats_data = pd.DataFrame(
        [
            {"Пользователь": "ИТОГО", "Общее количество": total_quantity, "% от общего": "100%"},
            {"Пользователь": "Среднее на пользователя", "Общее количество": avg_per_user, "% от общего": ""},
            {"Пользователь": "Активных пользователей", "Общее количество": active_users_count, "% от общего": ""},
        ]
    )
    df = pd.concat([stats_data, df], ignore_index=True)

    # Create response
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f"attachment; filename=reports_results_{month}.xlsx"

    # Write to excel
    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Результаты")
        worksheet = writer.sheets["Результаты"]

        # Adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception as e:
                    logger.error(e)
            adjusted_width = max_length + 2
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

    return response


@login_required(login_url="login_user")
@allowed_user_roles(["ADMIN", "MODERATOR"])
def surplus(request):
    # Get surplus data for active orders
    steps, surplus_data, detail_names, detail_orders = get_surplus_data()

    # Group details by step pair, then by order
    step_pair_orders = {}

    # For each step pair, organize details by order
    for i in range(len(steps) - 1):
        prev_step = steps[i]
        next_step = steps[i + 1]
        step_pair = (prev_step, next_step)

        # Create structure for this step pair if it doesn't exist
        if step_pair not in step_pair_orders:
            step_pair_orders[step_pair] = {}

        for detail_id, surplus in surplus_data[step_pair].items():
            if surplus != 0:  # Only include non-zero surplus
                for order_info in detail_orders.get(detail_id, set()):
                    # Create list for this order if it doesn't exist
                    if order_info not in step_pair_orders[step_pair]:
                        step_pair_orders[step_pair][order_info] = []

                    # Add detail to this order for this step pair
                    step_pair_orders[step_pair][order_info].append(
                        {
                            "detail_id": detail_id,  # Include detail_id for sorting
                            "name": detail_names[detail_id],
                            "surplus": surplus,
                            "status": "positive" if surplus > 0 else "negative",
                        }
                    )

    # Final data structure for template
    step_pairs_data = []

    # Process each step pair in order
    for i in range(len(steps) - 1):
        prev_step = steps[i]
        next_step = steps[i + 1]
        step_pair = (prev_step, next_step)

        if step_pair not in step_pair_orders:
            continue  # Skip if no data for this step pair

        # Sort orders by number (descending)
        orders = sorted(
            step_pair_orders[step_pair].keys(),
            key=lambda x: int(x.split("№")[1].strip()) if "№" in x else 0,
            reverse=True,
        )

        # Process orders for this step pair
        orders_data = []
        for order_info in orders:
            # Sort details by detail_id to match order entry sequence
            details = step_pair_orders[step_pair][order_info]
            details.sort(key=lambda x: x["detail_id"])

            orders_data.append({"order_info": order_info, "details": details})

        # Add step pair with its orders
        step_pairs_data.append({"prev_step": prev_step, "next_step": next_step, "orders": orders_data})

    context = {"step_pairs_data": step_pairs_data}

    return render(request, "core/surplus.html", context)
