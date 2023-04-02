from django.urls import path, include
from .views import AccountProfile, auth_code


urlpatterns = [
  path('profile', AccountProfile.as_view(), name='account_profile'),
  path('auth_code', auth_code, name='auth_code'),
  path('', include('allauth.urls')),
]