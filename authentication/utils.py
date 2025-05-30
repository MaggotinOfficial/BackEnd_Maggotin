import requests
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

def get_location_from_ip(ip):
    """
    Ambil lokasi berdasarkan IP menggunakan ip-api.com.
    """
    try:
        if ip == "127.0.0.1":
            ip = "8.8.8.8"  

        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        if response.status_code == 200 and data.get("status") == "success":
            city = data.get("city", "")
            region = data.get("regionName", "")
            country = data.get("country", "")
            return f"{city}, {region}, {country}"
        return "Unknown Location"
    except Exception as e:
        print(f"Error getting location: {e}")
        return "Unknown Location"

User = get_user_model()
token_generator = PasswordResetTokenGenerator()
def generate_password_reset_token(user):
    return token_generator.make_token(user)

def send_password_reset_email(user, request):
    # Generate token dan UID
    token = PasswordResetTokenGenerator().make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # Generate reset link
    reset_link = f"{request.scheme}://{request.get_host()}/auth/reset-password/{uid}/{token}/"

    # Log token, UID, dan reset link
    print(f"Token: {token}")
    print(f"UID: {uid}")
    print(f"Reset Link: {reset_link}")

    # Kirim email
    send_mail(
        "Reset Your Password",
        f"Click the link below to reset your password:\n\n{reset_link}",
        "no-reply@example.com",
        [user.email],
    )