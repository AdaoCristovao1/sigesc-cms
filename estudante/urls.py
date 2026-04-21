from django.urls import path
from . import views

app_name = 'estudante'

urlpatterns = [
    path('home/', views.aluno_home, name='aluno_home'),
    path('Geral/', views.alunos_geral, name='alunos_inativos'),
    path("meus-professores", views.meus_professores, name="meus_professores"),
    path('historico-academico', views.historico_academico, name='historico_academico'),
    path('historico-finaceiro', views.historico_financeiro, name='historico_financeiro'),
    path('recados-para-o-estimado-aluno', views.recados, name='recados'),
    path('aproveitamnento-escolar', views.aproveitamento_escolar, name='aproveitamento'),
    path('dados-aproveitamento/', views.dados_aproveitamento, name='dados_aproveitamento'),
    path('pagamentos', views.pagamentos, name='pagamentos'),
]