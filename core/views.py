import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.timezone import now, make_naive

from .models import ReportEntry, Report, OrderEntry, Order, Machine, Table, Detail, User, Plan, Step
from core.forms import UserCreateAdminForm, ReportForm, ReportEntryFormset, OrderForm, \
    OrderEntryFormset, DetailForm, MachineForm, PlanForm, PlanEntryFormset
from .decorators import allowed_user_roles, unauthenticated_user
from .scripts import get_shifts_table, get_leftovers, get_reports_view


@login_required(login_url='login_user')
def home(request):
    return render(request, 'core/home.html')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def stats(request):
    leftovers = get_leftovers()

    orders = Order.objects.all().order_by('-id')
    order_entries_leftovers = {}
    for order_entry in OrderEntry.objects.all():
        order_entries_leftovers[order_entry.id] = order_entry.quantity
        for report_entry in ReportEntry.objects.filter(report__order=order_entry.order):
            order_entries_leftovers[order_entry.id] -= report_entry.quantity

    current_date = Table.objects.all()[0].current_date
    today = now()
    today = today - datetime.timedelta(days=1)
    today = today.replace(hour=current_date.hour % 12, minute=current_date.minute,
                          second=current_date.second, microsecond=current_date.microsecond)
    Table.objects.all().update(current_date=today)
    active_step_pk, machines, table = get_shifts_table()
    context = {
        'orders': orders,
        'leftovers': leftovers,
        'order_entries_leftovers': order_entries_leftovers,
        'steps': Step.objects.all(),
        'active_step_pk': active_step_pk,
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

    _, machines, table = get_shifts_table()
    context = {
        'machines': machines,
        'table': table
    }
    return render(request, 'core/partials/table.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def switch_step(request, step):
    Table.objects.all().update(current_step=step)

    active_step_pk, machines, table = get_shifts_table()
    context = {
        'steps': Step.objects.all(),
        'active_step_pk': active_step_pk,
        'machines': machines,
        'table': table
    }
    return render(request, 'core/partials/right_col.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def orders_add(request):
    if request.method == "GET":
        form = OrderForm(initial={'date': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")})
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
        form = OrderForm(instance=order, initial={'date': make_naive(order.date).strftime("%Y-%m-%dT%H:%M")})
        formset = OrderEntryFormset(instance=order)
        context = {
            'order': order,
            'form': form,
            'formset': formset,
        }
        return render(request, 'core/orders_edit.html', context)
    if request.method == 'POST':
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
                    if entry_form.cleaned_data['DELETE'] is not True:
                        entry_form.save()
                    else:
                        # print(entry_form.cleaned_data)
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
    return HttpResponse('')


@unauthenticated_user
def login_user(request):
    if request.method == 'GET':
        return render(request, 'core/login.html', {})
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'WORKER':
                return redirect('report_form')
            else:
                return redirect('stats')
        else:
            messages.error(request, "Ошибка при входе, попробуйте еще раз")
            return redirect('login_user')


def logout_user(request):
    logout(request)
    messages.success(request, ("Вы вышли из системы"))
    return redirect('home')


@login_required(login_url='login_user')
def report_form(request):
    if request.method == "GET":
        # form = ReportForm(initial={'user': request.user, 'date': now()})
        form = ReportForm(initial={'user': request.user, 'date': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")})
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
            logout(request)
            return redirect('login_user')
        return redirect('report_form')


@login_required(login_url='login_user')
def report_confirmation(request):
    POST = request.POST.copy()
    if 'user' not in POST:
        POST['user'] = request.user
    if 'date' not in POST:
        POST['date'] = now()
    if request.method == "POST":
        form = ReportForm(POST)
        if form.is_valid():
            report_instance = form.save(commit=False)
            entry_formset = ReportEntryFormset(POST, request.FILES, instance=report_instance)
            if entry_formset.is_valid():
                report_entries = []
                for entry_form in entry_formset:
                    if entry_form.cleaned_data['DELETE'] is not True:
                        entry = entry_form.save(commit=False)
                        report_entries.append(entry)
                context = {
                    'report': report_instance,
                    'report_entries': report_entries,
                }
                return render(request, 'core/partials/report_confirmation.html', context)
            else:
                context = {
                    'errors': entry_formset.errors,
                }
                return render(request, 'core/partials/report_confirmation_error.html', context)
        else:
            context = {
                'errors': form.errors,
            }
            return render(request, 'core/partials/report_confirmation_error.html', context)


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
def detail_options(request):
    order = request.GET.get('order')
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
        entries = Detail.objects.all().order_by('name')
    cur_value = next(request.GET.values())
    if cur_value != '':
        cur_value = int(cur_value)
    context = {
        'details': details,
        'cur_value': cur_value,
    }
    return render(request, 'core/partials/detail_options.html', context)


@login_required(login_url='login_user')
def machine_options(request):
    step = request.GET.get('step')
    if step:
        machines = Machine.objects.filter(step__pk=step).all()
    else:
        machines = Machine.objects.all()
    cur_value = next(request.GET.values())
    if cur_value != '':
        cur_value = int(cur_value)
    context = {
        'machines': machines,
        'cur_value': cur_value,
    }
    return render(request, 'core/partials/machines_options.html', context)


def report_success(request, pk):
    report = Report.objects.get(pk=pk)
    context = {
        'report': report,
    }
    return render(request, 'core/report_success.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def reports_view(request):
    steps, shift_reports_lists = get_reports_view()
    context = {
        'steps': steps,
        'shift_reports_lists': shift_reports_lists,
    }
    return render(request, 'core/reports.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def reports_add(request):
    if request.method == "GET":
        form = ReportForm(initial={'date': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")})
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
                messages.success(request, 'Отчет успешно отправлен!')
        return redirect('reports_view')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def reports_edit(request, pk):
    report = Report.objects.get(pk=pk)
    if request.method == 'GET':
        form = ReportForm(instance=report, initial={'date': make_naive(report.date).strftime("%Y-%m-%dT%H:%M")})
        formset = ReportEntryFormset(instance=report)
        context = {
            'report': report,
            'form': form,
            'formset': formset,
        }
        return render(request, 'core/reports_edit.html', context)
    if request.method == 'POST':
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
                    if entry_form.cleaned_data['DELETE'] is not True:
                        entry_form.save()
                    else:
                        # print(entry_form.cleaned_data)
                        if entry_form.cleaned_data['id'] is not None:
                            entry_form.cleaned_data['id'].delete()
                messages.success(request, 'Отчет успешно изменен!')
        return redirect('reports_view')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def reports_delete(request, pk):
    Report.objects.get(pk=pk).delete()
    return HttpResponse('')


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
    return HttpResponse('')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def machines_view(request):
    steps = Step.objects.all()
    steps_machines = {}
    for step in steps:
        step_machines = Machine.objects.filter(step=step).order_by('-id')
        steps_machines[step.id] = step_machines
    context = {
        'steps': steps,
        'steps_machines': steps_machines,
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
    return HttpResponse('')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def users_view(request):
    users = User.objects.all().order_by('username')
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
        else:
            print(form)
            print(form.errors)
            messages.error(request, f'Ошибка')
            return redirect('users_add')


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
    return HttpResponse('')


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def report_modal(request):
    pk = int(str(request.GET.get("pk")))
    report = ReportEntry.objects.get(pk=pk).report
    context = {
        'report': report
    }
    return render(request, 'core/partials/report_modal.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def add_plan_entry_form(request):
    if request.method == 'GET':
        new_formset = PlanEntryFormset()
        form_number = int(request.GET.get("totalForms"))
        new_form = new_formset.empty_form
        new_form.prefix = new_form.prefix.replace("__prefix__", str(form_number))
        context = {
            'new_form': new_form,
            'new_total_forms_count': form_number + 1,
        }
        return render(request, 'core/partials/plan_entry_form.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def plan_modal(request):
    if request.method == 'GET':
        pk = int(str(request.GET.get("pk")))
        plan = Plan.objects.get(pk=pk)
        form = PlanForm(instance=plan)
        formset = PlanEntryFormset(instance=plan)
        context = {
            'plan': plan,
            'form': form,
            'formset': formset,
        }
        return render(request, 'core/partials/plan_modal.html', context)
    if request.method == 'POST':
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
                    if entry_form.cleaned_data['DELETE'] is not True:
                        entry_form.save()
                    else:
                        # print(entry_form.cleaned_data)
                        if entry_form.cleaned_data['id'] is not None:
                            entry_form.cleaned_data['id'].delete()
        return HttpResponse('', headers={'HX-Refresh': 'true'})
