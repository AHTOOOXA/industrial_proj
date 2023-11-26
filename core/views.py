from django.shortcuts import render, redirect
from core.forms import UserCreateForm


# Create your views here.
def register(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('register')
    context = {'form': UserCreateForm()}
    return render(request, 'core/register.html', context)
