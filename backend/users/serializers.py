from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    agree_to_terms = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "password",
            "confirm_password",
            "agree_to_terms",
        )

    def validate(self, data):
        # ✅ Check if passwords match
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")

        # ✅ Check if terms are agreed
        if not data.get("agree_to_terms"):
            raise serializers.ValidationError("You must agree to the terms.")

        # ✅ Check if email already exists (fixed typo here)
        email = data.get("email")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")

        return data

    def create(self, validated_data):
        # Remove non-model fields
        validated_data.pop("confirm_password")
        validated_data.pop("agree_to_terms")

        # ✅ Create user
        user = User.objects.create_user(
            username=validated_data["email"],  # use email as username
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=validated_data["password"],
            
        )
        return user

    def to_representation(self, instance):
        """Return camelCase to frontend"""
        refresh = RefreshToken.for_user(instance)
        return {
            "token": str(refresh.access_token),
            "user": {
                "id": instance.id,
                "email": instance.email,
                "firstName": instance.first_name,
                "lastName": instance.last_name,
            },
        }

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    
