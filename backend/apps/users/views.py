import logging
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import UserRegisterSerializer, UserSerializer
from django.http import JsonResponse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes


logger = logging.getLogger(__name__)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class LogoutView(generics.GenericAPIView):
    """
    Logout view that invalidates/blacklists the provided refresh token.
    Allows clients to cleanly terminate their session on the server.
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Token successfully blacklisted. Logged out."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.warning("Logout token blacklist failed: %s", e)
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


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
