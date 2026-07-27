from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import redirect, render

from .forms import ProductForm
from .models import Product


def root_redirect_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


def custom_404_view(request, exception=None):
    return render(request, "404.html", status=404)


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    error = None
    if request.method == "POST":
        username_input = request.POST.get("username", "").strip()
        password_input = request.POST.get("password", "").strip()
        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next", "dashboard")
            return redirect(next_url if next_url else "dashboard")
        else:
            error = "Invalid username or password. Please try again."
    return render(request, "login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required(login_url="login")
def dashboard_view(request):
    products = Product.objects.all()
    total_products = products.count()
    low_stock_count = 0
    total_value = 0
    for p in products:
        if p.quantity <= p.reorder_level:
            low_stock_count += 1
        total_value += (p.quantity * p.unit_price)

    context = {
        "total_products": total_products,
        "low_stock_count": low_stock_count,
        "total_value": total_value,
        "recent_products": products[:5],
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required(login_url="login")
def products_view(request):
    products = Product.objects.all()
    return render(request, "products/products.html", {"products": products})


@login_required(login_url="login")
def inventory_view(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Product saved successfully.")
            return redirect("inventory")
    else:
        form = ProductForm()

    products = Product.objects.all()
    context = {
        "form": form,
        "products": products,
    }
    return render(request, "inventory/inventory.html", context)


@login_required(login_url="login")
def transactions_view(request):
    return render(request, "transactions/transactions.html")


@login_required(login_url="login")
def suppliers_view(request):
    return render(request, "suppliers/suppliers.html")


@login_required(login_url="login")
def reports_view(request):
    return render(request, "reports/reports.html")


@login_required(login_url="login")
def users_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("dashboard")
    return render(request, "users/users.html")


@login_required(login_url="login")
def settings_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("dashboard")
    return render(request, "settings/settings.html")
