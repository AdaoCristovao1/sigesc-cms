from django.urls import path
from . import views

app_name = 'administracao'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('verificar-acao/', views.verificar_acao_usuario, name='verificar_acao_usuario'),
    path('funcionarios/', views.cadastrar_funcionario, name='cadastrar_funcionario'),
    path('confirmar-acao-funcionario/', views.confirmar_acao_funcionario, name='confirmar_acao_funcionario'),
    path('excluir-funcionario/', views.excluir_funcionario, name='excluir_funcionario'),
    path('classes/', views.classes, name='classes'),
    path('classes/criar/', views.criar_classe, name='criar_classe'),
    path('classes/atualizar/', views.atualizar_classe, name='atualizar_classe'),
    path('classes/eliminar/<int:id>/', views.eliminar_classe, name='eliminar_classe'),
    path('cursos/', views.cursos, name='cursos'),
    path('cursos/criar/', views.criar_curso, name='criar_curso'),
    path('cursos/atualizar/', views.atualizar_curso, name='atualizar_curso'),
    path('cursos/eliminar/<int:id>/', views.eliminar_curso, name='eliminar_curso'),
    path('turma-salas/', views.turmas_e_salas, name='turmas_e_salas'),
    path('turmas/criar/', views.criar_turma, name='criar_turma'),
    path('turmas/editar/', views.editar_turma, name='editar_turma'),
    path('turmas/excluir/<int:turma_id>/', views.eliminar_turma, name='excluir_turma'),
    path('matriculas/', views.matriculas_view, name='matriculas'),
    path('alunos-lista/', views.alunos_view, name='alunos_lista'),
    path('alunos/editar/<int:aluno_id>/', views.editar_aluno, name='editar_aluno'),
    path('alunos/deletar/<int:aluno_id>/', views.deletar_aluno, name='deletar_aluno'), 
    path('aluno/<int:id>/', views.aluno_detalhes, name='aluno_detalhes'),
    path('aluno/<int:id>/upload-foto/', views.upload_foto_aluno, name='upload_foto_aluno'), 
    path("ano-lectivo/", views.ano_lectivo, name='ano_lectivo'),
    path('reconfirmacao/', views.reconfirmacao, name='reconfirmacao'), 
] 
