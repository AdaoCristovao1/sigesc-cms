from django.urls import path
from . import views

app_name = 'escola'

urlpatterns = [
    path('admin-dashboard/', views.dashboard, name='dashboard'),
    path('escolas/', views.escola_lista, name='escola_lista'),
    path('escolas/criar/', views.escola_criar, name='escola_criar'),
    path('escolas/<int:pk>/editar/', views.escola_editar, name='escola_editar'),
    path('escolas/<int:pk>/delete/', views.escola_delete, name='escola_delete'),
    path('admin/cadastro-funcionario/', views.form_funcionario, name='form_funcionario'),
    path('admin/funcionarios/novo/', views.funcionario_criar, name='funcionario_criar'),
    path('admin/funcionarios/editar/<int:pk>/', views.funcionario_editar, name='funcionario_editar'),
    path('admin/funcionarios/deletar/<int:pk>/', views.funcionario_deletar, name='funcionario_deletar'),
    path('admin/configuracoes/', views.configuracoes_sistema, name='configuracoes'),
    path('backup/criar/', views.criar_backup, name='criar_backup'),
    path('backup/baixar/<int:backup_id>/', views.baixar_backup, name='baixar_backup'),
    path('backup/restaurar/', views.restaurar_backup, name='restaurar_backup'),
    path('backup/restaurar/arquivo/', views.restaurar_backup_arquivo, name='restaurar_backup_arquivo'),
    path('backup/excluir/', views.excluir_backup, name='excluir_backup'),
    path('configuracoes/salvar/', views.salvar_configuracoes, name='salvar_configuracoes'),
    path('manutencao/limpar-cache/', views.limpar_cache, name='limpar_cache'),
    path('manutencao/otimizar-banco/', views.otimizar_banco, name='otimizar_banco'),
    path('manutencao/relatorio-sistema/', views.relatorio_sistema, name='relatorio_sistema'),
]