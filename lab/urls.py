from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('delete/<int:pk>/', views.delete_record, name='delete_record'),  # YANGI QO'SHILDI
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.landing_page, name='landing'),
    path('export/', views.export_excel, name='export_excel'),
    path('guide/', views.guide_view, name='guide'),

]
