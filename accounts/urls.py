from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('inscription/', views.register, name='register'),
    path('connexion/', views.user_login, name='login'),
    path('deconnexion/', views.user_logout, name='logout'),
    path('tableau-de-bord/', views.dashboard, name='dashboard'),
    path('profil/', views.profile, name='profile'),
    path('profil/modifier/', views.profile_edit, name='profile_edit'),
]
