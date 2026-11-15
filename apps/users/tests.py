from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthAPITests(APITestCase):
    def setUp(self):
        self.email = "ana@universidad.edu"
        self.password = "ClaveSegura123"
        self.register_payload = {
            "email": self.email,
            "username": "ana",
            "password": self.password,
        }

    def register(self, **overrides):
        payload = {**self.register_payload, **overrides}
        return self.client.post(reverse("auth-register"), payload)

    def login(self, email=None, password=None):
        return self.client.post(
            reverse("auth-login"),
            {"email": email or self.email, "password": password or self.password},
        )

    def test_register_creates_user_with_hashed_password(self):
        response = self.register()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=self.email)
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(user.check_password(self.password))
        self.assertNotIn("password", response.data)

    def test_register_rejects_duplicate_email(self):
        self.register()
        response = self.register(username="otra")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_register_rejects_weak_password(self):
        response = self.register(password="123")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_login_returns_tokens_and_is_case_insensitive(self):
        self.register()
        response = self.login(email="ANA@Universidad.edu")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_wrong_password_fails(self):
        self.register()
        response = self.login(password="OtraClave123")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_token(self):
        response = self.client.get(reverse("auth-me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_authenticated_user(self):
        self.register()
        access = self.login().data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.get(reverse("auth-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.email)
        self.assertNotIn("password", response.data)

    def test_refresh_rotates_and_blacklists_previous_token(self):
        self.register()
        refresh = self.login().data["refresh"]

        response = self.client.post(reverse("auth-refresh"), {"refresh": refresh})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertNotEqual(response.data["refresh"], refresh)

        reused = self.client.post(reverse("auth-refresh"), {"refresh": refresh})
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_refresh_token(self):
        self.register()
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        response = self.client.post(reverse("auth-logout"), {"refresh": tokens["refresh"]})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        retry = self.client.post(reverse("auth-refresh"), {"refresh": tokens["refresh"]})
        self.assertEqual(retry.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_returns_400(self):
        self.register()
        access = self.login().data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.post(reverse("auth-logout"), {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password(self):
        self.register()
        access = self.login().data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.post(
            reverse("auth-change-password"),
            {"current_password": self.password, "new_password": "NuevaClave456"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(self.login().status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            self.login(password="NuevaClave456").status_code, status.HTTP_200_OK
        )
