from django.urls import path
from . import views

app_name='financa'
          
urlpatterns = [
    path('financas/', views.financas, name='financas'),
    path('pagamento/<int:aluno_id>/<str:servico>/', views.pagamento_servico, name='pagamento_servico'),
    path('pagar/<int:aluno_id>/propina', views.processar_pagamento_propina, name='pagar_propina'),
    path('pagar/<int:aluno_id>/servicos', views.processar_pagamento_servicos, name='pagar_servicos'),
    path('pagamento-manual-servicos/<int:aluno_id>', views.pagamento_manual, name='pagamento_manual'),
    path('servicos/', views.emolumentos, name='servicos'),
    path('add_emolumento/', views.add_emolumento, name='add_emolumento'),
    path('edit_emolumento/', views.edit_emolumento, name='edit_emolumento'),
    path('add_multa/', views.add_multa, name='add_multa'),
    path('edit_multa/', views.edit_multa, name='edit_multa'),
    path('add_pagamento/', views.add_pagamento, name='add_pagamento'),
    path('edit_pagamento/', views.edit_pagamento, name='edit_pagamento'),
    path('add_mes/', views.add_mes, name='add_mes'),
    path('edit_mes/', views.edit_mes, name='edit_mes'),
    path('delete_item/', views.delete_item, name='delete_item'), 
    path('relatorios/', views.relatorio_view, name='relatorios'),   
    path('documentos/historico-finaceiro/<int:aluno_id>/', views.historico_financeiro, name='historico_finaceiro'),
    path("obter-meses/", views.obter_meses, name="obter_meses"),
    path('gestao-de-despesas/', views.despesas, name='despesas'),
    path('despesas/adicionar/', views.adicionar_despesa, name='adicionar_despesa'),
    path('despesas/excluir/<int:id>/', views.excluir_despesa, name='excluir_despesa'),
    path('despesas/editar/<int:id>/', views.editar_despesa, name='editar_despesa'),
    path('gerar-folha-salario/', views.gerar_folha_salario, name='gerar_folha_salario'),
    path('editar/valor-falta/', views.editValorFalta, name='editValorFalta')     
]