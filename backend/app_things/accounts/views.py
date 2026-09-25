from itertools import repeat
from random import randint
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes


def login_view(request):
    email = request.POST["email"]
    password = request.POST["password"]
    user = authenticate(request, email=email, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False, "reason": "invalid credentials!"})


def register_view(request):
    username = request.POST["username"]
    email = request.POST["email"]
    institution = request.POST["institution"]
    password = request.POST["password"]
    repeat_password = request.POST["repeat_password"]

    if valid_email(email) and valid_password(password, repeat_password):
        user_model = get_user_model()
        user_model.objects.create_user(
            username=username, email=email, institution=institution, password=password
        )

        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False, "reason": "Invalid email / password"})


def send_reset_password_code_view(request):
    email = request.POST["email"]
    User = get_user_model()
    user = User.objects.filter(email=email).first()
    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_url = f"http://localhost:5173/reset/{uid}/{token}/"

        # dev only
        print(reset_url)

        # prod:
        # send_reset_url(email, reset_url)
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False})


def reset_password_view(request):
    User = get_user_model()
    uid = request.POST["uid"]
    token = request.POST["token"]
    new_password = request.POST["new_password"]

    try:
        user_id = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=user_id)
    except (ValueError, TypeError, User.DoesNotExist):
        return JsonResponse({"error": "Invalid reset link"}, status=400)

    if not default_token_generator.check_token(user, token):
        return JsonResponse({"error": "Invalid or expired reset link"}, status=400)

    user.set_password(new_password)
    user.save()

    return JsonResponse({"message": "Password reset successfully"})


def logout_view(request):
    logout(request)
    return JsonResponse({"message": "Logged out"})


# utilities
def valid_email(email):
    user_found = get_user_model().objects.filter(email=email).first()
    if user_found:
        return True
    else:
        return False


def valid_password(password, repeated_password):
    if (password != repeated_password) or (len(password) < 7):
        return False
    else:
        return True


# def send_reset_url(email, reset_url):
