from django.urls import path
from .views import user_profiles

urlpatterns = [
    path('', user_profiles, name='user_profiles'),  # Maps the root URL to user_profiles view
    path('user-profiles/', user_profiles, name='user_profiles'),
]
