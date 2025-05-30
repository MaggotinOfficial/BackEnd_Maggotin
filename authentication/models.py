from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

class CustomUser(AbstractUser):
    location = models.CharField(max_length=255, blank=True, null=True) 
    points = models.IntegerField(default=0)
    profile_pics = models.ImageField(upload_to='profilepics/', blank=True, null=True)
    total_harvest = models.BigIntegerField(default=0)
    total_waste = models.BigIntegerField(default=0)

    def __str__(self):
        return self.email
    

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    otp = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def generate_otp(self):
        """Generate a random OTP of 6 digits."""
        self.otp = ''.join(random.choices(string.digits, k=5))
        self.expires_at = self.created_at + timedelta(minutes=10)  # OTP valid for 10 minutes

    def is_valid(self):
        """Check if OTP is valid and not expired."""
        if self.expires_at is None:
            return False  # Jika expires_at tidak diatur, anggap OTP tidak valid
        return self.expires_at > timezone.now()

    def __str__(self):
        return f"OTP for {self.user.email}"