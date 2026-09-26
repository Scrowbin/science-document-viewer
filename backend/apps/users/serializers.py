from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    institution = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "institution")

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
