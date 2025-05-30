import re
from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import get_user_model
import logging

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'location', 'points', 'profile_pics', 'total_harvest', 'total_waste'] 

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'location']
    
    def validate_username(self, value):
        """
        Validasi untuk memastikan username hanya berisi huruf kecil.
        """
        if not value.islower():
            raise serializers.ValidationError("Username harus berisi hanya huruf kecil.")
        return value

    def validate_password(self, value):
        """
        Validasi password sesuai aturan yang disebutkan.
        """
        # Validasi panjang password
        if len(value) < 8:
            raise serializers.ValidationError("Password harus memiliki minimal 8 karakter.")
        
        # Validasi ada huruf kecil, besar, angka, dan simbol
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password harus mengandung setidaknya satu huruf kecil.")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password harus mengandung setidaknya satu huruf besar.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password harus mengandung setidaknya satu angka.")
        if not re.search(r'[!"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]', value):
            raise serializers.ValidationError("Password harus mengandung setidaknya satu karakter spesial.")

        # Validasi karakter pertama dan terakhir bukan angka
        if value[0].isdigit() or value[-1].isdigit():
            raise serializers.ValidationError("Password tidak boleh diawali atau diakhiri dengan angka.")
        
        # Validasi password tidak boleh sama dengan username atau username terbalik
        if value.lower() == self.initial_data['username'].lower():
            raise serializers.ValidationError("Password tidak boleh sama dengan username.")
        if value.lower() == self.initial_data['username'][::-1].lower():
            raise serializers.ValidationError("Password tidak boleh sama dengan username terbalik.")
        
        return value
    
    def create(self, validated_data):
        user = CustomUser(
            username=validated_data['username'],
            email=validated_data['email']
        )
        print(f"Password sebelum hashing: {validated_data['password']}") # Log sebelum hashing
        user.set_password(validated_data['password'])  # Hash password
        print(f"Password setelah hashing: {user.password}") # Log setelah hashing
        if 'location' in validated_data:
            user.location = validated_data['location']
        user.save()
        print(f"Password disimpan di database: {user.password}")
        return user
    
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email Pengguna")
    password = serializers.CharField(write_only=True, label="Kata Sandi")

    def validate(self, data):
        CustomUser = get_user_model()  # Ambil model user kustom
        try:
            user = CustomUser.objects.get(email=data['email'])  # Cari user berdasarkan email
            print(f"User ditemukan: {user.email}")  # Log user ditemukan
            print(f"Password di database: {user.password}")  # Log password hashed di DB
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid login credentials")

        # Verifikasi password
        if not user.check_password(data['password']):
            print(f"Password yang dimasukkan: {data['password']}")  # Log password input
            print("Password tidak valid")  # Log jika password tidak valid
            raise serializers.ValidationError("Invalid login credentials")

        # Pastikan akun aktif
        if not user.is_active:
            raise serializers.ValidationError("Akun Anda tidak aktif.")
        
        return user
    
class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ValidateOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=5)
    new_password = serializers.CharField(min_length=8)

class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'location']

    def validate_username(self, value):
        if not value.islower():
            raise serializers.ValidationError("Username harus berisi hanya huruf kecil.")
        return value

class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser 
        fields = ['id', 'username', 'points', 'profile_pics', 'total_harvest', 'total_waste']