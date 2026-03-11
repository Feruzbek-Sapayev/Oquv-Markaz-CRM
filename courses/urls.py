from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Courses
    path('', views.course_list, name='course_list'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('create/', views.course_create, name='course_create'),
    path('<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('<int:pk>/delete/', views.course_delete, name='course_delete'),
    path('<int:pk>/assign-teacher/', views.course_assign_teacher, name='course_assign_teacher'),
    path('teachers/<int:pk>/remove/', views.course_remove_teacher, name='course_remove_teacher'),
    # Groups
    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:pk>/', views.group_detail, name='group_detail'),
    path('groups/create/', views.group_create, name='group_create'),
    path('groups/<int:pk>/edit/', views.group_edit, name='group_edit'),
    path('groups/<int:pk>/delete/', views.group_delete, name='group_delete'),
    path('groups/<int:pk>/export/', views.group_export_excel, name='group_export'),
    # Enrollments
    path('groups/<int:group_pk>/enroll/', views.enrollment_create, name='enrollment_create'),
    path('enrollments/<int:pk>/remove/', views.enrollment_remove, name='enrollment_remove'),
]
