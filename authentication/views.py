from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CustomUser, PasswordResetOTP
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer, RequestOTPSerializer, UserSerializer, ValidateOTPSerializer, UpdateUserSerializer, LeaderboardSerializer
from django.contrib.auth import authenticate, get_user_model
from .utils import get_location_from_ip, send_password_reset_email
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str 
from django.core.exceptions import ValidationError
from django.core.mail import send_mail  

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        """
        Override metode create untuk menyisipkan lokasi berdasarkan IP.
        """
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')  # Ambil IP pengguna
        print(f"IP User: {ip}")  # Debugging IP
        location = get_location_from_ip(ip)  # Ambil lokasi dari utils
        print(f"User Location: {location}")  # Debugging lokasi

        # Buat salinan data yang dapat diubah
        mutable_data = request.data.copy()
        mutable_data['location'] = location  # Tambahkan lokasi ke data

        # Gunakan mutable_data untuk serializer
        serializer = self.get_serializer(data=mutable_data)
        if not serializer.is_valid():
            print("Serializer Errors: ", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        print(f"Password setelah save di database: {user.password}")  # Log setelah save
        return Response(self.get_serializer(user).data, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        print(f"Request Data: {request.data}")  # Debug data yang diterima dari request
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            print(f"User valid: {user.username}")  # Debug user yang berhasil login
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                }
            })
        print(f"Serializer Errors: {serializer.errors}")  # Debug error pada serializer
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()  # ✅ Masukkan token ke blacklist
            return Response({"message": "Logout berhasil"}, status=200)
        except Exception as e:
            return Response({"error": "Token tidak valid"}, status=400)

class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
            send_password_reset_email(user, request)
            return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
class ResetPasswordView(APIView):
    def post(self, request, uidb64, token):
        try:
            # Debug token dan UID
            print(f"UIDB64 received: {uidb64}")
            print(f"Token received: {token}")

            # Tambahkan padding jika diperlukan
            uidb64 += '=' * (-len(uidb64) % 4)

            # Decode UID
            user_id = force_str(urlsafe_base64_decode(uidb64))
            print(f"Decoded user ID: {user_id}")

            # Cari user berdasarkan ID
            user = CustomUser.objects.get(pk=user_id)
            print(f"User found: {user.email}")

            # Verifikasi token
            if not PasswordResetTokenGenerator().check_token(user, token):
                print("Invalid or expired token.")
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

            # Ambil password baru
            new_password = request.data.get("password")
            if not new_password:
                return Response({"error": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Set password baru
            user.set_password(new_password)
            user.save()
            print("Password reset successful.")
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        except (ValidationError, CustomUser.DoesNotExist, ValueError) as e:
            print(f"Error: {e}")
            return Response({"error": "Invalid token or user does not exist."}, status=status.HTTP_400_BAD_REQUEST)

class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sort_by = request.query_params.get('sort_by', 'points')  # Default to 'points'
        
        # Validate the sort_by parameter
        if sort_by not in ['points', 'total_harvest', 'total_waste']:
            return Response({"error": "Invalid sort_by parameter"}, status=status.HTTP_400_BAD_REQUEST)

        # Order users based on the selected criteria
        users = CustomUser .objects.filter(is_staff=False, is_superuser=False) .order_by(f'-{sort_by}', 'username')
        
        if not users.exists():
            return Response({"message": "Leaderboard is empty"}, status=status.HTTP_200_OK)

        serializer = LeaderboardSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class UserDetailView(APIView):
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]  # Memastikan pengguna sudah login

    def post(self, request):
        # Ambil password lama dan password baru dari request data
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({"error": "Both old and new passwords are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Ambil user yang sedang login
        user = request.user

        # Verifikasi apakah password lama benar
        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        # Set password baru
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password has been updated successfully."}, status=status.HTTP_200_OK)

class RequestOTPView(APIView):
    def post(self, request):
        # Validasi email
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = get_user_model().objects.get(email=email)
                
                # Generate OTP
                otp_instance = PasswordResetOTP.objects.create(user=user)
                otp_instance.generate_otp()
                otp_instance.save()

                # Kirim email dengan OTP
                send_mail(
                    "Your OTP for Password Reset",
                    f"Your OTP is {otp_instance.otp}. It is valid for 10 minutes.",
                    "no-reply@example.com",
                    [email],
                )

                return Response({"message": "OTP sent to email."}, status=status.HTTP_200_OK)
            
            except get_user_model().DoesNotExist:
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ValidateOTPView(APIView):
    def post(self, request):
        serializer = ValidateOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_input = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']

            print(f"Email: {email}, OTP: {otp_input}, New Password: {new_password}") 

            try:
                user = get_user_model().objects.get(email=email)
                otp_instance = PasswordResetOTP.objects.filter(user=user).order_by('-created_at').first()

                # Verifikasi apakah OTP valid
                if otp_instance is None or not otp_instance.is_valid():
                    return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

                if otp_instance.otp != otp_input:
                    return Response({"error": "Incorrect OTP."}, status=status.HTTP_400_BAD_REQUEST)

                # Update password
                user.set_password(new_password)
                user.save()

                # Hapus OTP setelah sukses
                otp_instance.delete()

                return Response({"message": "Password successfully changed."}, status=status.HTTP_200_OK)

            except get_user_model().DoesNotExist:
                print("User  does not exist") 
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateUserView(APIView):
    permission_classes = [IsAuthenticated]  # Hanya user yang login yang bisa update

    def put(self, request):
        user = request.user
        serializer = UpdateUserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User data updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
