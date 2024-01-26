import datetime
import itertools

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import F, Count
from django.db.models.functions import Trunc
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.context_processors import csrf
from crispy_forms.utils import render_crispy_form
from django.utils.timezone import now
from django.views.generic import ListView
from django_tables2 import SingleTableView, RequestConfig

from .models import ReportEntry, Report, OrderEntry, Order, Machine
from core.forms import UserCreateForm, UserCreateAdminForm, ReportForm, ReportEntryForm, ReportEntryFormset, OrderForm, \
    OrderEntryForm, OrderEntryFormset, NewReportForm
from .decorators import allowed_user_roles, unauthenticated_user
from .tables import ReportEntryTable, ReportTable, MyTable


@login_required(login_url='login_user')
def home(request):
    return render(request, 'core/home.html')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def stats(request):
    orders = Order.objects.all().order_by('-id')
    machines = Machine.objects.all()

    table = []
    timestamps = [datetime.date.today() - datetime.timedelta(days=1) + datetime.timedelta(days=i) for i in range(0, 6)]
    for i in range(len(timestamps) - 1):
        row_objs = ReportEntry.objects.filter(
            report__date__range=(timestamps[i], timestamps[i + 1]))
        row = [timestamps[i]]
        for machine in machines:
            obj = row_objs.filter(machine=machine)
            if obj:
                # row.append(obj)
                row.append(str(obj[0].detail) + '\n' + str(obj[0].quantity))
            else:
                row.append('')
        table.append(row)
    context = {
        'orders': orders,
        'machines': machines,
        'table': table
    }
    return render(request, 'core/stats.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def orders_add(request):
    if request.method == "GET":
        form = OrderForm()
        formset = OrderEntryFormset()
        context = {
            'form': form,
            'formset': formset,
        }
        return render(request, 'core/order_add.html', context)
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            report_instance = form.save(commit=False)
            report_instance.save()

            entry_formset = OrderEntryFormset(request.POST, request.FILES, instance=report_instance)
            if entry_formset.is_valid():
                for entry_form in entry_formset:
                    entry_form.save()
        return redirect('stats')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def orders_edit(request, pk):
    return redirect('stats')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def add_order_entry_form(request):
    if request.method == 'GET':
        new_formset = OrderEntryFormset()
        form_number = int(request.GET.get("totalForms"))
        new_form = new_formset.empty_form
        new_form.prefix = new_form.prefix.replace("__prefix__", str(form_number))
        context = {
            'new_form': new_form,
            'new_total_forms_count': form_number + 1,
        }
        return render(request, 'core/partials/order_entry_form.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def orders_delete(request, pk):
    Order.objects.get(pk=pk).delete()
    orders = Order.objects.all().order_by('-id')
    context = {
        'orders': orders,
    }
    return render(request, 'core/partials/orders_list.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def order_entries_delete(request, r_pk, re_pk):
    OrderEntry.objects.get(pk=re_pk).delete()
    order = Order.objects.get(pk=r_pk)
    context = {
        'order': order,
    }
    return render(request, 'core/partials/order_entries_list.html', context)


@unauthenticated_user
def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, ("There Was An Error Logging In, Try Again..."))
            return redirect('login_user')
    else:
        return render(request, 'core/login.html', {})


def logout_user(request):
    logout(request)
    messages.success(request, ("You Were Logged Out!"))
    return redirect('home')


def register_user(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ("Registration Successful!"))
            return redirect('home')
        else:
            messages.error(request, ("Error"))
            return redirect('register_user')
    else:
        form = UserCreateForm()
        return render(request, 'core/register.html', {
            'form': form,
        })


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def register_user_admin(request):
    if request.method == "GET":
        context = {'form': UserCreateAdminForm()}
        return render(request, 'core/register_employee.html', context)
    if request.method == "POST":
        form = UserCreateAdminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, (f'Пользователь успешно зарегистрирован'))
            # new_form = UserCreateAdminForm()
            # ctx = {}
            # ctx.update(csrf(request))
            # form_html = render_crispy_form(new_form, context=ctx)
            response = HttpResponse()
            response['HX-Redirect'] = request.build_absolute_uri('register_user_admin')
            return response
        ctx = {}
        ctx.update(csrf(request))
        form_html = render_crispy_form(form, context=ctx)
        return HttpResponse(form_html)


@login_required(login_url='login_user')
def report_form(request):
    if request.method == "GET":
        form = ReportForm(initial={'user': request.user, 'date': now()})
        form.fields['user'].disabled = True
        form.fields['date'].disabled = True
        formset = ReportEntryFormset()
        context = {
            'form': form,
            'formset': formset,
        }
        return render(request, 'core/report_form.html', context)
    if request.method == "POST":
        # these weird copying required to process disabled fields
        POST = request.POST.copy()
        POST['user'] = request.user
        POST['date'] = now()
        form = ReportForm(POST)
        if form.is_valid():
            report_instance = form.save(commit=False)
            report_instance.save()

            entry_formset = ReportEntryFormset(request.POST, request.FILES, instance=report_instance)
            if entry_formset.is_valid():
                for entry_form in entry_formset:
                    entry_form.save()
        return redirect('report_form')


@login_required(login_url='login_user')
def add_report_entry_form(request):
    if request.method == 'GET':
        new_formset = ReportEntryFormset()
        form_number = int(request.GET.get("totalForms"))
        new_form = new_formset.empty_form
        new_form.prefix = new_form.prefix.replace("__prefix__", str(form_number))
        context = {
            'new_form': new_form,
            'new_total_forms_count': form_number + 1,
        }
        return render(request, 'core/partials/report_entry_form.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def reports_view(request):
    reports = Report.objects.all().order_by('-date')
    context = {
        'reports': reports,
    }
    return render(request, 'core/reports.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def reports_add(request):
    if request.method == "GET":
        form = ReportForm()
        formset = ReportEntryFormset()
        context = {
            'form': form,
            'formset': formset,
        }
        return render(request, 'core/report_form.html', context)
    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report_instance = form.save(commit=False)
            report_instance.save()

            entry_formset = ReportEntryFormset(request.POST, request.FILES, instance=report_instance)
            if entry_formset.is_valid():
                for entry_form in entry_formset:
                    entry_form.save()
        return redirect('reports_view')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def reports_edit(request, pk):
    report = Report.objects.get(pk=pk)
    if request.method == 'GET':
        form = ReportForm(instance=report)
        # formset = ReportEntryFormset(queryset=report.reportentry_set.all())
        formset = ReportEntryFormset(instance=report)
        context = {
            'report': report,
            'form': form,
            'formset': formset,
        }
        return render(request, 'core/reports_edit.html', context)
    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)
        print(form.is_valid())
        if form.is_valid():
            report_instance = form.save(commit=False)
            report_instance.save()

            entry_formset = ReportEntryFormset(request.POST, request.FILES, instance=report_instance)
            print(entry_formset.is_valid())
            print(entry_formset.errors)
            if entry_formset.is_valid():
                for entry_form in entry_formset:
                    entry_form.save()
        return redirect('reports_view')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def reports_delete(request, pk):
    Report.objects.get(pk=pk).delete()
    reports = Report.objects.all()
    context = {
        'reports': reports,
    }
    return render(request, 'core/partials/reports_list.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def report_entries_delete(request, r_pk, re_pk):
    ReportEntry.objects.get(pk=re_pk).delete()
    report = Report.objects.get(pk=r_pk)
    context = {
        'report': report,
    }
    return render(request, 'core/partials/report_entries_list.html', context)
