from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)
        print("Incoming attrs:", attrs)

        if not self.user.is_active:
            raise serializers.ValidationError(
                "Email is not verified. Please verify your email before logging in."
            )

        # Optional: add extra user info in token response
        data.update({
            "user": {
                "id": self.user.id,
                "email": self.user.email,
                "full_name": self.user.full_name,
                "is_staff": self.user.is_staff,   # ⭐ IMPORTANT
            }
        })


        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
