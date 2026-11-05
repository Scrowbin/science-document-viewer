from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    institution = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "institution")

    def validate_username(self, value):
        # Login accepts a username or an email; an '@' in a username would make that ambiguous.
        if '@' in value:
            raise serializers.ValidationError("Usernames cannot contain '@'.")
        return value

    def validate_email(self, value):
        # The DB constraint is case-sensitive; treat Foo@x.org and foo@x.org as the same address.
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        candidate = User(username=attrs.get("username", ""), email=attrs.get("email", ""))
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            institution=validated_data.get("institution", ""),
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(source="date_joined", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "date_joined", "created_at")
