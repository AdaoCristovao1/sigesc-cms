from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    path('print-pauta/<int:epoca>', views.pauta_trimestre_print, name='pautas_trimestre_print'),
    path('print-pauta-coordenacao/<int:trimestre>', views.pauta_coordenacao, name='pautas_coord_trimestre_print'),
    path('alunos-print', views.alunos_print, name='print_alunos'),
    path('cartao-estudante/<int:aluno_id>/', views.cartao_estudante, name='cartao_estudante'),
    path('certificado/<int:id>/', views.certificado, name='certificado'),
    path('declaracao/<int:id>/', views.processar_declaracao, name='selecionar_declaracao'),
    path('declaracao-com-notas/<int:aluno_id>/<str:finalidade>/', views.selecionar_classe_declaracao, name='declaracao_com_notas'),
    path('declaracao-com-notas/gerar/<int:aluno_id>/<int:classe_id>/<str:finalidade>/', views.gerar_declaracao_com_notas, name='gerar_declaracao_com_notas'),
    path('declaracao-sem-notas/<int:aluno_id>/<path:finalidade>/', views.declaracao_sem_notas, name='declaracao_sem_notas'),
    path('relatorio/financeiro-completo/', views.relatorio_financeiro_pdf, name='relatorio_financeiro'), 
    path('Alunos/inadimplentes/', views.alunos_inadimpletes, name='alunos_inadimpletes'),
    path('Documentos/ata/', views.gerar_ata_prova, name='gerar_ata_prova'),
    path('boletim/<int:aluno_id>/', views.boletim_aluno, name='boletim'),
    path('api/faltas/estatisticas/', views.estatisticas_faltas, name='estatisticas_faltas'),
    path('api/faltas/funcionario/<int:funcionario_id>/', views.faltas_funcionario, name='faltas_funcionario'),
    path('registrar-falta-funcionario/', views.registrar_falta_funcionario, name='registrar_falta_funcionario'),
    path('api/faltas/remover/<int:falta_id>/', views.remover_falta_funcionario, name='remover_falta_funcionario'),
    path('recoperar/comprovativo/<int:aluno_id>/<int:pagamento_id>/', views.recoperar_comprovativo, name='recoperar_comprovativo'),
    path('horario-completo/', views.visualizar_horario_completo, name='visualizar_horario_completo'),
    path('horario-completo/pdf/', views.gerar_horario_completo, name='gerar_horario_completo'),
    path('relatorio-pedagogico/', views.relatorio_pedagogico, name='relatorio_pedagogico'),
    path('relatorio-pedagogico/impressao/', views.relatorio_pedagogico, name='relatorio_pedagogico_impressao'),
    
    # Opcional: Gerar PDF
    path('relatorio-pedagogico/pdf/', views.relatorio_pedagogico_pdf, name='relatorio_pedagogico_pdf'),
] 