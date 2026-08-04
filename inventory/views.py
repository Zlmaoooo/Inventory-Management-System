from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from .forms import ProductForm
from .models import Product


@never_cache
def landing_view(request):
    """Handles the root page, which IS the login experience.

    GET  → render the landing page with the embedded login form.
    POST → authenticate the submitted credentials.

    There is no separate public login page; /login/ redirects here.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")

    error = None
    form_data = {}

    if request.method == "POST":
        username_input = request.POST.get("username", "").strip()
        password_input = request.POST.get("password", "").strip()
        user = User.objects.filter(
            models.Q(username__iexact=username_input) | models.Q(email__iexact=username_input)
        ).first()
        if user is not None:
            user = authenticate(request, username=user.username, password=password_input)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next", "dashboard")
            return redirect(next_url if next_url else "dashboard")
        else:
            error = "Invalid username or email or password. Please try again."
            form_data = {"username": username_input}

    return render(request, "landing.html", {"error": error, "form_data": form_data})


def root_redirect_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("landing")


def custom_404_view(request, exception=None):
    return render(request, "404.html", status=404)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    
    error = None
    if request.method == "POST":
        username_input = request.POST.get("username", "").strip()
        email_input = request.POST.get("email", "").strip()
        password_input = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if not username_input or not email_input or not password_input:
            error = "All fields are required."
        elif password_input != confirm_password:
            error = "Passwords do not match. Please re-enter your password."
        elif len(password_input) < 6:
            error = "Password must be at least 6 characters long."
        elif User.objects.filter(username=username_input).exists():
            error = f"Username '{username_input}' is already taken. Please choose another."
        elif User.objects.filter(email=email_input).exists():
            error = f"An account with email '{email_input}' already exists."
        else:
            user = User.objects.create_user(
                username=username_input,
                email=email_input,
                password=password_input
            )
            login(request, user)
            messages.success(request, f"Welcome to Invenza, {user.username}! Your account has been created.")
            return redirect("dashboard")

    context = {
        "error": error,
        "form_data": request.POST if request.method == "POST" else {}
    }
    return render(request, "register.html", context)


@never_cache
def login_view(request):
    """Redirects to the landing page, which now contains the login form.

    Kept so that existing links (e.g. @login_required redirects) resolve
    cleanly.  Any ?next= parameter is forwarded so the post-login redirect
    still works correctly.
    """
    next_url = request.GET.get("next", "")
    target = f"/?next={next_url}" if next_url else "/"
    return redirect(target)


def logout_view(request):
    logout(request)
    return redirect("landing")


@login_required(login_url="landing")
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


@login_required(login_url="landing")
def products_view(request):
    products = Product.objects.all()
    return render(request, "products/products.html", {"products": products})


@login_required(login_url="landing")
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


@login_required(login_url="landing")
def transactions_view(request):
    return render(request, "transactions/transactions.html")


@login_required(login_url="landing")
def suppliers_view(request):
    return render(request, "suppliers/suppliers.html")


@login_required(login_url="landing")
def reports_view(request):
    return render(request, "reports/reports.html")


@login_required(login_url="landing")
def users_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("dashboard")
    return render(request, "users/users.html")


@login_required(login_url="landing")
def settings_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("dashboard")
    return render(request, "settings/settings.html")
