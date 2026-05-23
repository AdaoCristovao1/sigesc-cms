from pyexpat.errors import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from pedagogico.models import *
from administracao.models import *
from decimal import Decimal
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import portrait, A4, landscape
from reportlab.lib.units import mm, cm
import os
import io
from financeiro.models import *
from reportlab.lib.utils import ImageReader
from decimal import Decimal, ROUND_HALF_UP
from reportlab.lib import colors
from reportlab.graphics.barcode import code128
from django.template.loader import render_to_string
from django.core.exceptions import ObjectDoesNotExist
from datetime import date
from django.db.models import Sum, Count, Q, F, Avg
from collections import defaultdict
from django.db.models.functions import ExtractMonth
import calendar
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import base64
from reportlab.graphics.barcode import createBarcodeDrawing
import io
from datetime import time 
from django.http import FileResponse
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from django.db.models import Prefetch
from xhtml2pdf import pisa
import io

data_hoje = datetime.now() 
@login_required
def pauta_trimestre_print(request, epoca):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
    diretor = Funcionario.objects.filter(funcao__icontains="diretor_geral", escolas=escola_usuario).first()
    data_hoje = timezone.now()  # Adicionando a data atual

    reconfirmacoes = Reconfirmacao.objects.select_related(
        'aluno', 'turma', 'sala', 'classe', 'curso'
    ).filter(ano_letivo=ano_letivo, estado='Adimplente', escola=escola_usuario)

    if epoca != 5:  # Pautas por trimestre (1, 2, 3, 4)
        turmas_agrupadas = {}

        for r in reconfirmacoes.order_by('classe__numero', 'turma__nome', 'aluno__nome_completo'):
            key = f"{r.classe.numero}ª Classe - Turma: {r.turma.nome} - Sala: {r.sala.nome if r.sala else '---'} - Curso: {r.curso.nome if r.curso else '---'} - Turno: {r.turno}"
            
            if key not in turmas_agrupadas:
                turmas_agrupadas[key] = {
                    'alunos': [],
                    'disciplinas_turma': set()  # Usaremos set para evitar duplicatas
                }

            aluno = r.aluno
            classe_numero = r.classe.numero
            
            # Buscar todas as notas do aluno no trimestre específico
            notas_aluno = Nota.objects.filter(
                escola=escola_usuario,
                aluno=aluno,
                trimestre=epoca
            ).select_related('disciplina')
            
            linha = {
                'aluno': aluno.nome_completo,
                'disciplinas': {},  # Dicionário para mapear disciplinas por ID
                'estado': 'Aprovado'
            }
            
            tem_todas_notas = True
            
            for nota in notas_aluno:
                disciplina = nota.disciplina
                valor_nota = round(nota.valor)
                
                # Adicionar disciplina ao set da turma
                turmas_agrupadas[key]['disciplinas_turma'].add(disciplina)
                
                # Adicionar nota ao aluno
                linha['disciplinas'][disciplina.id] = {
                    'nome': disciplina.nome,
                    'valor': valor_nota
                }
                
                # Verificar aprovação/reprovação
                if valor_nota is not None:
                    if classe_numero < 7 and valor_nota < 5:
                        linha['estado'] = 'Reprovado'
                    elif classe_numero >= 7 and valor_nota < 10:
                        linha['estado'] = 'Reprovado'
                else:
                    tem_todas_notas = False
            
            if not tem_todas_notas:
                linha['estado'] = 'Pendente'
            
            turmas_agrupadas[key]['alunos'].append(linha)
        
        # Processar dados finais para o template
        turmas_final = {}
        for key, dados_turma in turmas_agrupadas.items():
            # Ordenar disciplinas pelo nome
            disciplinas_ordenadas = sorted(
                list(dados_turma['disciplinas_turma']),
                key=lambda x: x.nome
            )
            
            alunos_final = []
            for aluno_data in dados_turma['alunos']:
                # Criar lista ordenada de notas (na mesma ordem das disciplinas)
                notas_ordenadas = []
                for disciplina in disciplinas_ordenadas:
                    if disciplina.id in aluno_data['disciplinas']:
                        notas_ordenadas.append(aluno_data['disciplinas'][disciplina.id]['valor'])
                    else:
                        notas_ordenadas.append(None)
                
                alunos_final.append({
                    'aluno': aluno_data['aluno'],
                    'estado': aluno_data['estado'],
                    'notas': notas_ordenadas  # Lista ordenada de notas
                })
            
            turmas_final[key] = {
                'disciplinas': disciplinas_ordenadas,  # Lista ordenada de disciplinas
                'alunos': alunos_final
            }

        texto = ''
        if epoca == 4:
            texto = 'Exame'

        return render(request, 'documentos/pautas_trimestre_pdf.html', {
            'turmas_agrupadas': turmas_final,
            'trimestre': epoca,
            'diretor': diretor,
            'data': data_hoje,
            'texto': texto,
            'ano_lectivo':ano_letivo,
            'escola': escola_usuario,
        })
    
    else:  # Pautas finais (epoca = 5)
        turmas_agrupadas = {}

        for r in reconfirmacoes.order_by('classe__numero', 'turma__nome', 'aluno__nome_completo'):
            key = f"{r.classe.numero}ª Classe - Turma: {r.turma.nome} - Sala: {r.sala.nome if r.sala else '---'} - Curso: {r.curso.nome if r.curso else '---'} - Turno: {r.turno}"
            
            if key not in turmas_agrupadas:
                turmas_agrupadas[key] = {
                    'alunos': [],
                    'disciplinas_turma': set()
                }

            aluno = r.aluno
            classe_numero = r.classe.numero
            
            # Buscar todas as notas do aluno (todos os trimestres)
            notas_aluno = Nota.objects.filter(aluno=aluno, escola=escola_usuario).select_related('disciplina')
            
            linha = {
                'aluno': aluno.nome_completo,
                'disciplinas': {},
                'estado': 'Aprovado'
            }
            
            tem_todas_notas = True
            
            # Agrupar notas por disciplina
            notas_por_disciplina = {}
            for nota in notas_aluno:
                disciplina_id = nota.disciplina.id
                if disciplina_id not in notas_por_disciplina:
                    notas_por_disciplina[disciplina_id] = {
                        'disciplina': nota.disciplina,
                        'notas': {1: None, 2: None, 3: None, 4: None}
                    }
                notas_por_disciplina[disciplina_id]['notas'][nota.trimestre] = nota.valor
            
            # Calcular nota final para cada disciplina
            for disciplina_id, dados in notas_por_disciplina.items():
                disciplina = dados['disciplina']
                notas = dados['notas']
                
                # Adicionar disciplina ao set da turma
                turmas_agrupadas[key]['disciplinas_turma'].add(disciplina)
                
                # Calcular média final
                nota_final = None
                if notas[1] is not None and notas[2] is not None and notas[3] is not None:
                    if notas[4] is not None:  # Tem exame
                        media_trimestral = (notas[1] + notas[2] + notas[3]) / Decimal('3.0')
                        nota_final = (media_trimestral * Decimal('0.4')) + (notas[4] * Decimal('0.6'))

                        nota_final = nota_final.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                    else:
                        # Sem exame, calcular média simples
                        nota_final = (notas[1] + notas[2] + notas[3]) / Decimal('3.0')
                        nota_final = nota_final.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                    
                    # Verificar aprovação
                    if nota_final is not None:
                        if classe_numero < 7 and nota_final < 5:
                            linha['estado'] = 'Reprovado'
                        elif classe_numero >= 7 and nota_final < 10:
                            linha['estado'] = 'Reprovado'
                else:
                    tem_todas_notas = False
                
                # Armazenar nota final
                linha['disciplinas'][disciplina_id] = {
                    'nome': disciplina.nome,
                    'valor': nota_final
                }
            
            if not tem_todas_notas:
                linha['estado'] = 'Pendente'
            
            # Atualizar estado na reconfirmação (se necessário)
            reconfirmacao = Reconfirmacao.objects.filter(id=r.id).first()
            if reconfirmacao:
                if linha['estado'] == 'Reprovado':
                    reconfirmacao.estadoClasse = 'Reprovado'
                    reconfirmacao.save()
                elif linha['estado'] == 'Aprovado':
                    reconfirmacao.estadoClasse = 'Aprovado'
                    reconfirmacao.save()
            
            turmas_agrupadas[key]['alunos'].append(linha)
        
        # Processar dados finais para o template
        turmas_final = {}
        for key, dados_turma in turmas_agrupadas.items():
            # Ordenar disciplinas pelo nome
            disciplinas_ordenadas = sorted(
                list(dados_turma['disciplinas_turma']),
                key=lambda x: x.nome
            )
            
            alunos_final = []
            for aluno_data in dados_turma['alunos']:
                # Criar lista ordenada de notas (na mesma ordem das disciplinas)
                notas_ordenadas = []
                for disciplina in disciplinas_ordenadas:
                    if disciplina.id in aluno_data['disciplinas']:
                        notas_ordenadas.append(aluno_data['disciplinas'][disciplina.id]['valor'])
                    else:
                        notas_ordenadas.append(None)
                
                alunos_final.append({
                    'aluno': aluno_data['aluno'],
                    'estado': aluno_data['estado'],
                    'notas': notas_ordenadas  # Lista ordenada de notas
                })
            
            turmas_final[key] = {
                'disciplinas': disciplinas_ordenadas,  # Lista ordenada de disciplinas
                'alunos': alunos_final
            }

        return render(request, 'documentos/pautas_pdf.html', {
            'turmas_agrupadas': turmas_final,
            'diretor': diretor,
            'data': data_hoje,
            'ano_lectivo':ano_letivo,
            'escola': escola_usuario,
        })
    
def pauta_coordenacao(request, trimestre):
    query = request.GET.get('q', '')
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto').last()

    reconfirmacoes = Reconfirmacao.objects.select_related(
        'aluno', 'turma', 'sala', 'classe', 'curso'
    ).filter(ano_letivo=ano_letivo)

    if query:
        reconfirmacoes = reconfirmacoes.filter(
            Q(aluno__nome_completo__icontains=query) |
            Q(aluno__numero_mecanografico__icontains=query) |
            Q(turma__nome__icontains=query)
        )

    turmas_agrupadas = {}
    disciplinas = []  

    for r in reconfirmacoes.order_by('classe__numero', 'turma__nome', 'aluno__nome_completo'):
        key = f"{r.classe.numero}ª Classe - Turma: {r.turma.nome} - Sala: {r.sala.nome if r.sala else '---'} - Curso: {r.curso.nome if r.curso else '---'} - Turno: {r.turno}"
        if key not in turmas_agrupadas:
            turmas_agrupadas[key] = []

        aluno = r.aluno
        classe_numero = r.classe.numero
        linha = {
            'aluno': aluno.nome_completo,
            'disciplinas': [],
            'estado': 'Aprovado'
        }

        tem_todas_notas = True
        disciplinas = DisciplinasClasse.objects.filter(classe=r.classe).select_related('disciplina')

        for disciplina in disciplinas:
            nota = Nota.objects.filter(aluno=aluno, disciplina=disciplina.disciplina, trimestre=trimestre).first()
            valor_nota = nota.valor if nota else None

            if valor_nota is None:
                tem_todas_notas = False
            else:
                if classe_numero < 7 and valor_nota < 5:
                    linha['estado'] = 'Reprovado'
                    
                elif classe_numero >= 7 and valor_nota < 10:
                    linha['estado'] = 'Reprovado'

            linha['disciplinas'].append({
                'nome': disciplina.disciplina.nome,
                'valor': valor_nota
            })

        if not tem_todas_notas:
            linha['estado'] = 'Pendente'

        turmas_agrupadas[key].append(linha)

    texto = ''
    if trimestre == 4:
        texto = 'Exame'

    perfil = request.user.perfil
    usuario = request.user
    if perfil == 'professor':
        usuario = request.user
        funcionario = Funcionario.objects.filter(usuario=usuario).first()

        coordenacoes = Coordenacao.objects.filter(funcionario=funcionario)

        turmas_filtradas = []
        disciplinas_filtradas = []

        for coord in coordenacoes:
            if coord.tipo == 'turma' and coord.turma:
                turmas_filtradas.append(coord.turma)
            elif coord.tipo == 'disciplina' and coord.disciplina:
                disciplinas_filtradas.append(coord.disciplina)

        # Filtra reconfirmações:
        if turmas_filtradas:
            reconfirmacoes = Reconfirmacao.objects.filter(
                turma__in=turmas_filtradas
            ).select_related('classe', 'turma', 'sala', 'curso', 'aluno')
        elif disciplinas_filtradas:
            reconfirmacoes = Reconfirmacao.objects.filter(
                aluno__nota__disciplina__in=disciplinas_filtradas
            ).select_related('classe', 'turma', 'sala', 'curso', 'aluno').distinct()
        else:
            reconfirmacoes = Reconfirmacao.objects.none()

        turmas_agrupadas = {}

        for r in reconfirmacoes.order_by('classe__numero', 'turma__nome'):
            key = f"{r.classe.numero}ª Classe - Turma: {r.turma.nome} - Sala: {r.sala.nome if r.sala else '---'} - Curso: {r.curso.nome if r.curso else '---'} - Turno: {r.turno}"
            if key not in turmas_agrupadas:
                turmas_agrupadas[key] = []

            aluno = r.aluno
            classe_numero = r.classe.numero
            linha = {
                'aluno': aluno.nome_completo,
                'disciplinas': [],
                'estado': 'Aprovado'
            }

            tem_todas_notas = True

            # Se for coordenador de disciplina, filtra apenas as disciplinas coordenadas
            if disciplinas_filtradas:
                disciplinas = DisciplinasClasse.objects.filter(
                    classe=r.classe,
                    disciplina__in=disciplinas_filtradas
                ).select_related('disciplina')
            else:
                disciplinas = DisciplinasClasse.objects.filter(
                    classe=r.classe
                ).select_related('disciplina')

            for disciplina in disciplinas:
                nota = Nota.objects.filter(aluno=aluno, disciplina=disciplina.disciplina, trimestre=trimestre).first()
                valor_nota = nota.valor if nota else None

                if valor_nota is None:
                    tem_todas_notas = False
                else:
                    if classe_numero < 7 and valor_nota < 5:
                        linha['estado'] = 'Reprovado'
                    elif classe_numero >= 7 and valor_nota < 10:
                        linha['estado'] = 'Reprovado'

                linha['disciplinas'].append({
                    'nome': disciplina.disciplina.nome,
                    'valor': valor_nota
                })

            if not tem_todas_notas:
                linha['estado'] = 'Pendente'

            turmas_agrupadas[key].append(linha)

        texto = 'Exame' if trimestre == 4 else ''
        usuario = request.user

        return render(request, 'documentos/pauta_coord_print.html', {
            'turmas_agrupadas': turmas_agrupadas,
            'search_query': query,
            'trimestre': trimestre,
            'disciplinas': disciplinas,
            'texto': texto,
            'usuario':usuario
        })
    else:
        return HttpResponse(
            """
            <html>
                <head>
                    <title>Erro 401 - Não Autorizado</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            background-color: #f8f9fa;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                        }
                        .error-box {
                            text-align: center;
                            padding: 40px;
                            border: 2px solid #dc3545;
                            border-radius: 12px;
                            background-color: #fff;
                            box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
                        }
                        h1 {
                            color: #dc3545;
                            font-size: 48px;
                            margin-bottom: 10px;
                        }
                        p {
                            font-size: 20px;
                            color: #333;
                        }
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h1>401</h1>
                        <p><strong>Perfil não autorizado</strong></p>
                        <p>Você não tem permissão para acessar esta página.</p>
                    </div>
                </body>
            </html>
            """,
            status=401
        )
 
def boletim_aluno(request, aluno_id, classe_id=None): 
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    # Buscar o aluno
    aluno = get_object_or_404(Aluno, id=aluno_id)
    
    # Se classe_id foi passado, usa ele, senão usa a classe do aluno
    if classe_id:
        classe = get_object_or_404(Classe, id=classe_id)
    else:
        classe = aluno.classe
    
    # Buscar o diretor geral (opcional)
    diretor = Funcionario.objects.filter(escolas=escola_usuario, funcao__icontains="diretor_geral").first()
    
    # Buscar o ano letivo aberto
    ano_letivo = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()
    
    # Dados adicionais do formulário (se houver)
    dados = {
        'nome_pai': request.POST.get('nome_pai') if request.method == 'POST' else None,
        'nome_mae': request.POST.get('nome_mae') if request.method == 'POST' else None,
        'naturalidade': request.POST.get('naturalidade') if request.method == 'POST' else None,
        'municipio': request.POST.get('municipio') if request.method == 'POST' else None,
        'provincia': request.POST.get('provincia') if request.method == 'POST' else None,
        'data_nascimento': request.POST.get('data_nascimento') if request.method == 'POST' else None,
        'bi': request.POST.get('bi') if request.method == 'POST' else None,
    }
    
    # Buscar notas do aluno para a classe específica
    notas = Nota.objects.filter(
        escola=escola_usuario,
        aluno=aluno,
        classe=classe
    ).select_related('disciplina').order_by('disciplina__nome', 'trimestre')
    
    # Estruturar dados do boletim
    boletim = {}
    disciplinas_com_notas = set()  # Para controlar quais disciplinas têm pelo menos uma nota
    
    # Agrupar notas por disciplina
    for nota in notas:
        disciplina_nome = nota.disciplina.nome
        boletim.setdefault(disciplina_nome, {'notas': {}, 'media': '--', 'situacao': 'Pendente'})
        boletim[disciplina_nome]['notas'][nota.trimestre] = nota.valor
        disciplinas_com_notas.add(disciplina_nome)
    
    # Calcular médias para cada disciplina
    for disciplina_nome, dados_disc in boletim.items():
        n = dados_disc['notas']
        
        # Verificar se tem todos os trimestres (1, 2, 3) para calcular média parcial
        trimestres_existentes = [t for t in [1, 2, 3] if t in n]
        
        if trimestres_existentes:
            # Calcular média dos trimestres existentes
            soma_trimestres = sum(n[t] for t in trimestres_existentes)
            media_trimestres = soma_trimestres / len(trimestres_existentes)
            
            # Verificar se tem nota de exame (trimestre 4)
            if 4 in n:
                # Com exame: (média trimestres * 0.4) + (exame * 0.6)
                media_final = (media_trimestres * Decimal('0.4')) + (n[4] * Decimal('0.6'))
                boletim[disciplina_nome]['media'] = float(
                    Decimal(media_final).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                )
            else:
                # Sem exame: usa apenas média dos trimestres
                boletim[disciplina_nome]['media'] = float(
                    Decimal(media_trimestres).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                )
            
            # Definir situação da disciplina
            if boletim[disciplina_nome]['media'] >= 5:
                boletim[disciplina_nome]['situacao'] = 'Apto(a)'
            else:
                boletim[disciplina_nome]['situacao'] = 'Reprovado'
        else:
            # Não tem nenhum trimestre
            boletim[disciplina_nome]['media'] = '--'
            boletim[disciplina_nome]['situacao'] = 'Pendente'
    
    # Adicionar disciplinas da classe que não têm notas registradas
    disciplinas_classe = DisciplinasClasse.objects.filter(escola=escola_usuario, classe=classe).select_related('disciplina')
    
    for dc in disciplinas_classe:
        disciplina_nome = dc.disciplina.nome
        if disciplina_nome not in boletim:
            boletim[disciplina_nome] = {
                'notas': {},
                'media': '--',
                'situacao': 'Pendente'
            }
    
    # Calcular faltas (ajuste conforme seu modelo)
    faltas_indisciplina = 0
    faltas_nao_comparencia = 0
    
    # Se existir modelo de faltas, buscar
    if hasattr(aluno, 'falta_set'):
        faltas_indisciplina = aluno.falta_set.filter(
            classe=classe,
            tipo='indisciplina'
        ).count()
        faltas_nao_comparencia = aluno.falta_set.filter(
            classe=classe,
            tipo='nao_comparencia'
        ).count()
    
    # Calcular média geral total
    medias_validas = [
        dados['media'] 
        for dados in boletim.values() 
        if dados['media'] != '--' and isinstance(dados['media'], (int, float))
    ]
    
    if medias_validas:
        media_geral_total = round(sum(medias_validas) / len(medias_validas), 1)
        
        # Verificar situações das disciplinas
        situacoes = [dados['situacao'] for dados in boletim.values() if dados['situacao'] != 'Pendente']
        
        if any(s == 'Reprovado' for s in situacoes):
            situacao_geral = 'Reprovado'
        elif not situacoes:
            situacao_geral = 'Pendente'
        else:
            situacao_geral = 'Apto(a)'
    else:
        media_geral_total = 0
        situacao_geral = 'Pendente'
    
    # Converter boletim para o formato esperado pelo template
    notas_por_disciplina = {}
    for disciplina_nome, dados_disc in boletim.items():
        notas = {
            'MT1': dados_disc['notas'].get(1),
            'MT2': dados_disc['notas'].get(2),
            'MT3': dados_disc['notas'].get(3),
            'MDF': dados_disc['notas'].get(4),
            'media_geral': dados_disc['media'] if dados_disc['media'] != '--' else None,
            'situacao': dados_disc['situacao']
        }
        notas_por_disciplina[disciplina_nome] = notas
    
    return render(request, 'documentos/boletim.html', {
        'aluno': aluno,
        'classe': classe,
        'sala': aluno.sala if hasattr(aluno, 'sala') else None,
        'ano_lectivo': ano_letivo,
        'notas_por_disciplina': notas_por_disciplina,
        'faltas_indisciplina': faltas_indisciplina,
        'faltas_nao_comparencia': faltas_nao_comparencia,
        'media_geral_total': media_geral_total,
        'situacao_geral': situacao_geral,
        'data_hoje': date.today(),
        'diretor': diretor,  # Adicionado para o template
        'dados_aluno': dados,  # Dados adicionais do aluno
        "escola": escola_usuario
    })

@login_required
def alunos_print(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
    diretor = Funcionario.objects.filter(funcao__icontains="diretor_geral", escolas=escola_usuario).first()

    query = request.GET.get('q', '')
    ano_letivo = ano_letivo  
    reconfirmacoes = Reconfirmacao.objects.select_related(
        'aluno', 'turma', 'sala', 'classe', 'curso'
    ).filter(ano_letivo=ano_letivo, estado='Adimplente', escola=escola_usuario)

    if query:
        reconfirmacoes = reconfirmacoes.filter(
            Q(aluno__nome_completo__icontains=query) |
            Q(aluno__numero_mecanografico__icontains=query) |
            Q(turma__nome__icontains=query) |
            Q(escola=escola_usuario)
        )


    # Organizar por classe > turma (ordem crescente)
    turmas_agrupadas = {}
    for r in reconfirmacoes.order_by('classe__numero', 'turma__nome', 'aluno__nome_completo'):
        key = f"{r.classe.numero}ª Classe - Turma: {r.turma.nome} - Sala: {r.sala.nome if r.sala else '---'} - Curso: {r.curso.nome if r.curso else '---'} - Turno: {r.turno}"
        if key not in turmas_agrupadas:
            turmas_agrupadas[key] = []
        turmas_agrupadas[key].append(r.aluno)


    return render(request, 'documentos/alunos_print.html', {
        'turmas_agrupadas': turmas_agrupadas,
        'search_query': query,
        'ano_letivo' : ano_letivo,
        'diretor': diretor, 
        'data': data_hoje, 
        'escola': escola_usuario,
    })
from reportlab.pdfbase.pdfmetrics import stringWidth

def quebrar_texto(texto, fonte, tamanho, largura_max):
    palavras = texto.split()
    linhas = []
    linha_atual = ""

    for palavra in palavras:
        teste = f"{linha_atual} {palavra}".strip()
        largura = stringWidth(teste, fonte, tamanho)

        if largura <= largura_max:
            linha_atual = teste
        else:
            if linha_atual:
                linhas.append(linha_atual)
            linha_atual = palavra

    if linha_atual:
        linhas.append(linha_atual)

    return linhas

@login_required
def cartao_estudante(request, aluno_id):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    aluno = get_object_or_404(Aluno, pk=aluno_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=cartao_estudante_{aluno.id}.pdf'

    # Tamanho do cartão (85,6mm x 54mm)
    width, height = portrait((54 * mm, 85.6 * mm))
    p = canvas.Canvas(response, pagesize=(width, height))

    # ========== Fundo do cartão ==========
    bg_path = os.path.join(settings.BASE_DIR, 'static', 'imgs', 'ChatGPT Image 21_08_2025, 03_14_47.png')
    if os.path.exists(bg_path):
        p.drawImage(bg_path, 0, 0, width=width, height=height)

    # ========== Cabeçalho institucional ==========
    # Logo da escola vindo do banco
    if escola_usuario.logotipo and os.path.exists(escola_usuario.logotipo.path):
        p.drawImage(
            escola_usuario.logotipo.path,
            3*mm,
            height - 18*mm,
            width=16*mm,
            height=16*mm,
            preserveAspectRatio=True,
            mask='auto'
        )
  
    p.setFillColor(colors.white)

    nome_escola = escola_usuario.nome

    fonte = "Helvetica-Bold"
    tamanho = 8

    # largura disponível (ajusta conforme teu layout)
    largura_max = width - 25*mm  

    linhas = quebrar_texto(nome_escola, fonte, tamanho, largura_max)

    y = height - 9*mm

    p.setFont(fonte, tamanho)

    for linha in linhas[:4]:  # limita a 2 linhas para não quebrar o layout
        p.drawString(20*mm, y, linha)
        y -= 3.5*mm  # espaço entre linhas

    # Localização (província + município)
    p.setFont("Helvetica", 6)
    p.drawString(
        20*mm, 
        height - 24*mm, 
        f"{escola_usuario.municipio} - {escola_usuario.provincia}"
    )

    # ========== Foto do aluno ==========
    if aluno.foto and os.path.exists(aluno.foto.path):
        # posição aproximada do centro superior
        foto_x = width/2 - 12*mm
        foto_y = height - 54*mm
        foto_w = 24*mm
        foto_h = 28*mm

        # Desenha a imagem
        p.drawImage(
            aluno.foto.path,
            foto_x,
            foto_y,
            width=foto_w,
            height=foto_h,
            preserveAspectRatio=True,
            mask='auto'
        )

        # Define cor e espessura da borda
        p.setStrokeColorRGB(0, 0, 0.9)   # azul
        p.setLineWidth(3)              # grossura da linha
        p.rect(foto_x, foto_y, foto_w, foto_h)  # desenha o retângulo em volta

    # ========== Dados do aluno ==========
    dados_x = 10 * mm
    dados_y = height - 60*mm
    p.setFont("Helvetica", 10)
    p.setFillColor(colors.blue)

    nome = aluno.nome_completo.strip().split()
    primeiro_ultimo = f"{nome[0]} {nome[-1]}"
    p.drawString(dados_x, dados_y, primeiro_ultimo)

    p.setFont("Helvetica", 7)
    p.setFillColor(colors.black)
    p.drawString(dados_x, dados_y-10,   f"N. Mec: {aluno.numero_mecanografico}")
    p.drawString(dados_x, dados_y-20, f"Classe: {'Iniciação' if aluno.turma.classe.numero == 0 else aluno.turma.classe}")

    # ========== Código de Barras ==========
    barcode_value = str(aluno.numero_mecanografico) 
    barcode = code128.Code128(barcode_value, barHeight=4*mm, barWidth=1)
    barcode_x = width/2 - 25*mm 
    barcode_y = 10*mm            
    barcode.drawOn(p, barcode_x, barcode_y)

    # Rodapé
    p.setFont("Helvetica-Oblique", 6)
    p.drawCentredString(width/2, 5*mm, "Este cartão é pessoal e intransferível.")

    p.showPage()
    p.save()
    return response

from django.utils.http import urlencode

@login_required
def processar_declaracao(request, id):
    aluno = get_object_or_404(Aluno, id=id)
    
    if request.method == 'POST':
        # Obter dados do formulário
        tipo_declaracao = request.POST.get('tipo_declaracao')
        finalidade = request.POST.get('finalidade')
        
        if not tipo_declaracao or not finalidade:
            messages.error(request, 'Por favor, preencha todos os campos.')
            return render(request, 'documentos/form_declaracao.html', {
                'aluno': aluno
            })
        
        # Codificar a finalidade para URL (usar URL encoding)
        # Remover espaços em excesso e codificar
        finalidade_limpa = ' '.join(finalidade.strip().split())
        finalidade_codificada = finalidade_limpa.replace(' ', '-').lower()
        
        # Redirecionar para a declaração apropriada com dois parâmetros
        if tipo_declaracao == 'sem_notas':
            return redirect('documentos:declaracao_sem_notas', 
                          aluno_id=aluno.id, 
                          finalidade=finalidade_codificada)
        elif tipo_declaracao == 'com_notas':
            return redirect('documentos:declaracao_com_notas', 
                          aluno_id=aluno.id, 
                          finalidade=finalidade_codificada)
    
    # Se for GET, mostrar o formulário
    return render(request, 'documentos/form_declaracao.html', {
        'aluno': aluno
    })

@login_required
def selecionar_classe_declaracao(request, aluno_id, finalidade):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    
    # Buscar classes que o aluno teve notas
    classes = Classe.objects.filter(
        nota__aluno=aluno
    ).distinct().order_by('numero')
    
    return render(request, 'documentos/selecionar_classe_declaracao.html', {
        'aluno': aluno,
        'classes': classes,
        'finalidade':finalidade
    })

@login_required
def gerar_declaracao_com_notas(request, aluno_id, classe_id, finalidade):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})

    aluno = get_object_or_404(Aluno, id=aluno_id)
    classe = get_object_or_404(Classe, id=classe_id)
    diretor = Funcionario.objects.filter(escolas=escola_usuario, funcao__icontains="Diretor Geral").first() 

    
    dados = {
        'nome_pai': request.POST.get('nome_pai'),
        'nome_mae': request.POST.get('nome_mae'),
        'naturalidade': request.POST.get('naturalidade'),
        'municipio': request.POST.get('municipio'),
        'provincia': request.POST.get('provincia'),
        'data_nascimento': request.POST.get('data_nascimento'),
        'bi': request.POST.get('bi'),
    }

    notas = Nota.objects.filter(
        escola=escola_usuario,
        aluno=aluno,
        classe=classe
    ).select_related('disciplina').order_by('disciplina__nome', 'trimestre')

    boletim = {}

    for nota in notas:
        d = nota.disciplina.nome
        boletim.setdefault(d, {'notas': {}, 'media': '--'})
        boletim[d]['notas'][nota.trimestre] = nota.valor

    for d, dados_disc in boletim.items():
        n = dados_disc['notas']
        if all(t in n for t in [1, 2, 3, 4]):
            media = ((n[1] + n[2] + n[3]) / 3) * Decimal('0.4') + n[4] * Decimal('0.6')
            boletim[d]['media'] = float(
                Decimal(media).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            )

    return render(request, 'documentos/declaracao_com_notas.html', {
        'aluno': aluno,
        'classe': classe,
        'boletim': boletim,
        'diretor': diretor,
        'finalidade':finalidade,
        **dados,
        'escola':escola_usuario
    })

@login_required
def declaracao_sem_notas(request, aluno_id, finalidade):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    aluno = get_object_or_404(Aluno, id=aluno_id)
    ultima_reconfirmacao = Reconfirmacao.objects.filter(escola=escola_usuario, aluno=aluno).order_by('-ano_letivo').first()

    curso = ultima_reconfirmacao.curso.nome if ultima_reconfirmacao and ultima_reconfirmacao.curso else '________________'
    turma = ultima_reconfirmacao.turma.nome if ultima_reconfirmacao and ultima_reconfirmacao.turma else '______'
    classe = f"{ultima_reconfirmacao.classe.numero}ª" if ultima_reconfirmacao and ultima_reconfirmacao.classe else '___ª'

    diretor = Funcionario.objects.filter(escolas=escola_usuario, funcao__icontains="Diretor Geral").first()
    print(diretor)
    ano_letivo = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()
    data_emissao = datetime.now().strftime('%d/%m/%Y')

    return render(request, 'documentos/declaracao_sem_notas.html', {
        'aluno': aluno,
        'reconfirmacao': ano_letivo,
        'curso':curso,
        'turma': turma,
        'classe': classe,
        'diretor': diretor, 
        'data_emissao': data_emissao,
        'finalidade':finalidade,
        'escola':escola_usuario
    })

@login_required
def certificado(request, id):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    aluno = get_object_or_404(Aluno, id=id)
    diretor = Funcionario.objects.filter(escolas=escola_usuario, funcao__icontains="Diretor Geral").first()

    # Buscar TODAS as notas do aluno
    notas = (
        Nota.objects
        .filter(escola=escola_usuario, aluno=aluno)
        .select_related('disciplina', 'classe', 'ano_lectivo')
        .order_by('disciplina__nome', 'classe__numero', 'trimestre')
    )
    ano_conclusao = ""
    if request.method == "POST":
        ano_conclusao = request.POST.get("ano_conclusao")
        emissao_bi = request.POST.get("emissao_bi")
        n_processo = request.POST.get("n_processo")
        funcionario_conferiu = request.POST.get("funcionario_conferiu")
        tipo_certificado_template = request.POST.get("tipo_certificado")

    if not notas.exists():
        return render(request, 'documentos/sem_certificado.html')

    # =============================
    # IDENTIFICAR ANOS LETIVOS ÚNICOS (fazemos isto independente do método)
    # =============================
    anos_letivos = {}
    for nota in notas:
        ano_id = nota.ano_lectivo.id
        if ano_id not in anos_letivos:
            anos_letivos[ano_id] = {
                'ano': nota.ano_lectivo,
                'classes': {}  # classe.numero -> (classe, ano_lectivo)
            }
        # Associar classe ao ano letivo
        anos_letivos[ano_id]['classes'][nota.classe.numero] = {
            'classe': nota.classe,
            'ano_lectivo': nota.ano_lectivo
        }

    # Ordenar anos letivos por ID (ou outro atributo disponível)
    anos_ordenados = sorted(
        anos_letivos.values(), 
        key=lambda x: x['ano'].id  # Ordena por ID do ano letivo
    )

    # =============================
    # PREPARAR CABEÇALHOS DINÂMICOS (fazemos isto independente do método)
    # =============================
    cabecalhos = []
    for ano_info in anos_ordenados:
        ano = ano_info['ano']
        # Ordenar classes dentro do ano
        classes_ordenadas = sorted(ano_info['classes'].items(), key=lambda x: x[0])
        
        for classe_num, classe_data in classes_ordenadas:
            # Verificar quais atributos o AnoLectivo realmente tem
            ano_texto = ""
            if hasattr(ano, 'ano'):
                ano_texto = str(ano.ano)
            elif hasattr(ano, 'descricao'):
                ano_texto = ano.descricao
            else:
                ano_texto = str(ano.id)  # Fallback para ID
            
            cabecalho = {
                'classe_num': classe_num,
                'ano_lectivo': ano,
                'chave': f"{classe_num}_{ano.id}",
                'texto': f"{classe_num}ª {ano_texto}"
            }
            cabecalhos.append(cabecalho)

    # Se for GET, apenas mostrar o formulário
    if request.method == "GET":
        return render(request, 'documentos/form_certificado.html', {
            'aluno': aluno,
            'cabecalhos': cabecalhos,
        })

    # Se for POST, processar o certificado
    if request.method == "POST":
        # Dados pessoais
        nome_pai = request.POST.get("nome_pai")
        nome_mae = request.POST.get("nome_mae")
        naturalidade = request.POST.get("naturalidade")
        municipio = request.POST.get("municipio")
        provincia = request.POST.get("provincia")
        data_nascimento = request.POST.get("data_nascimento")
        bi = request.POST.get("bi")

        # =============================
        # AGRUPAR NOTAS POR DISCIPLINA E ANO/CLASSE
        # =============================
        disciplinas_dict = {}
        
        for nota in notas:
            d_id = nota.disciplina.id
            classe_num = nota.classe.numero
            ano_id = nota.ano_lectivo.id
            
            if d_id not in disciplinas_dict:
                disciplinas_dict[d_id] = {
                    'nome': nota.disciplina.nome,
                    'notas_por_ano': {}  # ano_id -> {classe_num: {notas: {1: None, ...}}}
                }
            
            # Inicializar estrutura para este ano letivo
            if ano_id not in disciplinas_dict[d_id]['notas_por_ano']:
                disciplinas_dict[d_id]['notas_por_ano'][ano_id] = {}
            
            # Inicializar estrutura para esta classe
            if classe_num not in disciplinas_dict[d_id]['notas_por_ano'][ano_id]:
                disciplinas_dict[d_id]['notas_por_ano'][ano_id][classe_num] = {
                    'notas': {1: None, 2: None, 3: None, 4: None},
                    'classe': nota.classe,
                    'ano_lectivo': nota.ano_lectivo
                }
            
            # Armazenar nota
            disciplinas_dict[d_id]['notas_por_ano'][ano_id][classe_num]['notas'][nota.trimestre] = nota.valor

        # =============================
        # FUNÇÕES DE CÁLCULO
        # =============================
        def calcular_media_final(notas_dict):
            """Calcula a média final com base nas 3 notas trimestrais + exame"""
            notas = notas_dict
            
            # Verificar se tem pelo menos os 3 trimestres
            if notas[1] is not None and notas[2] is not None and notas[3] is not None:
                media_trimestral = (notas[1] + notas[2] + notas[3]) / Decimal('3.0')
                
                if notas[4] is not None:  # exame
                    media = (media_trimestral * Decimal('0.4')) + (notas[4] * Decimal('0.6'))
                else:
                    media = media_trimestral
                
                return Decimal(media).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            return None

        def formatar_notas_classe(notas_classe):
            """Formata as notas para exibição: N1/N2/N3/Exame"""
            notas = notas_classe['notas']
            partes = []
            
            # Notas trimestrais
            for trim in [1, 2, 3]:
                if notas[trim] is not None:
                    partes.append(str(notas[trim]))
                else:
                    partes.append("-")
            
            # Exame (se houver)
            if notas[4] is not None:
                partes.append(str(notas[4]))
            
            return "/".join(partes)

        def numero_por_extenso(valor):
            mapa = {
                0: "Zero", 1: "Um", 2: "Dois", 3: "Três", 4: "Quatro",
                5: "Cinco", 6: "Seis", 7: "Sete", 8: "Oito", 9: "Nove",
                10: "Dez", 11: "Onze", 12: "Doze", 13: "Treze",
                14: "Catorze", 15: "Quinze", 16: "Dezasseis",
                17: "Dezassete", 18: "Dezoito", 19: "Dezanove", 20: "Vinte"
            }
            return mapa.get(int(valor), str(valor))

        # =============================
        # PREPARAR DADOS PARA TEMPLATE
        # =============================
        todas_disciplinas = []
        todas_medias_finais = []
        
        for dados in disciplinas_dict.values():
            # Para cada disciplina, criar uma lista ordenada de notas
            # que corresponda à ordem dos cabeçalhos
            notas_ordenadas = []
            
            for cab in cabecalhos:
                chave = cab['chave']
                # Encontrar as notas para esta combinação classe/ano
                encontrou = False
                
                # Procurar nos dados da disciplina
                for ano_id, classes_data in dados['notas_por_ano'].items():
                    for classe_num, classe_data in classes_data.items():
                        if f"{classe_num}_{ano_id}" == chave:
                            notas_ordenadas.append({
                                'notas_formatadas': formatar_notas_classe(classe_data),
                                'media': calcular_media_final(classe_data['notas']),
                                'classe_num': classe_num,
                                'ano_lectivo': classe_data['ano_lectivo']
                            })
                            encontrou = True
                            break
                    if encontrou:
                        break
                
                if not encontrou:
                    notas_ordenadas.append(None)
            
            # Calcular média final da disciplina (média de todas as classes/anos)
            medias_validas = []
            for ano_id, classes_data in dados['notas_por_ano'].items():
                for classe_num, classe_data in classes_data.items():
                    media = calcular_media_final(classe_data['notas'])
                    if media is not None:
                        medias_validas.append(media)
            
            if medias_validas:
                media_final_disciplina = sum(medias_validas) / len(medias_validas)
                media_final_disciplina = media_final_disciplina.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                todas_medias_finais.append(media_final_disciplina)
                
                linha = {
                    'nome': dados['nome'],
                    'notas_ordenadas': notas_ordenadas,
                    'media_final': media_final_disciplina,
                    'media_extenso': numero_por_extenso(media_final_disciplina),
                }
                todas_disciplinas.append(linha)

        # Ordenar disciplinas por nome
        todas_disciplinas = sorted(todas_disciplinas, key=lambda x: x['nome'])

        # =============================
        # MÉDIA GERAL DO CURSO
        # =============================
        media_geral = None
        media_geral_extenso = None
        
        if todas_medias_finais:
            media_geral = sum(todas_medias_finais) / len(todas_medias_finais)
            media_geral = media_geral.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            media_geral_extenso = numero_por_extenso(media_geral)
        context = {    
            'aluno': aluno,
            'diretor': diretor,
            'ano_conclusao':ano_conclusao,  
            'emissao_bi': emissao_bi,
            'n_processo': n_processo,
            'funcionario_conferiu': funcionario_conferiu,
            
            'todas_disciplinas': todas_disciplinas,
            'cabecalhos': cabecalhos,
            
            'media_geral': media_geral,
            'media_geral_extenso': media_geral_extenso,
            
            'nome_pai': nome_pai,
            'nome_mae': nome_mae,
            'naturalidade': naturalidade,
            'municipio': municipio,
            'provincia': provincia,
            'data_nascimento': data_nascimento,
            'bi': bi,
            'escola':escola_usuario
        }
        if tipo_certificado_template == "1":
           return render(request, 'documentos/certificado-primario.html', context)
        elif tipo_certificado_template == "2":
           return render(request, 'documentos/certificado_secundario.html', context)
        elif tipo_certificado_template == "3":
           return render(request, 'documentos/certificado-puniv.html', context)
        elif tipo_certificado_template == "4":
           return render(request, 'documentos/certificado-secundario-pedagogico.html', context)
        elif tipo_certificado_template == "5":
           return render(request, 'documentos/certificado-secundario-tecnico-profissional.html', context)
       
        return render(request, 'documentos/certificado-puniv.html', context)
    
@login_required
def relatorio_financeiro_pdf(request):
    """View específica para gerar o relatório impresso"""
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola inválida.')
    
    # ano letivo atual ou escolhido no select
    ano_lectivo = request.GET.get("ano_lectivo")
    if not ano_lectivo:
        ano_lectivo = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()
    
    # Filtra os pagamentos (RECEITAS)
    pagamentos = Pagamento.objects.filter(escola=escola_usuario, ano_lectivo=ano_lectivo)
    
    # Filtra as despesas (GASTOS)
    despesas = Despesa.objects.filter(escola=escola_usuario, ano_lectivo=ano_lectivo)
    
    # Agrupamento por tipo de serviço (RECEITAS)
    por_servico = pagamentos.values("tipoServico__nome").annotate(
        total=Sum("valor"),
        quantidade=Count("id")
    ).order_by("-total")

    # Agrupamento por categoria (DESPESAS)
    despesas_por_categoria = despesas.values("categoria").annotate(
        total=Sum("valor"),
        quantidade=Count("id"),
        total_pago=Sum('valor', filter=Q(status='pago')),
        total_pendente=Sum('valor', filter=Q(status='pendente'))
    ).order_by("-total")

    # Totais RECEITAS
    total_receitas = pagamentos.aggregate(total=Sum("valor"))["total"] or 0
    total_pagamentos = pagamentos.count()

    # Totais DESPESAS
    total_despesas = despesas.aggregate(total=Sum("valor"))["total"] or 0
    total_despesas_pagas = despesas.filter(status='pago').aggregate(total=Sum("valor"))["total"] or 0
    total_despesas_pendentes = despesas.filter(status='pendente').aggregate(total=Sum("valor"))["total"] or 0
    
    # Saldo em caixa
    saldo_caixa = total_receitas - total_despesas_pagas

    # --- AGRUPAMENTO MENSAL RECEITAS ---
    pagamentos_mensais = (
        Pagamento.objects
        .annotate(mes_pagamento=ExtractMonth("data_pagamento"))
        .values("mes_pagamento")
        .annotate(total=Sum("valor"))
        .filter(escola=escola_usuario, ano_lectivo=ano_lectivo)
        .order_by("mes_pagamento")
    )

    # --- AGRUPAMENTO MENSAL DESPESAS ---
    despesas_mensais = (
        Despesa.objects
        .annotate(mes_despesa=ExtractMonth("data_despesa"))
        .values("mes_despesa")
        .annotate(total=Sum("valor"))
        .filter(escola=escola_usuario, ano_lectivo=ano_lectivo)
        .order_by("mes_despesa")
    )

    # Prepara dados mensais para gráfico
    meses_labels = [calendar.month_abbr[i] for i in range(1, 13)]
    
    # Valores de receitas por mês
    receitas_mensais = [0] * 12
    for item in pagamentos_mensais:
        mes = item["mes_pagamento"]
        if mes:
            receitas_mensais[mes - 1] = float(item["total"])

    # Valores de despesas por mês
    despesas_mensais_vals = [0] * 12
    for item in despesas_mensais:
        mes = item["mes_despesa"]
        if mes:
            despesas_mensais_vals[mes - 1] = float(item["total"])

    # Últimas despesas (para tabela)
    ultimas_despesas = despesas.order_by('-data_despesa')[:10]

    # Estatísticas adicionais
    media_receita_mensal = total_receitas / 12 if total_receitas > 0 else 0
    media_despesa_mensal = total_despesas / 12 if total_despesas > 0 else 0
    percentual_despesas = (total_despesas_pagas / total_receitas * 100) if total_receitas > 0 else 0

    # Datas para o relatório
    from datetime import date
    data_inicio = date(date.today().year, 1, 1)
    data_fim = date.today()
    
    context = {
        "ano_lectivo": ano_lectivo,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "por_servico": por_servico,
        "total_receitas": total_receitas,
        "total_pagamentos": total_pagamentos,
        "total_despesas": total_despesas,
        "total_despesas_pagas": total_despesas_pagas,
        "total_despesas_pendentes": total_despesas_pendentes,
        "saldo_caixa": saldo_caixa,
        "despesas_por_categoria": despesas_por_categoria,
        "ultimas_despesas": ultimas_despesas,
        "meses_labels": meses_labels,
        "receitas_mensais": receitas_mensais,
        "despesas_mensais": despesas_mensais_vals,
        "media_receita_mensal": media_receita_mensal,
        "media_despesa_mensal": media_despesa_mensal,
        "percentual_despesas": percentual_despesas,
        "categoria_choices": Despesa.CATEGORIA_CHOICES,
        "director_geral": Funcionario.objects.filter(escolas=escola_usuario, funcao__icontains='diretor_geral').first(),
        "director_admin": Funcionario.objects.filter(escolas=escola_usuario, funcao__icontains='diretor_admin').first(),
        'escola': escola_usuario,
    }

    return render(request, "documentos/relatorio_financeiro.html", context)

@login_required
def relatorio_pedagogico(request):
    """
    View para gerar o relatório pedagógico completo
    Versão para visualização web e impressão
    """
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola inválida.')

    # Obter parâmetros da requisição
    ano_lectivo = request.GET.get("ano_lectivo")
    
    # Lista de anos letivos disponíveis
    anos_lectivos = AnoLectivo.objects.filter(escola=escola_usuario).values_list('ano', flat=True)
    if not ano_lectivo:
        ano_lectivo_obj = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').first()
        ano_lectivo = ano_lectivo_obj.ano if ano_lectivo_obj else None
    
    # ============ ESTATÍSTICAS GERAIS ============
    
    # Totais gerais
    total_alunos = Aluno.objects.filter(escola=escola_usuario).count()
    total_professores = Funcionario.objects.filter(escolas=escola_usuario, funcao__icontains='professor').count()
    total_funcionarios = Funcionario.objects.filter(escolas=escola_usuario).count()
    total_turmas = Turma.objects.filter(escola=escola_usuario, ano_letivo=ano_lectivo).count()
    total_disciplinas = Disciplina.objects.filter(escola=escola_usuario).count()
    
    # Alunos por gênero
    alunos_masculino = Aluno.objects.filter(escola=escola_usuario, genero='M').count()
    alunos_feminino = Aluno.objects.filter(escola=escola_usuario, genero='F').count()
    
    # Professores por gênero
    professores_masculino = Funcionario.objects.filter(
        escolas=escola_usuario,
        funcao__icontains='professor', genero='M'
    ).count()
    professores_feminino = Funcionario.objects.filter(
        escolas=escola_usuario,
        funcao__icontains='professor', genero='F'
    ).count()
    
    # ============ DADOS DE MATRÍCULAS ============
    
    # Alunos por turma (para o ano letivo selecionado)
    alunos_por_turma = Turma.objects.filter(ano_letivo=ano_lectivo).annotate(
        quantidade_alunos=Count('aluno')
    ).order_by('-quantidade_alunos')
    
    total_alunos_ano = Aluno.objects.filter(escola=escola_usuario, turma__ano_letivo=ano_lectivo).count()
    
    # Alunos por classe
    alunos_por_classe = []
    classes = Classe.objects.filter(escola=escola_usuario).order_by('numero')

    # Preparar dados para os gráficos
    labels_classes = []
    dados_classes = []

    for classe in classes:
        quantidade = Aluno.objects.filter(
            escola=escola_usuario,
            turma__ano_letivo=ano_lectivo,
            turma__classe=classe
        ).count()
        
        if quantidade > 0:
            percentual = (quantidade / total_alunos_ano * 100) if total_alunos_ano > 0 else 0
            alunos_por_classe.append({
                'classe': classe,
                'classe_numero': classe.numero,
                'classe_designacao': classe.designacao,
                'quantidade': quantidade,
                'percentual': percentual
            })
            
            labels_classes.append(f"{classe.numero}ª")
            dados_classes.append(quantidade)

    # Alunos por turno
    alunos_por_turno = []
    for turno in ['Manhã', 'Tarde', 'Noite']:
        quantidade = Aluno.objects.filter(
            escola=escola_usuario,
            turma__ano_letivo=ano_lectivo,
            turno=turno
        ).count()
        percentual = (quantidade / total_alunos_ano * 100) if total_alunos_ano > 0 else 0
        alunos_por_turno.append({
            'turno': turno,
            'quantidade': quantidade,
            'percentual': percentual
        })
    
    # Alunos por curso
    alunos_por_curso = []
    cursos = Curso.objects.filter(escola=escola_usuario)
    for curso in cursos:
        quantidade = Aluno.objects.filter(
            escola=escola_usuario,
            turma__ano_letivo=ano_lectivo,
            curso=curso
        ).count()
        if quantidade > 0:
            percentual = (quantidade / total_alunos_ano * 100) if total_alunos_ano > 0 else 0
            alunos_por_curso.append({
                'curso': curso,
                'quantidade': quantidade,
                'percentual': percentual
            })
    
    # ============ DADOS DE DESEMPENHO ACADÊMICO ============
    
    # Médias por disciplina (baseado nas notas)
    medias_disciplinas = []
    disciplinas = Disciplina.objects.filter(escola=escola_usuario)[:10]  # Top 10 disciplinas
    
    for disciplina in disciplinas:
        notas = Nota.objects.filter(
            escola=escola_usuario,
            disciplina=disciplina,
            ano_lectivo__ano=ano_lectivo,
            trimestre__in=[1, 2, 3]
        )
        
        if notas.exists():
            media_geral = notas.aggregate(Avg('valor'))['valor__avg'] or 0
            
            # Alunos por faixa de nota
            alunos_aprovados = notas.filter(valor__gte=10).values('aluno').distinct().count()
            alunos_reprovados = notas.filter(valor__lt=10).values('aluno').distinct().count()
            total_alunos_disciplina = alunos_aprovados + alunos_reprovados
            
            medias_disciplinas.append({
                'disciplina': disciplina,
                'media_geral': media_geral,
                'alunos_aprovados': alunos_aprovados,
                'alunos_reprovados': alunos_reprovados,
                'total_alunos': total_alunos_disciplina,
                'taxa_aprovacao': (alunos_aprovados / total_alunos_disciplina * 100) if total_alunos_disciplina > 0 else 0
            })
    
    # Ordenar por média geral
    medias_disciplinas = sorted(medias_disciplinas, key=lambda x: x['media_geral'], reverse=True)
    
    # Desempenho por classe
    desempenho_classes = []
    for classe in classes:
        alunos_classe = Aluno.objects.filter(
            escola=escola_usuario,
            turma__ano_letivo=ano_lectivo,
            turma__classe=classe
        )
        
        if alunos_classe.exists():
            # Calcular média geral da classe
            notas_classe = Nota.objects.filter(
                escola=escola_usuario,
                aluno__in=alunos_classe,
                ano_lectivo__ano=ano_lectivo,
                trimestre__in=[1, 2, 3]
            )
            
            media_classe = notas_classe.aggregate(Avg('valor'))['valor__avg'] or 0
            
            desempenho_classes.append({
                'classe': classe,
                'media_geral': media_classe,
                'total_alunos': alunos_classe.count()
            })
    
    # ============ DADOS DE FREQUÊNCIA (baseado em reconfirmações) ============
    
    # Status dos alunos (Adimplente/Inadimplente)
    status_alunos = Reconfirmacao.objects.filter(
        escola=escola_usuario,
        ano_letivo=ano_lectivo
    ).values('estado').annotate(
        quantidade=Count('aluno', distinct=True)
    )
    
    alunos_adimplentes = 0
    alunos_inadimplentes = 0
    
    for status in status_alunos:
        if status['estado'] == 'Adimplente':
            alunos_adimplentes = status['quantidade']
        elif status['estado'] == 'Inadimplente':
            alunos_inadimplentes = status['quantidade']
    
    # Status de classe (Aprovado/Reprovado/Pendente)
    status_classes = Reconfirmacao.objects.filter(
        escola=escola_usuario,
        ano_letivo=ano_lectivo
    ).values('estadoClasse').annotate(
        quantidade=Count('aluno', distinct=True)
    )
    
    aprovados = 0
    reprovados = 0
    pendentes = 0
    
    for status in status_classes:
        if status['estadoClasse'] == 'Aprovado':
            aprovados = status['quantidade']
        elif status['estadoClasse'] == 'Reprovado':
            reprovados = status['quantidade']
        elif status['estadoClasse'] == 'Pendente':
            pendentes = status['quantidade']
    
    total_avaliados = aprovados + reprovados + pendentes
    taxa_aprovacao_geral = (aprovados / total_avaliados * 100) if total_avaliados > 0 else 0
    
    # ============ DADOS DE DOCENTES ============
    
    # Professores por disciplina
    professores_disciplina = ProfessorVinculo.objects.filter(
        escola=escola_usuario,
        turma__ano_letivo=ano_lectivo
    ).values(
        'disciplina__nome', 'disciplina__id'
    ).annotate(
        quantidade=Count('professor', distinct=True),
        turmas=Count('turma', distinct=True)
    ).order_by('-quantidade')
    
    # Média de alunos por professor
    total_vinculos = ProfessorVinculo.objects.filter(escola=escola_usuario, turma__ano_letivo=ano_lectivo).count()
    media_alunos_professor = total_alunos_ano / total_vinculos if total_vinculos > 0 else 0
    
    # Coordenações
    coordenacoes_por_tipo = Coordenacao.objects.filter(escola=escola_usuario).values('tipo').annotate(
        quantidade=Count('id')
    )
    
    # ============ DADOS DE MONOGRAFIAS ============
    
    # Monografias por estado
    monografias_estado = Monografia.objects.filter(escola=escola_usuario).values('estado').annotate(
        quantidade=Count('id')
    )
    
    total_monografias = Monografia.objects.filter(escola=escola_usuario).count()
    
    # Média de notas das monografias
    media_notas_monografias = Avaliacao.objects.filter(
        escola=escola_usuario,
        nota__isnull=False
    ).aggregate(Avg('nota'))['nota__avg'] or 0
    
    # ============ DADOS PARA GRÁFICOS ============
    
    # Dados para gráfico de evolução de matrículas (últimos 5 anos)
    anos_evolucao = []
    matriculas_evolucao = []
    
    # Obter anos letivos ordenados
    anos_ordenados = AnoLectivo.objects.filter(escola=escola_usuario).order_by('-ano')[:5]
    for ano in reversed(anos_ordenados):
        anos_evolucao.append(ano.ano)
        quantidade = Aluno.objects.filter(escola=escola_usuario, turma__ano_letivo=ano.ano).count()
        matriculas_evolucao.append(quantidade)
    
    # Dados para gráfico de distribuição por classe
    labels_classes = [item['classe'].numero for item in alunos_por_classe]
    dados_classes = [item['quantidade'] for item in alunos_por_classe]
    
    # Dados para gráfico de desempenho por disciplina
    labels_disciplinas = [item['disciplina'].nome[:15] for item in medias_disciplinas[:8]]
    dados_disciplinas = [float(item['media_geral']) for item in medias_disciplinas[:8]]
    
    # Dados para gráfico de status dos alunos
    labels_status = ['Adimplentes', 'Inadimplentes']
    dados_status = [alunos_adimplentes, alunos_inadimplentes]
    cores_status = ['#28a745', '#dc3545']
    
    # Dados para gráfico de aprovação/reprovação
    labels_aprovacao = ['Aprovados', 'Reprovados', 'Pendentes']
    dados_aprovacao = [aprovados, reprovados, pendentes]
    cores_aprovacao = ['#28a745', '#dc3545', '#ffc107']
    
    # ============ ÚLTIMOS REGISTROS ============
    
    # Últimas notas lançadas
    ultimas_notas = Nota.objects.filter(escola=escola_usuario).select_related(
        'aluno', 'disciplina', 'ano_lectivo'
    ).order_by('-id')[:10]
    
    # Últimos alunos matriculados
    ultimos_alunos = Aluno.objects.filter(escola=escola_usuario).select_related(
        'turma', 'classe', 'curso'
    ).order_by('-id')[:10]
    
    # Últimas monografias submetidas
    ultimas_monografias = Monografia.objects.filter(escola=escola_usuario).order_by('-data_submissao')[:5]
    
    # ============ DIRETORES E COORDENADORES ============
    # Buscar diretores e coordenadores (ajuste conforme sua estrutura)
    diretor_pedagogico = Funcionario.objects.filter(
        escolas=escola_usuario,
        funcao__icontains='diretor pedagogico'
    ).first()
    
    coordenador = Funcionario.objects.filter(
        escolas=escola_usuario,
        funcao__icontains='coordenador'
    ).first()
    
    perfil = request.user.perfil
    usuario = request.user
    
    context = {
        # Filtros
        'ano_lectivo': ano_lectivo,
        'anos_lectivos_disponiveis': anos_lectivos,
        'usuario': usuario,
        
        # Estatísticas gerais
        'total_alunos': total_alunos,
        'total_professores': total_professores,
        'total_funcionarios': total_funcionarios,
        'total_turmas': total_turmas,
        'total_disciplinas': total_disciplinas,
        
        # Gênero
        'alunos_masculino': alunos_masculino,
        'alunos_feminino': alunos_feminino,
        'professores_masculino': professores_masculino,
        'professores_feminino': professores_feminino,
        
        # Alunos por categoria
        'alunos_por_turma': alunos_por_turma,
        'alunos_por_classe': alunos_por_classe,
        'alunos_por_turno': alunos_por_turno,
        'alunos_por_curso': alunos_por_curso,
        'total_alunos_ano': total_alunos_ano,
        
        # Desempenho acadêmico
        'medias_disciplinas': medias_disciplinas,
        'desempenho_classes': desempenho_classes,
        
        # Status
        'alunos_adimplentes': alunos_adimplentes,
        'alunos_inadimplentes': alunos_inadimplentes,
        'aprovados': aprovados,
        'reprovados': reprovados,
        'pendentes': pendentes,
        'taxa_aprovacao_geral': taxa_aprovacao_geral,
        'total_avaliados': total_avaliados,
        
        # Docentes
        'professores_disciplina': professores_disciplina,
        'media_alunos_professor': media_alunos_professor,
        'coordenacoes_por_tipo': coordenacoes_por_tipo,
        
        # Monografias
        'monografias_estado': monografias_estado,
        'total_monografias': total_monografias,
        'media_notas_monografias': media_notas_monografias,
        
        # Dados para gráficos
        'anos_evolucao': anos_evolucao,
        'matriculas_evolucao': matriculas_evolucao,
        'labels_classes': labels_classes,
        'dados_classes': dados_classes,
        'labels_disciplinas': labels_disciplinas,
        'dados_disciplinas': dados_disciplinas,
        'labels_status': labels_status,
        'dados_status': dados_status,
        'cores_status': cores_status,
        'labels_aprovacao': labels_aprovacao,
        'dados_aprovacao': dados_aprovacao,
        'cores_aprovacao': cores_aprovacao,
        
        # Últimos registros
        'ultimas_notas': ultimas_notas,
        'ultimos_alunos': ultimos_alunos,
        'ultimas_monografias': ultimas_monografias,
        
        # Diretores e coordenadores
        'diretor_pedagogico': diretor_pedagogico,
        'coordenador': coordenador,
        'escola': escola_usuario,
    }
    
    return render(request, 'documentos/relatorio_pedagogico.html', context)


@login_required
def relatorio_pedagogico_pdf(request):
    """
    View para gerar PDF do relatório pedagógico
    (Opcional - se quiser gerar PDF diretamente)
    """
    import io
    from xhtml2pdf import pisa
    from django.template.loader import get_template
    
    # Obter parâmetros
    ano_lectivo = request.GET.get("ano_lectivo")
    
    # Reutilizar a lógica da view principal
    # (Aqui você pode chamar a função que prepara os dados ou copiar a lógica)
    # Para simplificar, vamos redirecionar para a view de impressão e converter para PDF
    
    # Preparar context (pode copiar a mesma lógica da view principal)
    # ... (código de preparação dos dados igual ao da view principal)
    
    # Usar template de impressão
    template_path = 'documentos/relatorio_pedagogico_print.html'
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_pedagogico_{ano_lectivo}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    # Criar PDF
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response.write(result.getvalue())
        return response
    
    return HttpResponse('Erro ao gerar PDF', status=400)

@login_required
def alunos_inadimpletes(request):
    from django.utils import timezone
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    # Filtrar apenas alunos com estado = Inadimplente
    inadimplentes = Reconfirmacao.objects.filter(estado="Inadimplente", escola=escola_usuario).select_related(
        "aluno", "turma", "classe", "curso", "sala"
    ).order_by("aluno__nome_completo")

    ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()

    # Diretor (se for fixo ou do request.user)
    diretor = request.user  # ou um objeto específico

    context = {
        "alunos_inadimplentes": inadimplentes,
        "ano_letivo": ano_letivo,
        "diretor": diretor,
        "data": timezone.now(),
        'escola':escola_usuario,
    }
    return render(request, "documentos/alunos-inadimplentes.html", context)

@login_required
def gerar_ata_prova(request):
    from django.utils import timezone
    escola_id_sessao = request.session.get('escola_atual_id')

    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()

    if request.method == "POST":
        turma_id = request.POST.get("turma_id") 
        epoca = request.POST.get("epoca")
        disciplina = request.POST.get("disciplina")
        professor = request.POST.get("professor")

        turma = Turma.objects.select_related("classe", "curso").get(id=turma_id, escola=escola_usuario)
    
        alunos = Aluno.objects.filter(turma=turma, escola=escola_usuario).order_by("nome_completo")

        context = {
            "turma": turma,
            "professor": professor,
            "alunos": alunos,
            "data": timezone.now(),
            "ano_letivo": ano_letivo,
            "epoca":epoca,
            "disciplina":disciplina,
            'escola': escola_usuario
        }
        return render(request, "documentos/ata-prova.html", context)
    
def estatisticas_faltas(request):
    escola_usuario = request.session.get('escola_atual_id')
    ano_lectivo_id = request.GET.get('ano_lectivo')
    mes = request.GET.get('mes')

    filtros = {}
    if ano_lectivo_id:
        filtros['ano_lectivo_id'] = ano_lectivo_id
    if mes and mes.isdigit():
        filtros['mes'] = int(mes)

    total_faltas = FaltaFuncionario.objects.filter(**filtros, escola=escola_usuario,).count()

    desconto = DescontoFalta.objects.filter(escola=escola_usuario).first()
    valor_desconto = desconto.valor_desconto if desconto else Decimal('0.00')
    desconto_total = Decimal(total_faltas) * valor_desconto

    faltas_por_funcionario = (
        FaltaFuncionario.objects.filter(**filtros, escola=escola_usuario,)
        .values('funcionario_id', 'funcionario__nome')
        .annotate(total_faltas=Count('id'))
        .order_by('-total_faltas')
    )

    return JsonResponse({
        'total_faltas': total_faltas,
        'desconto_total': float(desconto_total),
        'faltas_por_funcionario': list(faltas_por_funcionario)
    })

def faltas_funcionario(request, funcionario_id):
    escola_usuario = request.session.get('escola_atual_id')
    ano_lectivo_id = request.GET.get('ano_lectivo')

    funcionario = get_object_or_404(Funcionario, id=funcionario_id, escolas=escola_usuario)

    faltas = FaltaFuncionario.objects.filter(funcionario=funcionario, escola=escola_usuario)

    if ano_lectivo_id:
        faltas = faltas.filter(ano_lectivo_id=ano_lectivo_id, escolas=escola_usuario)

    faltas_data = faltas.order_by(
        '-ano_lectivo__ano',
        '-mes',
        '-dia'
    ).values(
        'id',
        'dia',
        'mes',
        ano_lectivo_nome=F('ano_lectivo__ano'),
        registrado_por_nome=F('registrado_por__username')
    )
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    faltas_list = []
    for falta in faltas_data:
        falta['mes_nome'] = meses[falta['mes'] - 1] if 1 <= falta['mes'] <= 12 else ''
        faltas_list.append(falta)

    return JsonResponse({
        'funcionario': {
            'id': funcionario.id,
            'nome': funcionario.nome,
            'funcao': funcionario.funcao,
        },
        'faltas': faltas_list
    })

def registrar_falta_funcionario(request):
    escola_usuario = request.session.get('escola_atual_id')

    escola_id = request.session.get('escola_atual_id')

    if not escola_id:
        return JsonResponse({'success': False, 'message': 'Escola não selecionada.'})

    try:
        escola_usuario = Escola.objects.get(id=escola_id)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido.'}, status=405)

    try:
        funcionario_id = request.POST.get('funcionario_id', '').strip()
        mes_str = request.POST.get('mes', '').strip()
        dia_str = request.POST.get('dia', '').strip()

        if not funcionario_id:
            return JsonResponse({'success': False, 'message': 'ID do funcionário é obrigatório.'})

        if not mes_str or not dia_str:
            return JsonResponse({'success': False, 'message': 'Mês e dia são obrigatórios.'})

        funcionario_id = int(funcionario_id)
        mes = int(mes_str)
        dia = int(dia_str)

        if not (1 <= mes <= 12):
            return JsonResponse({'success': False, 'message': 'Mês inválido.'})

        if not (1 <= dia <= 31):
            return JsonResponse({'success': False, 'message': 'Dia inválido.'})

        funcionario = Funcionario.objects.get(id=funcionario_id, escolas=escola_usuario)

        # Ano lectivo automático
        ano_lectivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
        if not ano_lectivo:
            return JsonResponse({'success': False, 'message': 'Nenhum ano lectivo aberto.'})

        FaltaFuncionario.objects.create(
            escola=escola_usuario,
            funcionario=funcionario,
            ano_lectivo=ano_lectivo,
            mes=mes,
            dia=dia,
            registrado_por=request.user
        )
        perfil = request.user.perfil   
        usuario = request.user 

        if perfil == 'diretor_admin':
            return redirect('administracao:cadastrar_funcionario')
        
        elif perfil == 'secretario_admin':
            return redirect('administracao:cadastrar_funcionario')
        
        elif perfil == 'diretor_geral':
            return redirect('core:cadastrar_funcionario')

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
@require_http_methods(["DELETE"])
@login_required
def remover_falta_funcionario(request, falta_id):
    try:
        # Buscar a falta
        falta = FaltaFuncionario.objects.get(id=falta_id)
        
        # Verificar permissões (opcional: apenas quem registrou ou admin pode remover)
        # if falta.registrado_por != request.user and not request.user.is_superuser:
        #     return JsonResponse({
        #         'success': False, 
        #         'message': 'Você não tem permissão para remover esta falta.'
        #     }, status=403)
        
        # Armazenar informações para mensagem de sucesso
        funcionario_nome = falta.funcionario.nome
        data_falta = f"{falta.dia}/{falta.mes}/{falta.ano_lectivo.ano}"
        
        # Remover a falta
        falta.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Falta de {funcionario_nome} ({data_falta}) removida com sucesso.'
        })
        
    except FaltaFuncionario.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Falta não encontrada.'
        }, status=404)
        
    except Exception as e:
        print(f"Erro ao remover falta: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erro ao remover falta: {str(e)}'
        }, status=500)
    
def recoperar_comprovativo(request, aluno_id, pagamento_id):
    # Buscar o aluno e o pagamento específico
    aluno = get_object_or_404(Aluno, id=aluno_id)
    pagamento = get_object_or_404(Pagamento, id=pagamento_id, aluno=aluno)
    
    perfil = request.user.perfil
    
    # Verificar permissões
    if perfil not in ['diretor_geral', 'diretor_admin', 'secretario_geral', 'secretario_admin']:
        return HttpResponse(
            """
            <html>
                <head>
                    <title>Erro 401 - Não Autorizado</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            background-color: #f8f9fa;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                        }
                        .error-box {
                            text-align: center;
                            padding: 40px;
                            border: 2px solid #dc3545;
                            border-radius: 12px;
                            background-color: #fff;
                            box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
                        }
                        h1 {
                            color: #dc3545;
                            font-size: 48px;
                            margin-bottom: 10px;
                        }
                        p {
                            font-size: 20px;
                            color: #333;
                        }
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h1>401</h1>
                        <p><strong>Perfil não autorizado</strong></p>
                        <p>Você não tem permissão para acessar esta página.</p>
                    </div>
                </body>
            </html>
            """,
            status=401
        )
    
    # Preparar os dados para o template
    meses_info = []
    
    # Determinar se tem multa (você precisará ajustar conforme seu modelo)
    tem_multa = False
    multa_valor = Decimal('0')
    
    # Se você tem um campo de multa no modelo Pagamento, use:
    # multa_valor = pagamento.multa_valor if hasattr(pagamento, 'multa_valor') else Decimal('0')
    # tem_multa = multa_valor > 0
    
    # Para o template, criar a estrutura de meses_info
    meses_info.append({
        'nome': pagamento.mes.nome if pagamento.mes else "Pagamento Único",
        'valor': pagamento.valor,
        'multa': multa_valor,
        'total': pagamento.valor + multa_valor,
        'tem_multa': tem_multa,
    })
    
    # Gerar código de barras baseado no ID do pagamento
    from datetime import datetime
    import base64
    from reportlab.graphics.barcode import createBarcodeDrawing
    
    # Usar o ID do pagamento para o código de barras
    barcode_value = str(pagamento.id)
    
    try:
        drawing = createBarcodeDrawing(
            'Code128',
            value=barcode_value,
            barHeight=40,
            barWidth=2.5,
            humanReadable=True
        )
        barcode_svg = drawing.asString('svg')
        barcode_base64 = base64.b64encode(barcode_svg.encode("utf-8")).decode("utf-8")
    except Exception as e:
        print(f"Erro ao gerar código de barras: {e}")
        barcode_base64 = ""
    
    # Determinar se é pagamento único ou mensal
    tipo_pagamento_radio = 'unico' if not pagamento.mes else 'mensal'
    
    # Calcular total pago
    total_pago = pagamento.valor + multa_valor
    
    # Criar objeto recibo para o template
    class Recibo:
        def __init__(self, numero):
            self.numero = numero
    
    recibo = Recibo(numero=pagamento.id)
    
    # Contexto para o template
    contexto = {
        "aluno": aluno,
        "meses_info": meses_info,
        "total_pago": total_pago,
        "valor_manual": pagamento.valor,
        "data_pagamento": pagamento.data_pagamento,
        "tipo_pagamento_radio": tipo_pagamento_radio,
        "tipo_pagamento": pagamento.tipo,
        "emolumento": pagamento.tipoServico,
        "barcode": barcode_base64,
        "recibo": recibo,
        "multa_geral_valor": multa_valor,
    }
    
    # Verificar qual perfil para redirecionar para o template correto
    # Todos usam o mesmo template, mas se quiser diferenciar:
    return render(request, "financeiro/comprovativos/comprovativo_pagamento.html", contexto)

# documentos/views.py

import io
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.utils import timezone
from django.db.models import Prefetch
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas

# Constantes
DIAS_SEMANA = ['2ª Feira', '3ª Feira', '4ª Feira', '5ª Feira', '6ª Feira']
HORARIOS = [
    {'tempo': '1ª', 'inicio': '13:00', 'fim': '13:45'},
    {'tempo': '2ª', 'inicio': '13:45', 'fim': '14:30'},
    {'tempo': '3ª', 'inicio': '14:30', 'fim': '15:15'},
    {'tempo': '4ª', 'inicio': '15:30', 'fim': '16:15'},
    {'tempo': '5ª', 'inicio': '16:15', 'fim': '17:00'},
    {'tempo': '6ª', 'inicio': '17:00', 'fim': '17:45'},
]


@login_required
def gerar_horario_completo(request):
    """
    Gera PDF com horário completo no formato da imagem (matriz por turma)
    """
    buffer = io.BytesIO()
    
    # Criar PDF em orientação paisagem
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # Margens
    left_margin = 1.5 * cm
    right_margin = 1.5 * cm
    top_margin = 2.5 * cm
    bottom_margin = 1.5 * cm
    
    content_width = width - left_margin - right_margin
    
    # Obter todas as turmas do I Ciclo (7ª, 8ª, 9ª)
    turmas = Turma.objects.filter(
        classe__numero__in=[7, 8, 9]
    ).select_related('classe', 'curso').order_by('classe__numero', 'nome')
    
    page_num = 1
    
    for turma in turmas:
        # Adicionar nova página se necessário
        if page_num > 1:
            c.showPage()
        
        # ===== CABEÇALHO INSTITUCIONAL =====
        # Título da instituição
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width/2, height - 1.2*cm, "REPÚBLICA DE ANGOLA")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width/2, height - 1.8*cm, "GOVERNO DA PROVÍNCIA DO BIÉ")
        
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(width/2, height - 2.4*cm, "ADMINISTRAÇÃO MUNICIPAL DO CUNHINGA")
        
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(width/2, height - 3.0*cm, "DIRECÇÃO MUNICIPAL DA EDUCAÇÃO")
        
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(width/2, height - 3.6*cm, "COMPLEXO ESCOLAR DE CAPESSA")
        
        # Linha divisória
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(left_margin, height - 4.2*cm, width - right_margin, height - 4.2*cm)
        
        # ===== TÍTULO DO HORÁRIO =====
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor('#2c3e50'))
        c.drawCentredString(width/2, height - 5.0*cm, 
                           f"HORÁRIO PARA O I CICLO (7ª, 8ª & 9ª CLASSE) ANO LECTIVO {timezone.now().year}/{(timezone.now().year + 1)}")
        
        # ===== CABEÇALHO DA TURMA =====
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        y_position = height - 6.0*cm
        c.drawString(left_margin, y_position, f"{turma.classe.numero}ª Classe")
        
        # ===== PREPARAR DADOS DA TABELA =====
        # Mapear dias da semana para índices
        dia_map = {
            '2ª Feira': 0,
            '3ª Feira': 1,
            '4ª Feira': 2,
            '5ª Feira': 3,
            '6ª Feira': 4,
        }
        
        # Criar matriz vazia: 6 horários x 5 dias
        matriz = [[None for _ in range(5)] for _ in range(6)]
        
        # Buscar vínculos e horários da turma
        vinculos = ProfessorVinculo.objects.filter(turma=turma).select_related(
            'professor', 'disciplina'
        ).prefetch_related(
            Prefetch('horarios', queryset=HorarioAula.objects.all())
        )
        
        # Preencher a matriz
        for vinculo in vinculos:
            for horario in vinculo.horarios.all():
                dia_idx = dia_map.get(horario.get_dia_semana_display())
                if dia_idx is not None:
                    # Encontrar o índice do horário baseado no tempo
                    for i, h in enumerate(HORARIOS):
                        if h['inicio'] == horario.hora_inicio.strftime("%H:%M"):
                            matriz[i][dia_idx] = vinculo.disciplina.nome
    
        # ===== CRIAR TABELA =====
        # Cabeçalho da tabela
        table_data = []
        
        # Linha de cabeçalho dos dias
        header_row = ['Tempo', 'Hora', '2ª Feira', '3ª Feira', '4ª Feira', '5ª Feira', '6ª Feira']
        table_data.append(header_row)
        
        # Preencher linhas da tabela
        for i, horario in enumerate(HORARIOS):
            row = [
                horario['tempo'],
                f"{horario['inicio']}-{horario['fim']}",
                matriz[i][0] or '',  # 2ª Feira
                matriz[i][1] or '',  # 3ª Feira
                matriz[i][2] or '',  # 4ª Feira
                matriz[i][3] or '',  # 5ª Feira
                matriz[i][4] or '',  # 6ª Feira
            ]
            table_data.append(row)
        
        # Adicionar linha de intervalo
        table_data.append(['Intervalo', '', '', '', '', '', ''])
        table_data.append(['', '', '', '', '', '', ''])
        
        # Calcular larguras das colunas
        col_widths = [
            content_width * 0.08,  # Tempo
            content_width * 0.12,  # Hora
            content_width * 0.16,  # 2ª Feira
            content_width * 0.16,  # 3ª Feira
            content_width * 0.16,  # 4ª Feira
            content_width * 0.16,  # 5ª Feira
            content_width * 0.16,  # 6ª Feira
        ]
        
        # Criar tabela
        table = Table(table_data, colWidths=col_widths)
        
        # Estilizar tabela
        style = TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            
            # Bordas
            ('GRID', (0, 0), (-1, -3), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            
            # Linha do intervalo
            ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#f0f0f0')),
            ('SPAN', (0, -2), (-1, -2)),  # Mesclar células do intervalo
            ('ALIGN', (0, -2), (-1, -2), 'CENTER'),
            ('FONTNAME', (0, -2), (-1, -2), 'Helvetica-Bold'),
            
            # Linha vazia após intervalo
            ('BACKGROUND', (0, -1), (-1, -1), colors.white),
            ('SPAN', (0, -1), (-1, -1)),
            
            # Alinhamento das células
            ('ALIGN', (0, 1), (0, -3), 'CENTER'),  # Coluna Tempo
            ('ALIGN', (1, 1), (1, -3), 'CENTER'),  # Coluna Hora
            ('ALIGN', (2, 1), (-1, -3), 'CENTER'),  # Colunas das disciplinas
            
            # Tamanho da fonte
            ('FONTSIZE', (0, 1), (-1, -3), 8),
            
            # Altura das linhas
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ])
        
        table.setStyle(style)
        
        # Posicionar tabela
        table_y = y_position - 1.5*cm - (len(table_data) * 0.6 * cm)
        
        # Verificar se cabe na página
        if table_y < bottom_margin:
            c.showPage()
            page_num += 1
            # Redesenhar cabeçalho da página
            table_y = height - 8*cm
        
        table.wrapOn(c, content_width, height)
        table.drawOn(c, left_margin, table_y)
        
        # ===== ASSINATURAS =====
        signature_y = table_y - 1.5*cm
        
        # Assinatura do Director da Escola
        c.setFont("Helvetica", 9)
        c.drawString(left_margin, signature_y, "VISTO O DIRECTOR DA ESCOLA")
        c.setFont("Helvetica-Bold", 9)
        c.drawString(left_margin, signature_y - 0.5*cm, "Lic. José Velemo")
        
        # Assinatura do Subdirector Pedagógico (canto direito)
        c.setFont("Helvetica", 9)
        c.drawRightString(width - right_margin, signature_y, "O Subdirector Pedagógico")
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(width - right_margin, signature_y - 0.5*cm, "Elias António")
        
        page_num += 1
    
    c.save()
    buffer.seek(0)
    
    filename = f'horario_completo_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf'
    
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type='application/pdf'
    )


@login_required
def visualizar_horario_completo(request):
    """
    Visualização HTML do horário completo no formato matriz
    """
    # Obter todas as turmas do I Ciclo (7ª, 8ª, 9ª)
    turmas = Turma.objects.filter(
        classe__numero__in=[7, 8, 9]
    ).select_related('classe', 'curso').order_by('classe__numero', 'nome')
    
    # Mapear dias
    dia_map = {
        '2ª Feira': 0,
        '3ª Feira': 1,
        '4ª Feira': 2,
        '5ª Feira': 3,
        '6ª Feira': 4,
    }
    
    turmas_horarios = []
    
    for turma in turmas:
        # Criar matriz vazia
        matriz = [[None for _ in range(5)] for _ in range(6)]
        
        # Buscar vínculos e horários
        vinculos = ProfessorVinculo.objects.filter(turma=turma).select_related(
            'professor', 'disciplina'
        ).prefetch_related(
            Prefetch('horarios', queryset=HorarioAula.objects.all())
        )
        
        # Preencher matriz
        for vinculo in vinculos:
            for horario in vinculo.horarios.all():
                dia_idx = dia_map.get(horario.get_dia_semana_display())
                if dia_idx is not None:
                    for i, h in enumerate(HORARIOS):
                        if h['inicio'] == horario.hora_inicio.strftime("%H:%M"):
                            matriz[i][dia_idx] = vinculo.disciplina.nome
                            break
        
        turmas_horarios.append({
            'classe': turma.classe.numero,
            'turma_nome': turma.nome,
            'matriz': matriz,
            'horarios': HORARIOS,
            'dias': DIAS_SEMANA
        })
    
    context = {
        'turmas_horarios': turmas_horarios,
        'ano_letivo': f"{timezone.now().year}/{(timezone.now().year + 1)}",
        'total_turmas': len(turmas_horarios),
    }
    
    return render(request, 'documentos/horario_completo.html', context)
