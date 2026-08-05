from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Product, Profile, Shop, Transaction


# ---------------------------------------------------------------------------
# Helper: build a fully-onboarded user (User + Shop + Profile) in one call.
# ---------------------------------------------------------------------------

def _make_shop_user(username, shop_name, password="password123"):
    """Create a User, a Shop, and a Profile linking them — the full onboarding
    state that @shop_required expects before granting access."""
    user = User.objects.create_user(username=username, password=password)
    shop = Shop.objects.create(
        name=shop_name,
        shop_type="Grocery",
        location="Test Location",
        contact_number="0000000000",
    )
    Profile.objects.create(user=user, shop=shop, role="owner")
    return user, shop


def _make_product(shop, name="Test Product", sku="TEST-001"):
    """Create a Product belonging to the given shop with current_stock=0."""
    return Product.objects.create(
        shop=shop,
        name=name,
        sku=sku,
        unit_price="10.00",
        category="Test",
        reorder_level=5,
    )


class RegistrationAndLandingViewsTests(TestCase):
    def test_landing_page_renders_for_unauthenticated_user(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        # Headline updated when landing page was redesigned (commit c8d3480)
        self.assertContains(response, "Inventory")
        self.assertContains(response, "under control")

    def test_landing_login_accepts_username_or_email(self):
        """After login, a user without a Shop is redirected to shop_create.
        A user WITH a Shop (created here) lands on dashboard.
        We use follow=True so assertRedirects can chase the full chain."""
        user, shop = _make_shop_user("emailuser", "Email User Shop")
        user.email = "emailuser@example.com"
        user.save()

        # Login by username
        username_response = self.client.post(
            reverse("landing"),
            {"username": user.username, "password": "password123"},
            follow=True,
        )
        self.assertRedirects(username_response, reverse("dashboard"))

        self.client.logout()

        # Login by email
        email_response = self.client.post(
            reverse("landing"),
            {"username": user.email, "password": "password123"},
            follow=True,
        )
        self.assertRedirects(email_response, reverse("dashboard"))

    def test_successful_user_registration(self):
        """Registration sends the new user to shop_create (onboarding step 2),
        not directly to dashboard — by design since commit 960ee74."""
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
        )
        # After registration, redirect goes to shop onboarding (not dashboard)
        self.assertRedirects(response, reverse("shop_create"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_registration_password_mismatch_shows_error(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "mismatchuser",
                "email": "mismatch@example.com",
                "password": "password123",
                "confirm_password": "differentpassword",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match")
        self.assertFalse(User.objects.filter(username="mismatchuser").exists())


class InventoryAndProductsViewsTests(TestCase):
    def setUp(self):
        # Both users now get a proper Shop + Profile so @shop_required passes.
        self.user, self.shop = _make_shop_user("testuser", "Test Shop A")
        self.staff_user, self.staff_shop = _make_shop_user("adminuser", "Admin Shop")
        self.staff_user.is_staff = True
        self.staff_user.is_superuser = True
        self.staff_user.save()

    def test_unauthenticated_user_redirected_to_login(self):
        protected_urls = [
            reverse("dashboard"),
            reverse("products"),
            reverse("inventory"),
            reverse("transactions"),
            reverse("suppliers"),
            reverse("reports"),
            reverse("users"),
            reverse("settings"),
        ]
        for url in protected_urls:
            response = self.client.get(url)
            # @shop_required redirects unauthenticated users to the landing
            # page ('/'), not to '/login/?next=...'.
            self.assertRedirects(response, reverse("landing"))

    def test_inventory_page_shows_form_and_saved_products(self):
        self.client.login(username="testuser", password="password123")
        # Products now start at current_stock=0 (no quantity field on creation).
        product = _make_product(self.shop, name="Rice", sku="RICE-001")

        response = self.client.get(reverse("inventory"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add New Product")
        self.assertContains(response, "Saved Inventory Items")
        self.assertContains(response, "RICE-001")

    def test_products_page_shows_catalog(self):
        self.client.login(username="testuser", password="password123")
        _make_product(self.shop, name="Beans", sku="BEAN-001")

        response = self.client.get(reverse("products"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product Catalog")
        self.assertContains(response, "BEAN-001")

    def test_saving_product_on_inventory_shows_up_in_products_catalog(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("inventory"),
            {
                "action": "add_product",
                "name": "Sugar",
                "sku": "SUG-001",
                "unit_price": "18.00",
                "category": "Groceries",
                "reorder_level": 2,
                "description": "Test product",
            },
        )

        self.assertRedirects(response, reverse("inventory"))
        self.assertTrue(Product.objects.filter(sku="SUG-001").exists())
        # New product must start at current_stock=0
        self.assertEqual(Product.objects.get(sku="SUG-001").current_stock, 0)

        products_response = self.client.get(reverse("products"))
        self.assertContains(products_response, "SUG-001")

    def test_role_based_access_to_admin_views(self):
        self.client.login(username="testuser", password="password123")
        users_resp = self.client.get(reverse("users"))
        self.assertRedirects(users_resp, reverse("dashboard"))

        settings_resp = self.client.get(reverse("settings"))
        self.assertRedirects(settings_resp, reverse("dashboard"))

        self.client.login(username="adminuser", password="password123")
        users_resp_admin = self.client.get(reverse("users"))
        self.assertEqual(users_resp_admin.status_code, 200)

        settings_resp_admin = self.client.get(reverse("settings"))
        self.assertEqual(settings_resp_admin.status_code, 200)


# ---------------------------------------------------------------------------
# Security test: cross-shop product isolation
# ---------------------------------------------------------------------------

class ProductShopIsolationTests(TestCase):
    """Verify that a product created by Shop A is NEVER visible to Shop B.

    This is the primary data-isolation regression test. It covers every
    surface that renders product data: the dashboard count, the products
    catalog page, and the inventory list page.
    """

    def setUp(self):
        self.user_a, self.shop_a = _make_shop_user("shop_a_owner", "Alpha Mart")
        self.user_b, self.shop_b = _make_shop_user("shop_b_owner", "Beta Bazaar")

    def test_product_not_visible_to_other_shop_user(self):
        # --- Step 1: Log in as User A and add a product via the inventory view. ---
        self.client.login(username="shop_a_owner", password="password123")
        post_resp = self.client.post(
            reverse("inventory"),
            {
                "action": "add_product",
                "name": "AlphaWidget",
                "sku": "AW-001",
                "unit_price": "9.99",
                "category": "Widgets",
                "reorder_level": 10,
                "description": "Belongs to Shop A only.",
            },
        )
        self.assertRedirects(post_resp, reverse("inventory"))

        # Confirm the product was saved AND linked to Shop A.
        product = Product.objects.get(sku="AW-001")
        self.assertEqual(product.shop, self.shop_a,
                         "Product must be linked to Shop A after creation.")

        # --- Step 2: Log out User A and log in as User B. ---
        self.client.logout()
        self.client.login(username="shop_b_owner", password="password123")

        # --- Step 3: Dashboard — total_products must be 0 for Shop B. ---
        dashboard_resp = self.client.get(reverse("dashboard"))
        self.assertEqual(dashboard_resp.status_code, 200)
        self.assertEqual(
            dashboard_resp.context["total_products"], 0,
            "Dashboard must show 0 products for Shop B (data isolation failure).",
        )

        # --- Step 4: Products catalog — AW-001 must NOT appear. ---
        products_resp = self.client.get(reverse("products"))
        self.assertEqual(products_resp.status_code, 200)
        self.assertNotContains(
            products_resp, "AW-001",
            msg_prefix="Shop B's product catalog must not contain Shop A's SKU.",
        )
        self.assertNotContains(
            products_resp, "AlphaWidget",
            msg_prefix="Shop B's product catalog must not contain Shop A's product name.",
        )

        # --- Step 5: Inventory list — AW-001 must NOT appear. ---
        inventory_resp = self.client.get(reverse("inventory"))
        self.assertEqual(inventory_resp.status_code, 200)
        self.assertNotContains(
            inventory_resp, "AW-001",
            msg_prefix="Shop B's inventory page must not contain Shop A's SKU.",
        )
        self.assertNotContains(
            inventory_resp, "AlphaWidget",
            msg_prefix="Shop B's inventory page must not contain Shop A's product name.",
        )


# ---------------------------------------------------------------------------
# Transaction system tests
# ---------------------------------------------------------------------------

class TransactionSystemTests(TestCase):
    """Tests for the full stock-transaction lifecycle.

    Covers: stock-IN increases current_stock, stock-OUT decreases it,
    negative-stock validation, cross-shop transaction isolation, and the
    invariant that ProductForm does not accept a quantity field.
    """

    def setUp(self):
        self.user, self.shop = _make_shop_user("txn_user", "Txn Shop")
        self.product = _make_product(self.shop, name="Widget", sku="WGT-001")
        self.client.login(username="txn_user", password="password123")

    def _post_stock_in(self, product, qty, notes=""):
        return self.client.post(reverse("inventory"), {
            "action": "stock_in",
            "product": product.pk,
            "quantity": qty,
            "notes": notes,
        })

    def _post_stock_out(self, product, qty, notes=""):
        return self.client.post(reverse("inventory"), {
            "action": "stock_out",
            "product": product.pk,
            "quantity": qty,
            "notes": notes,
        })

    def test_stock_in_increases_current_stock(self):
        """A valid Stock-In transaction raises current_stock by the given qty."""
        resp = self._post_stock_in(self.product, 50)
        self.assertRedirects(resp, reverse("inventory"))

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 50)

        # Confirm the Transaction record exists and is linked to the shop
        txn = Transaction.objects.get(product=self.product, type="IN")
        self.assertEqual(txn.quantity, 50)
        self.assertEqual(txn.shop, self.shop)

    def test_stock_out_decreases_current_stock(self):
        """A valid Stock-Out transaction lowers current_stock by the given qty."""
        # First bring stock up to 100
        self._post_stock_in(self.product, 100)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 100)

        resp = self._post_stock_out(self.product, 30)
        self.assertRedirects(resp, reverse("inventory"))

        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 70)

        txn = Transaction.objects.get(product=self.product, type="OUT")
        self.assertEqual(txn.quantity, 30)

    def test_stock_out_below_zero_rejected(self):
        """A Stock-Out exceeding current_stock must be rejected with a form error
        and must NOT change current_stock or create a Transaction record."""
        # current_stock is 0 — trying to remove 10 must fail
        resp = self._post_stock_out(self.product, 10)

        # Should NOT redirect — form re-renders with error
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Cannot remove")

        # current_stock must remain 0
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 0)

        # No Transaction record should have been created
        self.assertFalse(Transaction.objects.filter(product=self.product, type="OUT").exists())

    def test_transaction_not_visible_to_other_shop(self):
        """Transactions from Shop A must not appear in Shop B's history."""
        # Create a stock-in for Shop A's product
        self._post_stock_in(self.product, 20)
        self.client.logout()

        # Log in as a completely different shop's user
        other_user, other_shop = _make_shop_user("other_user", "Other Shop")
        self.client.login(username="other_user", password="password123")

        resp = self.client.get(reverse("transactions"))
        self.assertEqual(resp.status_code, 200)

        # The transaction list in context must be empty for the other shop
        self.assertEqual(
            resp.context["transactions"].count(), 0,
            "Shop B's transactions view must not expose Shop A's transactions.",
        )
        self.assertNotContains(resp, "WGT-001")

    def test_add_product_form_ignores_quantity_field(self):
        """Submitting a quantity field with add_product must be silently ignored —
        the product should always start at current_stock=0."""
        resp = self.client.post(reverse("inventory"), {
            "action": "add_product",
            "name": "Sneaky Product",
            "sku": "SNK-001",
            "unit_price": "5.00",
            "category": "Test",
            "reorder_level": 1,
            "description": "",
            # Attacker/tester tries to inject an initial quantity via POST
            "quantity": 9999,
            "current_stock": 9999,
        })

        self.assertRedirects(resp, reverse("inventory"))
        product = Product.objects.get(sku="SNK-001")
        self.assertEqual(
            product.current_stock, 0,
            "current_stock must be 0 regardless of any quantity/current_stock in POST data.",
        )
