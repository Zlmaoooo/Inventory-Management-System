from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from .forms import ProductForm, ShopEditForm, ShopForm
from .models import Product, Profile, Shop


# ---------------------------------------------------------------------------
# Decorator: shop_required
# ---------------------------------------------------------------------------

def shop_required(view_func):
    """Guards authenticated-only views that also require a completed Shop/Profile.

    If the user is not authenticated → redirect to the landing/login page.
    If the user has no Profile, or has a Profile with shop=None → redirect to
    the shop-creation flow so they complete onboarding before proceeding.

    Applied to all protected views except shop_create_view (which must only
    use @login_required to avoid a redirect loop).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("landing")
        try:
            profile = request.user.profile
            if profile.shop is None:
                return redirect("shop_create")
        except Profile.DoesNotExist:
            return redirect("shop_create")
        return view_func(request, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Public / Auth views
# ---------------------------------------------------------------------------

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
            messages.success(request, f"Welcome to Invenza, {user.username}! Now let's set up your shop.")
            # Redirect to shop onboarding — NOT dashboard (profile/shop not set up yet)
            return redirect("shop_create")

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


# ---------------------------------------------------------------------------
# Shop onboarding
# ---------------------------------------------------------------------------

@login_required(login_url="landing")
def shop_create_view(request):
    """Step 2 of registration: create the user's Shop and link their Profile.

    Must NOT use @shop_required — that would cause an infinite redirect loop
    for users who have no shop yet (which is exactly who this view serves).
    """
    # If the user already has a profile with a shop, send them to the dashboard
    try:
        profile = request.user.profile
        if profile.shop is not None:
            return redirect("dashboard")
    except Profile.DoesNotExist:
        pass

    form = ShopForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            shop = form.save()
            # Use update_or_create to safely handle any pre-existing Profile row
            Profile.objects.update_or_create(
                user=request.user,
                defaults={"shop": shop, "role": "owner"},
            )
            messages.success(request, f"Your shop \"{shop.name}\" has been created. Welcome to your dashboard!")
            return redirect("dashboard")

    return render(request, "shop_onboarding.html", {"form": form})


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@shop_required
def profile_view(request):
    """Displays the logged-in user's profile and their shop details."""
    profile = request.user.profile
    return render(request, "profile/profile.html", {"profile": profile})


@shop_required
def profile_edit_view(request):
    """Allows the user to update their shop's details."""
    profile = request.user.profile
    shop = profile.shop
    form = ShopEditForm(request.POST or None, instance=shop)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Shop details updated successfully.")
            return redirect("profile")

    return render(request, "profile/profile_edit.html", {"form": form, "shop": shop})


# ---------------------------------------------------------------------------
# App views (protected by @shop_required)
# ---------------------------------------------------------------------------

@shop_required
def dashboard_view(request):
    # Only show products that belong to the logged-in user's own shop.
    shop = request.user.profile.shop
    products = Product.objects.filter(shop=shop)
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


@shop_required
def products_view(request):
    # Only show products that belong to the logged-in user's own shop.
    shop = request.user.profile.shop
    products = Product.objects.filter(shop=shop)
    return render(request, "products/products.html", {"products": products})


@shop_required
def inventory_view(request):
    # All product operations are scoped to the logged-in user's shop.
    shop = request.user.profile.shop

    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            # Inject the shop before writing to the DB — the user never sees
            # or selects a shop field; it's set automatically from their session.
            product = form.save(commit=False)
            product.shop = shop
            product.save()
            messages.success(request, "Product saved successfully.")
            return redirect("inventory")
    else:
        form = ProductForm()

    # Only list products belonging to this shop.
    products = Product.objects.filter(shop=shop)
    context = {
        "form": form,
        "products": products,
    }
    return render(request, "inventory/inventory.html", context)


@shop_required
def transactions_view(request):
    return render(request, "transactions/transactions.html")


@shop_required
def suppliers_view(request):
    return render(request, "suppliers/suppliers.html")


@shop_required
def reports_view(request):
    return render(request, "reports/reports.html")


@shop_required
def users_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("dashboard")
    return render(request, "users/users.html")


@shop_required
def settings_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("dashboard")
    return render(request, "settings/settings.html")
