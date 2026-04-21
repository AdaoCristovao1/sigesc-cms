from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ['username', 'email', 'perfil', 'telefone', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {'fields': ('perfil', 'telefone', 'foto')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Adicionais', {'fields': ('perfil', 'telefone', 'foto')}),
    )
