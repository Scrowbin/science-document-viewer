from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/v1/auth/register/'
        self.login_url = '/api/v1/auth/token/'
        self.refresh_url = '/api/v1/auth/token/refresh/'
        self.me_url = '/api/v1/auth/me/'
        self.logout_url = '/api/v1/auth/logout/'

        self.test_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='Password123!'
        )

    def test_user_registration_success(self):
        payload = {
            'username': 'newresearcher',
            'email': 'new@example.com',
            'password': 'StrongPassword123!',
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'new@example.com')
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('created_at', response.data['user'])
        self.assertIn('date_joined', response.data['user'])

    def test_user_registration_duplicate_email(self):
        payload = {
            'username': 'anotheruser',
            'email': 'existing@example.com',
            'password': 'Password123!',
        }
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_success(self):
        payload = {
            'username': 'existinguser',
            'password': 'Password123!',
        }
        response = self.client.post(self.login_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_current_user_me_endpoint(self):
        self.client.force_authenticate(user=self.test_user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'existinguser')
        self.assertEqual(response.data['email'], 'existing@example.com')
        self.assertIn('created_at', response.data)
        self.assertIn('date_joined', response.data)

    def test_token_refresh(self):
        login_resp = self.client.post(self.login_url, {
            'username': 'existinguser',
            'password': 'Password123!',
        }, format='json')
        refresh_token = login_resp.data['refresh']

        refresh_resp = self.client.post(self.refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_resp.data)

    def test_logout_and_token_blacklisting(self):
        login_resp = self.client.post(self.login_url, {
            'username': 'existinguser',
            'password': 'Password123!',
        }, format='json')
        refresh_token = login_resp.data['refresh']

        logout_resp = self.client.post(self.logout_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(logout_resp.status_code, status.HTTP_200_OK)

        # Attempting to refresh with the blacklisted token must fail with 401 Unauthorized
        fail_refresh = self.client.post(self.refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(fail_refresh.status_code, status.HTTP_401_UNAUTHORIZED)
