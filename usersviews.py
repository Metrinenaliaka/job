from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import redirect, get_object_or_404
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.conf import settings
from .models import User, EmailVerification, PasswordReset
from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    ResendVerificationSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import ValidationError


# =========================
# LOGIN
# =========================

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# =========================
# REGISTER
# =========================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()

        # Create verification token
        verification = EmailVerification.objects.create(user=user)

        verification_link = (
            f"https://simizi.net/api/users/verify-email/{verification.token}/"
        )

        email_subject = "Verify Your Simizi Account"

        email_body = f"""
Hello,

Welcome to Simizi 👋

Thank you for creating an account with Simizi. We’re excited to have you on board!

To complete your registration and secure your account, please verify your email address by clicking the link below:

🔐 Verify your email address:
{verification_link}

Once verified, you’ll have full access to Simizi and all of its features.

If you did not create a Simizi account, you can safely ignore this email — no action is required.

Thank you for choosing Simizi.

Warm regards,
The Simizi Team
🌐 https://simizi.net
"""

        send_mail(
            email_subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )


# =========================
# VERIFY EMAIL
# =========================

class VerifyEmailView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        verification = get_object_or_404(EmailVerification, token=token)

        if verification.is_expired():
            verification.delete()
            return redirect("https://simizi.net/?verified=expired")

        user = verification.user
        user.is_active = True
        user.save()

        verification.delete()

        return redirect("https://simizi.net/?verified=true")


# =========================
# RESEND VERIFICATION
# =========================

class ResendVerificationView(generics.GenericAPIView):
    serializer_class = ResendVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"message": "If the email exists, a verification link has been sent."},
                status=status.HTTP_200_OK
            )

        if user.is_active:
            return Response(
                {"message": "Account already verified."},
                status=status.HTTP_400_BAD_REQUEST
            )

        EmailVerification.objects.filter(user=user).delete()
        verification = EmailVerification.objects.create(user=user)

        verification_link = (
            f"https://simizi.net/api/users/verify-email/{verification.token}/"
        )

        send_mail(
            "Resend Email Verification - Simizi",
            f"Click the link below to verify your Simizi account:\n\n{verification_link}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return Response(
            {"message": "Verification email sent."},
            status=status.HTTP_200_OK
        )


# =========================
# REQUEST PASSWORD RESET
# =========================

class RequestPasswordResetView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"message": "If the email exists, a reset link has been sent."},
                status=status.HTTP_200_OK
            )

        PasswordReset.objects.filter(user=user).delete()
        reset = PasswordReset.objects.create(user=user)

        reset_link = (
            f"https://simizi.net/reset-password/{reset.token}/"
        )

        send_mail(
            "Reset Your Simizi Password",
            f"Click the link below to reset your password:\n\n{reset_link}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return Response(
            {"message": "Reset link sent."},
            status=status.HTTP_200_OK
        )


# =========================
# CONFIRM PASSWORD RESET
# =========================

class ConfirmPasswordResetView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, token):
        reset = get_object_or_404(PasswordReset, token=token)

        if reset.is_expired():
            reset.delete()
            return Response(
                {"error": "Reset link expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_password = request.data.get("password")

        if not new_password:
            raise ValidationError({"password": "Password required."})

        user = reset.user
        user.set_password(new_password)
        user.save()

        reset.delete()

        return Response(
            {"message": "Password reset successful."},
            status=status.HTTP_200_OK
        )
~
~
~
