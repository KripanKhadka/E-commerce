from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Item, Order, OrderItem, Payment


class SportsStoreViewsTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(
            title="Nike Mercurial Vapor Pro",
            price=129.99,
            discount_price=99.99,
            category="FB",
            label="D",
            slug="nike-mercurial-vapor-pro",
            description="Elite football boots built for speed.",
            image="sample.png",
            brand="Nike",
        )

    def test_home_page_shows_sports_storefront(self):
        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ArenaSports")
        self.assertContains(response, "Train harder. Shop smarter.")
        self.assertContains(response, self.item.title)

    def test_home_page_groups_products_by_sport_category(self):
        Item.objects.create(
            title="Spalding Basketball",
            price=79.99,
            discount_price=59.99,
            category="BK",
            label="S",
            slug="spalding-basketball",
            description="A durable basketball for training and games.",
            image="sample.png",
            brand="Spalding",
        )

        response = self.client.get(reverse("core:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Football / Soccer")
        self.assertContains(response, "Basketball")

    def test_product_detail_page_shows_add_to_cart(self):
        response = self.client.get(reverse("core:product", kwargs={"slug": self.item.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add to Cart")

    def test_user_can_add_item_to_cart(self):
        user = get_user_model().objects.create_user(username="tester", password="secret123")
        self.client.login(username="tester", password="secret123")

        response = self.client.get(reverse("core:add-to-cart", kwargs={"slug": self.item.slug}))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.filter(user=user, ordered=False).exists())
        self.assertTrue(OrderItem.objects.filter(user=user, item=self.item, ordered=False).exists())

    def test_user_can_remove_item_from_cart(self):
        user = get_user_model().objects.create_user(username="tester", password="secret123")
        self.client.login(username="tester", password="secret123")
        self.client.get(reverse("core:add-to-cart", kwargs={"slug": self.item.slug}))

        response = self.client.get(reverse("core:remove-from-cart", kwargs={"slug": self.item.slug}))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Order.objects.filter(user=user, ordered=False).exists())
        self.assertFalse(OrderItem.objects.filter(user=user, item=self.item, ordered=False).exists())

    def test_coupon_can_be_applied_to_order(self):
        user = get_user_model().objects.create_user(username="tester2", password="secret123")
        self.client.login(username="tester2", password="secret123")
        self.client.get(reverse("core:add-to-cart", kwargs={"slug": self.item.slug}))
        self.client.post(reverse("core:add-coupon"), {"code": "SAVE10"})

        order = Order.objects.get(user=user, ordered=False)
        self.assertEqual(order.coupon.code, "SAVE10")

    def test_refund_page_is_available(self):
        user = get_user_model().objects.create_user(username="tester3", password="secret123")
        self.client.login(username="tester3", password="secret123")

        response = self.client.get(reverse("core:request-refund"))

        self.assertEqual(response.status_code, 200)

    def test_user_can_register(self):
        response = self.client.post(
            reverse("register"),
            {"username": "newuser", "email": "new@example.com", "password1": "StrongPass123!", "password2": "StrongPass123!"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username="newuser").exists())

    def test_payment_page_completes_checkout(self):
        user = get_user_model().objects.create_user(username="tester4", password="secret123")
        self.client.login(username="tester4", password="secret123")
        self.client.get(reverse("core:add-to-cart", kwargs={"slug": self.item.slug}))

        response = self.client.post(
            reverse("core:checkout"),
            {"street_address": "123 Main St", "apartment_address": "Apt 4", "zip": "10001"},
        )

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(user=user, ordered=False)
        self.assertIsNotNone(order.shipping_address)

        payment_response = self.client.get(reverse("core:payment"))
        self.assertEqual(payment_response.status_code, 200)

        self.client.post(reverse("core:payment"))
        order.refresh_from_db()
        self.assertTrue(order.ordered)
        self.assertTrue(Payment.objects.filter(user=user).exists())
