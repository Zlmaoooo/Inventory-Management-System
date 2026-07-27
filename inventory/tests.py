from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Product


class RegistrationAndLandingViewsTests(TestCase):
    def test_landing_page_renders_for_unauthenticated_user(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Streamline Your Inventory")
        self.assertContains(response, reverse("register"))

    def test_successful_user_registration(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
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
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.staff_user = User.objects.create_user(username="adminuser", password="password123", is_staff=True)

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
            self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_inventory_page_shows_form_and_saved_products(self):
        self.client.login(username="testuser", password="password123")
        Product.objects.create(
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
