from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.test import override_settings
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

    def test_login_with_username_works(self):
        user, shop = _make_shop_user("emailuser", "Email User Shop")
        user.email = "emailuser@example.com"
        user.save()

        response = self.client.post(
            reverse("landing"),
            {"username": user.username, "password": "password123"},
            follow=True,
        )
        self.assertRedirects(response, reverse("dashboard"))

    def test_login_with_email_works(self):
        user, shop = _make_shop_user("emailuser", "Email User Shop")
        user.email = "emailuser@example.com"
        user.save()

        response = self.client.post(
            reverse("landing"),
            {"username": user.email, "password": "password123"},
            follow=True,
        )
        self.assertRedirects(response, reverse("dashboard"))

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

    def test_registration_rejects_duplicate_email(self):
        existing = User.objects.create_user(
            username="existing",
            email="duplicate@example.com",
            password="password123",
        )

        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": existing.email,
                "password": "password123",
                "confirm_password": "password123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email already exists.")
        self.assertFalse(User.objects.filter(username="newuser").exists())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_flow_sends_email(self):
        user = User.objects.create_user(
            username="resetuser",
            email="resetuser@example.com",
            password="password123",
        )

        response = self.client.post(
            reverse("password_reset"),
            {"email": user.email},
        )

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(user.email, mail.outbox[0].to)
        self.assertIn("/accounts/reset/", mail.outbox[0].body)


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


# ---------------------------------------------------------------------------
# Product edit / delete / archive tests
# ---------------------------------------------------------------------------

class ProductEditDeleteTests(TestCase):
    """Tests for the product edit, delete, and archive lifecycle.

    Covers: edit updates metadata but not stock, hard-delete with no
    transactions, archive-instead-of-delete with transaction history,
    archived product exclusion from stock dropdowns, and cross-shop
    isolation on edit/delete endpoints.
    """

    def setUp(self):
        self.user, self.shop = _make_shop_user("edit_user", "Edit Shop")
        self.product = _make_product(self.shop, name="Original Name", sku="ORIG-001")
        self.client.login(username="edit_user", password="password123")

    # ------------------------------------------------------------------
    # 1. Edit updates metadata but NOT current_stock
    # ------------------------------------------------------------------

    def test_edit_product_updates_fields_but_not_stock(self):
        """POST to the edit URL changes name, unit_price etc. but leaves
        current_stock untouched even if an attacker injects it in POST data."""
        # Give the product some stock via a transaction first
        self.client.post(reverse("inventory"), {
            "action": "stock_in",
            "product": self.product.pk,
            "quantity": 42,
        })
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 42)

        # Now edit the product — include a bogus current_stock in POST
        resp = self.client.post(
            reverse("product_edit", args=[self.product.pk]),
            {
                "name": "Updated Name",
                "sku": "ORIG-001",
                "unit_price": "99.99",
                "category": "Updated",
                "reorder_level": 10,
                "description": "Changed.",
                "current_stock": 9999,  # should be silently ignored
            },
        )
        self.assertRedirects(resp, reverse("products"))

        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Updated Name")
        self.assertEqual(str(self.product.unit_price), "99.99")
        # current_stock must be unchanged — still 42, not 9999
        self.assertEqual(
            self.product.current_stock, 42,
            "current_stock must not be changeable via the edit form.",
        )

    # ------------------------------------------------------------------
    # 2. Hard-delete when no transactions
    # ------------------------------------------------------------------

    def test_delete_product_with_no_transactions_removes_it(self):
        """A product with zero transaction history is permanently deleted on POST."""
        pk = self.product.pk
        self.assertFalse(self.product.transactions.exists())

        resp = self.client.post(
            reverse("product_delete", args=[pk]),
            {"action": "delete"},
        )
        self.assertRedirects(resp, reverse("products"))

        # Row must be completely gone from the DB
        self.assertFalse(
            Product.all_objects.filter(pk=pk).exists(),
            "Product with no transactions should be permanently deleted.",
        )

    # ------------------------------------------------------------------
    # 3. Archive instead of delete when transactions exist
    # ------------------------------------------------------------------

    def test_delete_product_with_transactions_archives_instead(self):
        """A product with transaction history gets is_active=False, not deleted."""
        # Create a stock-in transaction so history exists
        self.client.post(reverse("inventory"), {
            "action": "stock_in",
            "product": self.product.pk,
            "quantity": 10,
        })
        self.assertTrue(self.product.transactions.exists())

        pk = self.product.pk
        resp = self.client.post(
            reverse("product_delete", args=[pk]),
            {"action": "delete"},
        )
        self.assertRedirects(resp, reverse("products"))

        # Product row must still exist (transaction FK integrity)
        self.product.refresh_from_db()
        self.assertFalse(
            self.product.is_active,
            "Product with transactions must be archived (is_active=False), not deleted.",
        )

        # Must NOT appear in the default (active) queryset
        self.assertFalse(
            Product.objects.filter(pk=pk).exists(),
            "Archived product must be excluded from the default Product queryset.",
        )

        # Must appear via all_objects (row preserved for transaction FK)
        self.assertTrue(
            Product.all_objects.filter(pk=pk).exists(),
            "Archived product row must still exist in all_objects for transaction history.",
        )

    # ------------------------------------------------------------------
    # 4. Archived products excluded from stock movement dropdown
    # ------------------------------------------------------------------

    def test_archived_products_excluded_from_stock_movement_dropdown(self):
        """After archiving, the product must not appear in StockInForm's
        product queryset (which is shop-scoped via the default manager)."""
        from .forms import StockInForm

        # Verify it's in the dropdown while active
        form_before = StockInForm(shop=self.shop)
        self.assertIn(
            self.product,
            list(form_before.fields["product"].queryset),
            "Active product should be in the stock-in dropdown.",
        )

        # Archive the product (simulate: set is_active=False directly)
        self.product.is_active = False
        self.product.save()

        # Now it must be gone from the dropdown
        form_after = StockInForm(shop=self.shop)
        self.assertNotIn(
            self.product,
            list(form_after.fields["product"].queryset),
            "Archived product must not appear in the stock-in dropdown.",
        )

    # ------------------------------------------------------------------
    # 5. Cross-shop isolation on edit and delete endpoints
    # ------------------------------------------------------------------

    def test_cannot_edit_or_delete_another_shops_product(self):
        """User B cannot edit or delete Shop A's products — both endpoints must
        redirect to the products page without making any changes."""
        other_user, other_shop = _make_shop_user("other_edit_user", "Other Shop")
        self.client.login(username="other_edit_user", password="password123")

        original_name = self.product.name
        pk = self.product.pk

        # Attempt edit
        edit_resp = self.client.post(
            reverse("product_edit", args=[pk]),
            {
                "name": "Hacked Name",
                "sku": "HACK-001",
                "unit_price": "0.01",
                "category": "Hacked",
                "reorder_level": 0,
                "description": "",
            },
        )
        self.assertRedirects(edit_resp, reverse("products"))

        # Product must be unchanged
        self.product.refresh_from_db()
        self.assertEqual(
            self.product.name, original_name,
            "Cross-shop edit attempt must not change the product name.",
        )

        # Attempt delete
        delete_resp = self.client.post(
            reverse("product_delete", args=[pk]),
            {"action": "delete"},
        )
        self.assertRedirects(delete_resp, reverse("products"))

        # Product must still exist and still be active
        self.assertTrue(
            Product.all_objects.filter(pk=pk, is_active=True).exists(),
            "Cross-shop delete attempt must not delete or archive the product.",
        )


class GoogleOAuthAccountLinkingTests(TestCase):
    def test_google_login_with_existing_email_links_to_same_user_id(self):
        """Confirm registering normally and then logging in via Google with the
        same email connects to the exact same User ID without creating duplicates."""
        from allauth.account.models import EmailAddress
        from allauth.socialaccount.models import SocialAccount, SocialApp, SocialLogin
        from allauth.socialaccount.helpers import complete_social_login
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.test import RequestFactory

        # 1. Register user normally
        user = User.objects.create_user(
            username="google_link_user",
            email="googlelink@example.com",
            password="password123",
        )
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=True,
            primary=True,
        )

        initial_user_count = User.objects.filter(email="googlelink@example.com").count()
        self.assertEqual(initial_user_count, 1)

        request = RequestFactory().get("/")
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        request.user = user

        from allauth.socialaccount.adapter import get_adapter
        social_adapter = get_adapter(request)
        provider = social_adapter.get_provider(request, "google")

        # 3. Simulate Google OAuth login with matching email
        account = SocialAccount(
            provider="google",
            uid="google-uid-99999",
            extra_data={"email": "googlelink@example.com", "email_verified": True},
        )
        sociallogin = SocialLogin(user=User(email="googlelink@example.com"), account=account)
        sociallogin.provider = provider
        sociallogin.email_addresses = [
            EmailAddress(email="googlelink@example.com", verified=True, primary=True)
        ]
        # Perform social login lookup and connect social account
        sociallogin.lookup()
        self.assertTrue(sociallogin.is_existing)
        account = sociallogin.account
        account.user = sociallogin.user or user
        account.save()

        # 3. Assert no duplicate user was created
        final_user_count = User.objects.filter(email="googlelink@example.com").count()
        self.assertEqual(
            final_user_count, 1,
            "Google login with matching email must NOT create a duplicate User row."
        )

        # 4. Assert social account connects to the exact same User ID
        linked_account = SocialAccount.objects.get(uid="google-uid-99999")
        self.assertEqual(
            linked_account.user_id, user.id,
            "Google SocialAccount must be linked to the existing user's ID."
        )

