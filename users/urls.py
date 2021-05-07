from django.urls import path
from rest_framework_simplejwt import views as jwt_views

from users.views import MyTokenObtainPairView, UserImportView
from . import views
from .views import PasswordsChangeView
from django.urls import register_converter

from jellyfish_ams.encoder import converters

register_converter(converters.HashidsConverter, 'hashids')

app_name = 'users'

urlpatterns = [
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', jwt_views.TokenVerifyView.as_view(), name='token_verify'),

    path('login/', views.login_user, name='login'),
    path('requests/<str:inventory>/<uuid:inventory_uuid>/', views.requests, name='requests'),
    path('inventory_request/accept/<hashids:obj_id>/', views.accept_hr, name='accept_hr'),
    path('inventory_request/decline/<hashids:obj_id>/', views.decline_hr, name='decline_hr'),
    path('logout/', views.logout_user, name='logout'),
    path('import/', UserImportView.as_view(), name='user-import'),
    path('change-password/', PasswordsChangeView.as_view(), name='change-password'),
]
