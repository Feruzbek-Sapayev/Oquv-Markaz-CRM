from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.session_list, name='session_list'),
    path('update-ajax/', views.attendance_update_ajax, name='attendance_update_ajax'),
    path('export-excel/', views.export_attendance_excel, name='export_attendance_excel'),
    path('groups/<int:group_pk>/create/', views.session_create, name='session_create'),
    path('<int:pk>/', views.session_detail, name='session_detail'),
    path('<int:pk>/delete/', views.session_delete, name='session_delete'),
]
