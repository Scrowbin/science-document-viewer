from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/v1/auth/register/"
        self.login_url = "/api/v1/auth/token/"
        self.refresh_url = "/api/v1/auth/token/refresh/"
        self.me_url = "/api/v1/auth/me/"
        self.logout_url = "/api/v1/auth/logout/"

        self.test_user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="Password123!",
            institution="cbt university",
        )

    def test_user_registration_success(self):
        payload = {
            "username": "newresearcher",
            "email": "new@example.com",
            "password": "StrongPassword123!",
            "institution": "cbt university 2",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("tokens", response.data)
        self.assertEqual(response.data["user"]["email"], "new@example.com")
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertIn("created_at", response.data["user"])
        self.assertIn("date_joined", response.data["user"])

    def test_user_registration_duplicate_email(self):
        payload = {
            "username": "anotheruser",
            "email": "existing@example.com",
            "password": "Password123!",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        payload = {
            "username": "existinguser",
            "password": "Password123!",
        }
        response = self.client.post(self.login_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_current_user_me_endpoint(self):
        self.client.force_authenticate(user=self.test_user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "existinguser")
        self.assertEqual(response.data["email"], "existing@example.com")
        self.assertIn("created_at", response.data)
        self.assertIn("date_joined", response.data)

    def test_token_refresh(self):
        login_resp = self.client.post(
            self.login_url,
            {
                "username": "existinguser",
                "password": "Password123!",
            },
            format="json",
        )
        refresh_token = login_resp.data["refresh"]

        refresh_resp = self.client.post(
            self.refresh_url, {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_resp.data)

    def test_logout_and_token_blacklisting(self):
        login_resp = self.client.post(
            self.login_url,
            {
                "username": "existinguser",
                "password": "Password123!",
            },
            format="json",
        )
        refresh_token = login_resp.data["refresh"]

        logout_resp = self.client.post(
            self.logout_url, {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(logout_resp.status_code, status.HTTP_200_OK)

        # Attempting to refresh with the blacklisted token must fail with 401 Unauthorized
        fail_refresh = self.client.post(
            self.refresh_url, {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(fail_refresh.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthHardeningTests(TestCase):
    """Registration validation, email/username login rules and auth throttling (2026-11)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="alice", email="Alice@Example.com", password="Password123!"
        )

    def _register(self, **overrides):
        payload = {"username": "bob", "email": "bob@example.com", "password": "StrongPassword123!"}
        payload.update(overrides)
        return self.client.post("/api/v1/auth/register/", payload, format="json")

    def test_registration_validation(self):
        self.assertEqual(self._register(username="bob@example").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._register(password="password").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._register(password="12345678901").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._register(email="alice@example.com").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._register().status_code, status.HTTP_201_CREATED)

    def test_login_by_email_case_insensitive_and_inactive_rejected(self):
        url = "/api/v1/auth/token/"
        for ident in ("alice", "alice@example.com", "ALICE@EXAMPLE.COM"):
            resp = self.client.post(url, {"username": ident, "password": "Password123!"}, format="json")
            self.assertEqual(resp.status_code, status.HTTP_200_OK, ident)
        resp = self.client.post(url, {"username": "alice@example.com", "password": "wrong"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.user.is_active = False
        self.user.save()
        resp = self.client.post(url, {"username": "alice", "password": "Password123!"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        from django.contrib.auth import authenticate
        self.assertIsNone(authenticate(username="alice", password="Password123!"))

    def test_logout_requires_valid_refresh_token(self):
        self.assertEqual(self.client.post("/api/v1/auth/logout/", {}, format="json").status_code,
                         status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.post("/api/v1/auth/logout/", {"refresh": "garbage"}, format="json").status_code,
                         status.HTTP_400_BAD_REQUEST)

    def test_login_is_throttled(self):
        from unittest.mock import patch
        from django.core.cache import cache
        from rest_framework.throttling import ScopedRateThrottle
        cache.clear()
        self.addCleanup(cache.clear)
        with patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"auth": "2/min"}):
            codes = [
                self.client.post("/api/v1/auth/token/", {"username": "alice", "password": "x"}, format="json").status_code
                for _ in range(3)
            ]
        self.assertEqual(codes, [401, 401, 429])
