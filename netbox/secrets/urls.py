from django.urls import path

from extras.views import ObjectChangeLogView
from . import views
from .models import Secret, SecretRole

app_name = 'secrets'
urlpatterns = [

    # Secret roles
    path('secret-roles/', views.SecretRoleListView.as_view(), name='secretrole_list'),
    path('secret-roles/add/', views.SecretRoleCreateView.as_view(), name='secretrole_add'),
    path('secret-roles/import/', views.SecretRoleBulkImportView.as_view(), name='secretrole_import'),
    path('secret-roles/delete/', views.SecretRoleBulkDeleteView.as_view(), name='secretrole_bulk_delete'),
    path('secret-roles/<slug:slug>/edit/', views.SecretRoleEditView.as_view(), name='secretrole_edit'),
    path('secret-roles/<slug:slug>/changelog/', ObjectChangeLogView.as_view(), name='secretrole_changelog', kwargs={'model': SecretRole}),

    # Secrets
    path('secrets/', views.SecretListView.as_view(), name='secret_list'),
    path('secrets/import/', views.SecretBulkImportView.as_view(), name='secret_import'),
    path('secrets/edit/', views.SecretBulkEditView.as_view(), name='secret_bulk_edit'),
    path('secrets/delete/', views.SecretBulkDeleteView.as_view(), name='secret_bulk_delete'),
    path('secrets/<int:pk>/', views.SecretView.as_view(), name='secret'),
    path('secrets/<int:pk>/edit/', views.secret_edit, name='secret_edit'),
    path('secrets/<int:pk>/delete/', views.SecretDeleteView.as_view(), name='secret_delete'),
    path('secrets/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='secret_changelog', kwargs={'model': Secret}),

]
