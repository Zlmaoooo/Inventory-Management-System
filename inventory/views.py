from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction as db_transaction
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from .auth_utils import get_post_auth_redirect_url
from .forms import RegistrationForm, ProductEditForm, ProductForm, ShopEditForm, ShopForm, StockInForm, StockOutForm
from .models import Product, Profile, Shop, Transaction


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
        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            login(request, user)
            return redirect(get_post_auth_redirect_url(request, user, request.GET.get("next", "")))
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

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data["username"],
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        login(request, user, backend="inventory.auth_backends.UsernameOrEmailBackend")
        messages.success(request, f"Welcome to Invenza, {user.username}! Now let's set up your shop.")
        return redirect("shop_create")

    return render(request, "register.html", {"form": form})


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
        if p.current_stock <= p.reorder_level:
            low_stock_count += 1
        total_value += (p.current_stock * p.unit_price)

    context = {
        "total_products": total_products,
        "low_stock_count": low_stock_count,
        "total_value": total_value,
        "recent_products": products[:5],
    }
    return render(request, "dashboard/dashboard.html", context)


@shop_required
def products_view(request):
    """Product catalog page.

    Default view shows only active products (is_active=True) via the default
    ActiveProductManager. Passing ?archived=1 switches to the archived view
    which shows soft-deleted products so they can be inspected or restored.
    """
    shop = request.user.profile.shop
    show_archived = request.GET.get("archived") == "1"

    if show_archived:
        products = Product.all_objects.filter(shop=shop, is_active=False)
    else:
        # Default manager already filters is_active=True
        products = Product.objects.filter(shop=shop)

    archived_count = Product.all_objects.filter(shop=shop, is_active=False).count()

    context = {
        "products": products,
        "show_archived": show_archived,
        "archived_count": archived_count,
    }
    return render(request, "products/products.html", context)


@shop_required
def product_edit_view(request, pk):
    """Edit a product's metadata (name, SKU, unit_price, category, reorder_level,
    description). current_stock is NOT editable here.

    Uses all_objects so archived products can still be edited (e.g., to fix
    a typo before restoring them). Shop isolation is enforced manually.
    """
    shop = request.user.profile.shop
    try:
        product = Product.all_objects.get(pk=pk)
    except Product.DoesNotExist:
        return redirect("products")

    # Isolation check — same pattern as all other shop-scoped operations.
    if product.shop != shop:
        return redirect("products")

    form = ProductEditForm(request.POST or None, instance=product)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f"\"{product.name}\" updated successfully.")
            return redirect("products")

    context = {
        "form": form,
        "product": product,
    }
    return render(request, "products/product_edit.html", context)


@shop_required
def product_delete_view(request, pk):
    """Delete or archive a product, with a confirmation step on GET.

    Logic on POST:
      - action=restore  → set is_active=True (un-archive).
      - has transactions → set is_active=False (soft-delete / archive).
      - no transactions  → Product.delete() (hard delete).

    Uses all_objects so archived products can be restored or inspected.
    Shop isolation is enforced manually.
    """
    shop = request.user.profile.shop
    try:
        product = Product.all_objects.get(pk=pk)
    except Product.DoesNotExist:
        return redirect("products")

    # Isolation check.
    if product.shop != shop:
        return redirect("products")

    has_transactions = product.transactions.exists()

    if request.method == "POST":
        action = request.POST.get("action", "delete")

        if action == "restore":
            product.is_active = True
            product.save()
            messages.success(request, f"\"{product.name}\" has been restored to the active catalog.")
            return redirect("products")

        # Delete or archive
        if has_transactions:
            product.is_active = False
            product.save()
            messages.warning(
                request,
                f"\"{product.name}\" has been archived — it has transaction history "
                f"and cannot be permanently deleted.",
            )
        else:
            product_name = product.name
            product.delete()
            messages.success(request, f"\"{product_name}\" has been permanently deleted.")

        return redirect("products")

    # GET — render confirmation page
    context = {
        "product": product,
        "has_transactions": has_transactions,
        "transaction_count": product.transactions.count(),
    }
    return render(request, "products/product_confirm_delete.html", context)


@shop_required
def inventory_view(request):
    """Inventory management page — two separate actions on one page.

    action=add_product:
        Creates a new Product with current_stock=0. The shop is injected
        automatically from the session — never taken from form data.

    action=record_movement:
        Creates a Transaction (IN or OUT) and updates the product's
        current_stock atomically via the post_save signal.
        The whole sequence runs inside db_transaction.atomic() so that if
        anything fails partway through, neither the Transaction row nor
        the stock change is persisted.
    """
    shop = request.user.profile.shop

    # Initialise both forms (GET state)
    form_product = ProductForm()
    form_stock_in = StockInForm(shop=shop)
    form_stock_out = StockOutForm(shop=shop)
    active_form = None   # used by the template to re-open the right panel on error

    if request.method == "POST":
        action = request.POST.get("action")

        # --- Add New Product ---
        if action == "add_product":
            form_product = ProductForm(request.POST)
            if form_product.is_valid():
                product = form_product.save(commit=False)
                product.shop = shop
                # current_stock defaults to 0 — never set from POST data
                product.save()
                messages.success(request, f"Product \"{product.name}\" added. Record a Stock-In to set initial stock.")
                return redirect("inventory")
            active_form = "add_product"

        # --- Record Stock Movement ---
        elif action in ("stock_in", "stock_out"):
            txn_type = "IN" if action == "stock_in" else "OUT"
            FormClass = StockInForm if txn_type == "IN" else StockOutForm
            form = FormClass(request.POST, shop=shop)

            if txn_type == "IN":
                form_stock_in = form
            else:
                form_stock_out = form

            if form.is_valid():
                product = form.cleaned_data["product"]
                qty = form.cleaned_data["quantity"]
                notes = form.cleaned_data.get("notes", "")

                # Wrap Transaction creation + signal-triggered stock update in
                # a single atomic block — if anything fails, both roll back
                # together and no partial state is persisted.
                with db_transaction.atomic():
                    Transaction.objects.create(
                        product=product,
                        shop=shop,
                        type=txn_type,
                        quantity=qty,
                        notes=notes,
                        created_by=request.user,
                    )
                    # The post_save signal fires inside this atomic block and
                    # updates Product.current_stock with F() — also rolled back
                    # if an exception occurs after this point.

                direction = "added to" if txn_type == "IN" else "removed from"
                messages.success(request, f"{qty} unit(s) {direction} \"{product.name}\" stock.")
                return redirect("inventory")

            active_form = action

    products = Product.objects.filter(shop=shop)
    context = {
        "form_product": form_product,
        "form_stock_in": form_stock_in,
        "form_stock_out": form_stock_out,
        "active_form": active_form,
        "products": products,
    }
    return render(request, "inventory/inventory.html", context)


@shop_required
def transactions_view(request):
    """Shop-scoped transaction history, optionally filtered by product.

    GET ?product=<id> filters the table to a single product. The product
    dropdown in the filter bar is also shop-scoped so users cannot enumerate
    other shops' products via the query string.
    """
    shop = request.user.profile.shop

    # Only expose products belonging to this shop in the filter dropdown
    products = Product.objects.filter(shop=shop)

    # Parse optional product filter from GET params
    selected_product_id = request.GET.get("product", "")
    transactions = Transaction.objects.filter(shop=shop).select_related(
        "product", "created_by"
    )
    if selected_product_id:
        # Validate the product belongs to this shop before filtering —
        # prevents using the query param to probe another shop's transactions.
        if products.filter(pk=selected_product_id).exists():
            transactions = transactions.filter(product_id=selected_product_id)
        else:
            selected_product_id = ""  # reset invalid/cross-shop param

    context = {
        "transactions": transactions,
        "products": products,
        "selected_product_id": selected_product_id,
    }
    return render(request, "transactions/transactions.html", context)


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
