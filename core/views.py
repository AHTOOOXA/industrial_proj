from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from core.forms import UserCreateForm, WorkerForm
from .decorators import allowed_user_roles, unauthenticated_user


# Create your views here.
@login_required(login_url='login_user')
def home(request):
    return render(request, 'core/home.html')


@login_required(login_url='login_user')
def worker_form(request):
    if request.method == 'POST':
        form = WorkerForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()
            return redirect('home')
        else:
            messages.error(request, ("Error"))
            return redirect('worker_form')
    context = {'form': WorkerForm()}
    return render(request, 'core/worker_form.html', context)


@login_required(login_url='login_user')
@allowed_user_roles(['ADMIN', 'MODERATOR'])
def table(request):
    return render(request, 'core/table.html')


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

