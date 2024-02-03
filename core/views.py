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

from .models import ReportEntry, Report, OrderEntry, Order, Machine, Table, Detail, User
from core.forms import UserCreateForm, UserCreateAdminForm, ReportForm, ReportEntryForm, ReportEntryFormset, OrderForm, \
    OrderEntryForm, OrderEntryFormset, DetailForm, MachineForm
from .decorators import allowed_user_roles, unauthenticated_user
from .scripts import get_shifts_table


@login_required(login_url='login_user')
def home(request):
    return render(request, 'core/home.html')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def stats(request):
    orders = Order.objects.all().order_by('-id')
    order_entries_leftovers = {}
    for order_entry in OrderEntry.objects.all():
        order_entries_leftovers[order_entry.id] = order_entry.quantity
        for report_entry in ReportEntry.objects.filter(report__order=order_entry.order):
            order_entries_leftovers[order_entry.id] -= report_entry.quantity
    machines = Machine.objects.all()
    table = get_shifts_table()
    context = {
        'orders': orders,
        'order_entries_leftovers': order_entries_leftovers,
        'machines': machines,
        'table': table
    }
    return render(request, 'core/stats.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def shift_table(request, value):
    current_date = Table.objects.all()[0].current_date
    new_date = current_date + int(value) * datetime.timedelta(hours=12)
    Table.objects.all().update(current_date=new_date)
    table = get_shifts_table(new_date)
    machines = Machine.objects.all()
    context = {
        'machines': machines,
        'table': table
    }
    return render(request, 'core/partials/table.html', context)


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
    order = Order.objects.get(pk=pk)
    if request.method == 'GET':
        form = OrderForm(instance=order)
        formset = OrderEntryFormset(instance=order)
        context = {
            'order': order,
            'form': form,
            'formset': formset,
        }
        return render(request, 'core/orders_edit.html', context)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        print(form.is_valid())
        if form.is_valid():
            order_instance = form.save(commit=False)
            order_instance.save()

            entry_formset = OrderEntryFormset(request.POST, request.FILES, instance=order_instance)
            print(entry_formset.is_valid())
            print(entry_formset.errors)
            if entry_formset.is_valid():
                for entry_form in entry_formset:
                    if entry_form.cleaned_data['DELETE'] is not True:
                        entry_form.save()
                    else:
                        print(entry_form.cleaned_data)
                        if entry_form.cleaned_data['id'] is not None:
                            entry_form.cleaned_data['id'].delete()
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
                    if entry_form.cleaned_data['DELETE'] is not True:
                        entry_form.save()
            messages.success(request, 'Отчет успешно отправлен!')
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
                    if entry_form.cleaned_data['DELETE'] is not True:
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
                    if entry_form.cleaned_data['DELETE'] is not True:
                        entry_form.save()
                    else:
                        print(entry_form.cleaned_data)
                        if entry_form.cleaned_data['id'] is not None:
                            entry_form.cleaned_data['id'].delete()
                            # entry = ReportEntry.objects.get(entry_form.cleaned_data['id']).delete()
        return redirect('reports_view')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def reports_delete(request, pk):
    Report.objects.get(pk=pk).delete()
    reports = Report.objects.all().order_by('-id')
    context = {
        'reports': reports,
    }
    return render(request, 'core/partials/reports_list.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def details_view(request):
    details = Detail.objects.all().order_by('-id')
    context = {
        'details': details,
    }
    return render(request, 'core/details.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def details_add(request):
    if request.method == "GET":
        form = DetailForm()
        context = {
            'form': form,
        }
        return render(request, 'core/detail_form.html', context)
    if request.method == "POST":
        form = DetailForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Деталь успешно добавлена')
        return redirect('details_view')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def details_edit(request, pk):
    detail = Detail.objects.get(pk=pk)
    if request.method == 'GET':
        form = DetailForm(instance=detail)
        context = {
            'detail': detail,
            'form': form,
        }
        return render(request, 'core/details_edit.html', context)
    if request.method == 'POST':
        form = DetailForm(request.POST, instance=detail)
        if form.is_valid():
            form.save()
            messages.success(request, f'Деталь успешно изменена')
        return redirect('details_view')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def details_delete(request, pk):
    Detail.objects.get(pk=pk).delete()
    details = Detail.objects.all().order_by('-id')
    context = {
        'details': details,
    }
    return render(request, 'core/partials/details_list.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def machines_view(request):
    machines = Machine.objects.all().order_by('-id')
    context = {
        'machines': machines,
    }
    return render(request, 'core/machines.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def machines_add(request):
    if request.method == "GET":
        form = MachineForm()
        context = {
            'form': form,
        }
        return render(request, 'core/machine_form.html', context)
    if request.method == "POST":
        form = MachineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Станок успешно добавлен')
        return redirect('machines_view')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def machines_edit(request, pk):
    machine = Machine.objects.get(pk=pk)
    if request.method == 'GET':
        form = MachineForm(instance=machine)
        context = {
            'machine': machine,
            'form': form,
        }
        return render(request, 'core/machines_edit.html', context)
    if request.method == 'POST':
        form = MachineForm(request.POST, instance=machine)
        if form.is_valid():
            form.save()
            messages.success(request, f'Станок успешно изменен')
        return redirect('machines_view')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def machines_delete(request, pk):
    Machine.objects.get(pk=pk).delete()
    machines = Machine.objects.all().order_by('-id')
    context = {
        'machines': machines,
    }
    return render(request, 'core/partials/machines_list.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def users_view(request):
    users = User.objects.all().order_by('-id')
    context = {
        'users': users,
    }
    return render(request, 'core/users.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def users_add(request):
    if request.method == "GET":
        context = {
            'form': UserCreateAdminForm()
        }
        return render(request, 'core/user_form.html', context)
    if request.method == "POST":
        form = UserCreateAdminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Сотрудник успешно зарегистрирован')
        return redirect('users_view')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def users_edit(request, pk):
    user = User.objects.get(pk=pk)
    if request.method == 'GET':
        form = UserCreateAdminForm(instance=user)
        context = {
            'user': user,
            'form': form,
        }
        return render(request, 'core/users_edit.html', context)
    if request.method == 'POST':
        form = UserCreateAdminForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Станок успешно изменен')
        return redirect('users_view')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def users_delete(request, pk):
    User.objects.get(pk=pk).delete()
    users = User.objects.all().order_by('-id')
    context = {
        'users': users,
    }
    return render(request, 'core/partials/users_list.html', context)


def test(request):
    table = []
    timestamps = [datetime.date.today() - datetime.timedelta(days=1) + datetime.timedelta(days=i) for i in range(0, 6)]

    machines = Machine.objects.all()
    for i in range(len(timestamps) - 1):
        row_objs = ReportEntry.objects.filter(
            report__date__range=(timestamps[i], timestamps[i + 1]))
        row = [timestamps[i]]
        for machine in machines:
            obj = row_objs.filter(machine=machine)
            if obj:
                # row.append(obj)
                row.append(str(obj[0].detail) + ':\n' + str(obj[0].quantity))
            else:
                row.append('empty')
        table.append(row)

    # my_table = MyTable(table)

    # # Use RequestConfig to configure the table
    # RequestConfig(request).configure(my_table)
    #
    # return render(request, 'test.html', context={'my_table': my_table})

    s = '\n'.join(['    '.join(str(row)) for row in table])
    print(s)
    return render(request, 'test.html', context={'table': table, 'machines': machines})
