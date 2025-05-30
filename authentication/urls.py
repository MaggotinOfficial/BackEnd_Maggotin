from django.urls import path, include
from .views import RegisterView, LoginView, RequestPasswordResetView, ResetPasswordView, ChangePasswordView, RequestOTPView, ValidateOTPView,  LeaderboardView, UserDetailView, LogoutView, UpdateUserView
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('request-reset-password/', RequestPasswordResetView.as_view(), name='request-reset-password'),
    path('reset-password/<uidb64>/<token>/', ResetPasswordView.as_view(), name='reset-password'),
    path('auth/password/reset/', include('allauth.urls')),  # Menambahkan URL reset password dari allauth
    path('change-password/', ChangePasswordView.as_view(), name='change-password'), 
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('validate-otp/', ValidateOTPView.as_view(), name='validate-otp'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
    path("logout/", LogoutView.as_view(), name="logout"), 
    path('update-user/', UpdateUserView.as_view(), name='update-user'),

]
