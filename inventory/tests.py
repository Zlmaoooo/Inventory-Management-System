from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Product, Profile, Shop


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
        # Product must belong to a shop now — use the test user's shop.
        Product.objects.create(
            shop=self.shop,
            name="Rice",
            sku="RICE-001",
            quantity=10,
            unit_price="25.00",
            category="Grains",
            reorder_level=5,
            description="Test product",
        )

        response = self.client.get(reverse("inventory"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add New Product")
        self.assertContains(response, "Saved Inventory Items")
        self.assertContains(response, "RICE-001")

    def test_products_page_shows_catalog(self):
        self.client.login(username="testuser", password="password123")
        Product.objects.create(
            shop=self.shop,
            name="Beans",
            sku="BEAN-001",
            quantity=8,
            unit_price="12.50",
            category="Grains",
            reorder_level=3,
            description="Test product",
        )

        response = self.client.get(reverse("products"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product Catalog")
        self.assertContains(response, "BEAN-001")

    def test_saving_product_on_inventory_shows_up_in_products_catalog(self):
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("inventory"),
            {
                "name": "Sugar",
                "sku": "SUG-001",
                "quantity": 4,
                "unit_price": "18.00",
                "category": "Groceries",
                "reorder_level": 2,
                "description": "Test product",
            },
        )

        self.assertRedirects(response, reverse("inventory"))
        self.assertTrue(Product.objects.filter(sku="SUG-001").exists())

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
                "name": "AlphaWidget",
                "sku": "AW-001",
                "quantity": 50,
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
