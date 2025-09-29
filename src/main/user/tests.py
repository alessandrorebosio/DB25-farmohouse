"""Unit tests for the User app (mocked to avoid touching legacy DB).

These tests focus on business logic and view flow while avoiding actual
database writes/reads, since models are mapped to existing tables with
managed=False. We use unittest.mock to simulate ORM behavior.
"""

from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase, RequestFactory
from django.http import HttpRequest

from .forms import RegisterForm
from .backends import UserBackend
from . import views


class RegisterFormValidationTests(SimpleTestCase):
	"""Validate RegisterForm rules without saving to the database."""

	def test_tax_code_must_be_16_chars(self):
		form = RegisterForm(
			data={
				"tax_code": "short",
				"name": "Mario",
				"surname": "Rossi",
				"username": "mario",
				"email": "mario@example.com",
				"password1": "x",
				"password2": "x",
			}
		)
		self.assertFalse(form.is_valid())
		self.assertIn("tax_code", form.errors)

	@patch("user.forms.User.objects")
	def test_username_must_be_unique(self, user_manager):
		user_manager.filter.return_value.exists.return_value = True
		form = RegisterForm(
			data={
				"tax_code": "RSSMRA85T10A562S",
				"name": "Mario",
				"surname": "Rossi",
				"username": "mario",
				"email": "mario@example.com",
				"password1": "x",
				"password2": "x",
			}
		)
		self.assertFalse(form.is_valid())
		self.assertIn("username", form.errors)

	def test_passwords_must_match(self):
		form = RegisterForm(
			data={
				"tax_code": "RSSMRA85T10A562S",
				"name": "Mario",
				"surname": "Rossi",
				"username": "mario",
				"email": "mario@example.com",
				"password1": "x",
				"password2": "y",
			}
		)
		self.assertFalse(form.is_valid())
		self.assertIn("__all__", form.errors)


class UserBackendTests(SimpleTestCase):
	"""Test the custom authentication backend with mocked ORM calls."""

	@patch("user.backends.ActiveEmployee.objects")
	@patch("user.backends.Employee.objects")
	@patch("user.backends.DjangoUser.objects")
	@patch("user.backends.User.objects")
	@patch("user.backends.check_password")
	def test_authenticate_sets_staff_and_superuser(
		self,
		mock_check_password,
		mock_app_user_objects,
		mock_django_user_objects,
		mock_employee_objects,
		mock_active_employee_objects,
	):
		backend = UserBackend()

		app_user = MagicMock()
		app_user.username = "adminuser"
		app_user.email = "admin@example.com"
		app_user.password = "pbkdf2_sha256$...hashed..."
		mock_app_user_objects.get.return_value = app_user

		mock_check_password.return_value = True

		django_user = MagicMock()
		django_user.username = "adminuser"
		django_user.email = ""
		django_user.has_usable_password.return_value = False
		mock_django_user_objects.get_or_create.return_value = (django_user, True)

		mock_active_employee_objects.filter.return_value.exists.return_value = True

		employee = MagicMock()
		employee.role = "admin"
		mock_employee_objects.filter.return_value.first.return_value = employee

		user = backend.authenticate(HttpRequest(), username="adminuser", password="pw")

		self.assertIs(user, django_user)
		self.assertTrue(django_user.is_staff)
		self.assertTrue(django_user.is_superuser)

		self.assertEqual(django_user.email, "admin@example.com")

		django_user.set_unusable_password.assert_called_once()
		django_user.save.assert_called_once()


class LoginViewFlowTests(SimpleTestCase):
	"""Smoke test del flow di login con form autenticazione mockato."""

	def setUp(self):
		self.factory = RequestFactory()

	@patch("user.views.AuthenticationForm")
	@patch("user.views.login")
	def test_login_redirects_to_next_on_success(self, mock_login, mock_auth_form):
		form_instance = MagicMock()
		form_instance.is_valid.return_value = True
		form_instance.get_user.return_value = MagicMock()
		mock_auth_form.return_value = form_instance

		request = self.factory.post("/login/", data={"username": "u", "password": "p", "next": "/profile/"})
		response = views.login_view(request)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response["Location"], "/profile/")
		mock_login.assert_called_once()

