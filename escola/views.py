from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from .models import *
from django.db.models import Q, Sum, Count
from django.utils import timezone
from administracao.models import *
from financeiro.models import Pagamento, Despesa
from pedagogico.models import Monografia
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
import uuid
from django.http import HttpResponse, JsonResponse, FileResponse
import os
import zipfile
import json
import subprocess
from io import BytesIO
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.conf import settings
from django.db import connection

@login_required
def dashboard(request):
    perfil = request.user.perfil
    usuario = request.user

    # Totais gerais do sistema
    total_escolas = Escola.objects.count()
    total_alunos = Aluno.objects.all().count()
    total_funcionarios = Funcionario.objects.all().count()
    total_turmas = Turma.objects.all().count()
    
    # Dados financeiros do mês atual (consolidado)
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    
    pagamentos_mes = Pagamento.objects.filter(
        data_pagamento__year=ano_atual,
        data_pagamento__month=mes_atual
    )
    total_arrecadado = pagamentos_mes.aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Últimas escolas cadastradas
    ultimas_escolas = Escola.objects.all().order_by('-criado_em')[:5]
    
    # Últimos alunos cadastrados no sistema
    ultimos_alunos = Aluno.objects.all().select_related('turma').order_by('-id')[:5]
    
    # Dados para gráfico de distribuição de alunos por escola (top 5)
    escolas_top = Escola.objects.annotate(
        total_alunos=Count('aluno')
    ).order_by('-total_alunos')[:5]
    
    escolas_nomes = [escola.nome for escola in escolas_top]
    escolas_alunos = [escola.total_alunos for escola in escolas_top]
    
    # Distribuição por turno (geral)
    turno_manha = Aluno.objects.filter(turno='Manhã').count()
    turno_tarde = Aluno.objects.filter(turno='Tarde').count()
    turno_noite = Aluno.objects.filter(turno='Noite').count()
    
    # Funcionários por tipo
    funcionarios_docentes = Funcionario.objects.filter(funcao='professor').count()
    funcionarios_administrativos = Funcionario.objects.filter(funcao='administrativo').count()
    funcionarios_auxiliares = Funcionario.objects.filter(funcao='auxiliar').count()
    
    # Alunos por status (matriculados vs inadimplentes)
    alunos_inadimplentes = Reconfirmacao.objects.filter(
        ano_letivo=ano_atual,
        estado='Inadimplente'
    ).count()
    
    context = {
        # Cards principais
        'total_escolas': total_escolas,
        'total_alunos': total_alunos,
        'total_funcionarios': total_funcionarios,
        'total_docentes': funcionarios_docentes,
        'total_turmas': total_turmas,
        
        # Financeiro
        'faturamento_mensal': total_arrecadado,
        'total_arrecadado': total_arrecadado,
        
        # Dados para gráficos
        'escolas_nomes': escolas_nomes,
        'escolas_alunos': escolas_alunos,
        'dados_turnos': [turno_manha, turno_tarde, turno_noite],
        
        # Alertas
        'alunos_inadimplentes': alunos_inadimplentes,
        
        # Listas
        'ultimas_escolas': ultimas_escolas,
        'ultimos_alunos': ultimos_alunos,
        
        # Outros dados
        'ano_lectivo_atual': ano_atual,
        'funcionarios_administrativos': funcionarios_administrativos,
        'funcionarios_auxiliares': funcionarios_auxiliares,
    }
    
    if perfil in ['admin_central']:
        return render(request, 'escola/admin-dashboard.html', context)
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

@login_required
def escola_lista(request):
    search = request.GET.get('search', '')
    escolas_list = Escola.objects.all().order_by('-criado_em')
    
    if search:
        escolas_list = escolas_list.filter(nome__icontains=search)
    
    # Adiciona contagem de alunos para cada escola
    escolas_list = escolas_list.annotate(
        total_alunos=Count('aluno')
    )
    
    # Paginação
    paginator = Paginator(escolas_list, 10)
    page_number = request.GET.get('page')
    escolas = paginator.get_page(page_number)
    
    context = {
        'escolas': escolas,
        'search': search, 
        'total_escolas': Escola.objects.count(),
        'total_alunos_sistema': Aluno.objects.count(),  # Total geral do sistema
    }

    perfil = request.user.perfil
    usuario = request.user
    if perfil in ['admin_central']:
        return render(request, 'escola/escola_lista.html', context)
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

@login_required
def escola_criar(request):
    if request.method == 'POST':
        # Capturando dados do POST
        nome = request.POST.get('nome', '').strip()
        decreto_executivo = request.POST.get('decreto_executivo', '').strip() or None
        provincia = request.POST.get('provincia', '').strip()
        municipio = request.POST.get('municipio', '').strip()
        endereco = request.POST.get('endereco', '').strip()
        nif = request.POST.get('nif', '').strip() or None
        contacto = request.POST.get('contacto', '').strip()
        logotipo = request.FILES.get('logotipo')
        
        # Validações
        erros = []
        
        if not nome:
            erros.append('O campo Nome da Escola é obrigatório.')
        if not provincia:
            erros.append('O campo Província é obrigatório.')
        if not municipio:
            erros.append('O campo Município é obrigatório.')
        if not endereco:
            erros.append('O campo Endereço é obrigatório.')
        if not contacto:
            erros.append('O campo Contacto é obrigatório.')
        
        # Validar NIF único (se fornecido)
        if nif and Escola.objects.filter(nif=nif).exists():
            erros.append(f'Já existe uma escola cadastrada com o NIF {nif}.')
        
        if erros:
            for erro in erros:
                messages.error(request, erro)
            context = {
                'titulo': 'Nova Escola',
                'botao': 'Cadastrar',
                'nome': nome,
                'decreto_executivo': decreto_executivo,
                'provincia': provincia,
                'municipio': municipio,
                'endereco': endereco,
                'nif': nif,
                'contacto': contacto,
            }
            perfil = request.user.perfil
            usuario = request.user
            if perfil in ['admin_central']:
                return render(request, 'escola/escola_form.html', context)
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
        
        # Criar escola
        escola = Escola(
            nome=nome,
            decreto_executivo=decreto_executivo,
            provincia=provincia,
            municipio=municipio,
            endereco=endereco,
            nif=nif,
            contacto=contacto,
            logotipo=logotipo
        )
        escola.save()
        
        messages.success(request, f'Escola "{nome}" criada com sucesso!')
        return redirect('escola:escola_lista')
    
    context = {
        'titulo': 'Nova Escola',
        'botao': 'Cadastrar',
        'escola': None,
    }
    perfil = request.user.perfil
    usuario = request.user
    if perfil in ['admin_central']:
        return render(request, 'escola/escola_form.html', context)
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

@login_required
def escola_editar(request, pk):
    escola = get_object_or_404(Escola, pk=pk)
    
    if request.method == 'POST':
        # Capturando dados do POST
        nome = request.POST.get('nome', '').strip()
        decreto_executivo = request.POST.get('decreto_executivo', '').strip() or None
        provincia = request.POST.get('provincia', '').strip()
        municipio = request.POST.get('municipio', '').strip()
        endereco = request.POST.get('endereco', '').strip()
        nif = request.POST.get('nif', '').strip() or None
        contacto = request.POST.get('contacto', '').strip()
        logotipo = request.FILES.get('logotipo')
        remover_logotipo = request.POST.get('remover_logotipo', '')
        
        # Validações
        erros = []
        
        if not nome:
            erros.append('O campo Nome da Escola é obrigatório.')
        if not provincia:
            erros.append('O campo Província é obrigatório.')
        if not municipio:
            erros.append('O campo Município é obrigatório.')
        if not endereco:
            erros.append('O campo Endereço é obrigatório.')
        if not contacto:
            erros.append('O campo Contacto é obrigatório.')
        
        # Validar NIF único (excluindo a escola atual)
        if nif and Escola.objects.exclude(pk=pk).filter(nif=nif).exists():
            erros.append(f'Já existe outra escola cadastrada com o NIF {nif}.')
        
        if erros:
            for erro in erros:
                messages.error(request, erro)
            context = {
                'titulo': 'Editar Escola',
                'botao': 'Atualizar',
                'escola': escola,
                'nome': nome,
                'decreto_executivo': decreto_executivo,
                'provincia': provincia,
                'municipio': municipio,
                'endereco': endereco,
                'nif': nif,
                'contacto': contacto,
            }
            perfil = request.user.perfil
            usuario = request.user
            if perfil in ['admin_central']:
                return render(request, 'escola/escola_form.html', context)
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
                
        # Atualizar campos
        escola.nome = nome
        escola.decreto_executivo = decreto_executivo
        escola.provincia = provincia
        escola.municipio = municipio
        escola.endereco = endereco
        escola.nif = nif
        escola.contacto = contacto
        
        # Remover logotipo se solicitado
        if remover_logotipo == 'sim' and escola.logotipo:
            escola.logotipo.delete(save=False)
            escola.logotipo = None
        
        # Atualizar logotipo se enviado
        if logotipo:
            # Remove o antigo se existir
            if escola.logotipo:
                escola.logotipo.delete(save=False)
            escola.logotipo = logotipo
        
        escola.save()
        
        messages.success(request, f'Escola "{nome}" atualizada com sucesso!')
        return redirect('escola:escola_lista')
    
    context = {
        'titulo': 'Editar Escola',
        'botao': 'Atualizar',
        'escola': escola,
        'nome': escola.nome,
        'decreto_executivo': escola.decreto_executivo,
        'provincia': escola.provincia,
        'municipio': escola.municipio,
        'endereco': escola.endereco,
        'nif': escola.nif,
        'contacto': escola.contacto,
    }
    perfil = request.user.perfil
    usuario = request.user
    if perfil in ['admin_central']:
        return render(request, 'escola/escola_form.html', context)
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

@login_required
def escola_delete(request, pk):
    escola = get_object_or_404(Escola, pk=pk)
    
    if request.method == 'POST':
        nome = escola.nome
        # Remove o logotipo do disco
        if escola.logotipo:
            escola.logotipo.delete(save=False)
        escola.delete()
        messages.success(request, f'Escola "{nome}" removida com sucesso!')
        return redirect('escola:escola_lista')
    
    perfil = request.user.perfil
    usuario = request.user
    if perfil in ['admin_central']:
        return render(request, 'escola/escola_confirm_delete.html', {'escola': escola})
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

Usuario = get_user_model()

def remover_acentos(texto):
    """Remove acentos de um texto"""
    import unicodedata
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')

def criar_usuario_funcionario(nome, bi, funcao, escolas_ids):
    """Cria um usuário automaticamente para o funcionário"""
    try:
        # Remove acentos e pega primeiro e último nome
        nomes = remover_acentos(nome.lower()).split()
        primeiro_nome = nomes[0]
        ultimo_nome = nomes[-1] if len(nomes) > 1 else nomes[0]
        
        # Gera um código único
        codigo_unico = str(uuid.uuid4())[:5]
        email = f"{primeiro_nome}{ultimo_nome}{codigo_unico}@sigesc.co.ao"
        username = f"{primeiro_nome}{ultimo_nome}{codigo_unico}@sigesc.co.ao"
        
        # Mapeia a função para o perfil correto
        perfil_map = {
            'Diretor Geral': 'diretor_geral',
            'Diretor Pedagógico': 'diretor_pedagogico',
            'Diretor Administrativo': 'diretor_admin',
            'Coordenador de Turno': 'coordenador_turno',
            'Coordenador de Turma': 'coordenador_turma',
            'Coordenador de Disciplina': 'coordenador_disc',
            'Secretário Geral': 'secretario_geral',
            'Secretário Administrativo': 'secretario_admin',
            'Secretário Pedagógico': 'secretario_ped',
            'Professor': 'professor',
            'Auxiliar Administrativo': 'secretario_admin',
            'Outro': 'secretario_admin',
        }
        
        perfil = perfil_map.get(funcao, 'secretario_admin')
        
        # Busca a primeira escola
        primeira_escola = Escola.objects.get(id=escolas_ids[0]) if escolas_ids else None
        
        # Cria o usuário
        usuario = Usuario.objects.create_user(
            username=username,
            email=email,
            password=bi,  # Senha inicial = BI
            first_name=nome.split()[0],
            last_name=' '.join(nome.split()[1:]) if len(nome.split()) > 1 else '',
            perfil=perfil,
            escola=primeira_escola,
            telefone='',
        )
        
        return usuario
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        return None

@login_required
def form_funcionario(request):
    search = request.GET.get('search', '')
    escola_filter = request.GET.get('escola', '')
    funcao_filter = request.GET.get('funcao', '')
    
    # Query base (SEM professores)
    funcionarios_qs = Funcionario.objects \
        .prefetch_related('escolas') \
        .exclude(funcao='professor')
    
    # Filtros
    if search:
        funcionarios_qs = funcionarios_qs.filter(
            Q(nome__icontains=search) |
            Q(bi__icontains=search) |
            Q(funcao__icontains=search) |
            Q(email__icontains=search)
        )
    
    if escola_filter:
        funcionarios_qs = funcionarios_qs.filter(escolas__id=escola_filter)
    
    if funcao_filter:
        funcionarios_qs = funcionarios_qs.filter(funcao=funcao_filter)
    
    funcionarios_qs = funcionarios_qs.order_by('-criado_em')
    
    # Paginação
    paginator = Paginator(funcionarios_qs, 12)
    page_number = request.GET.get('page')
    funcionarios = paginator.get_page(page_number)
    
    total_funcionarios = funcionarios_qs.count()
    total_ativos = funcionarios_qs.filter(ativo=True).count()
    
    context = {
        'funcionarios': funcionarios,
        'escolas': Escola.objects.all(),
        'search': search,
        'escola_filter': escola_filter,
        'funcao_filter': funcao_filter,
        'funcoes': Funcionario.FUNCOES,
        'total_funcionarios': total_funcionarios,
        'total_ativos': total_ativos,
    }

    perfil = request.user.perfil
    usuario = request.user
    if perfil in ['admin_central']:
        return render(request, 'escola/form-funcionario.html', context)
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

@login_required
def funcionario_criar(request):
    """Criar novo funcionário"""
    if request.method == 'POST':
        escolas_ids = request.POST.getlist('escolas')
        nome = request.POST.get('nome', '').strip()
        bi = request.POST.get('bi', '').strip()
        genero = request.POST.get('genero', '')
        funcao = request.POST.get('funcao', '')
        telefone = request.POST.get('telefone', '').strip()
        email = request.POST.get('email', '').strip()
        nivel_academico = request.POST.get('nivel_academico', '').strip()
        area_formacao = request.POST.get('area_formacao', '').strip()
        salario = request.POST.get('salario', '0').replace(',', '.')
        ativo = request.POST.get('ativo') == 'on'
        
        # Validações
        erros = []
        
        if not escolas_ids:
            erros.append('Selecione pelo menos uma escola.')
        if not nome:
            erros.append('O nome é obrigatório.')
        if not bi:
            erros.append('O BI é obrigatório.')
        if not genero:
            erros.append('O gênero é obrigatório.')
        if not funcao:
            erros.append('A função é obrigatória.')
        if not telefone:
            erros.append('O telefone é obrigatório.')
        
        # Verifica se já existe funcionário com este BI
        if Funcionario.objects.filter(bi=bi).exists():
            erros.append(f'Já existe um funcionário com o BI nº {bi}')
        
        # Valida salário
        try:
            salario = float(salario) if salario else 0
            if salario < 0:
                erros.append('O salário não pode ser negativo.')
        except ValueError:
            erros.append('Valor de salário inválido.')
        
        if erros:
            for erro in erros:
                messages.error(request, erro)

            perfil = request.user.perfil
            usuario = request.user
            if perfil in ['admin_central']:
                return render(request, 'escola/funcionario_form.html', {
                    'escolas': Escola.objects.all(),
                    'dados_post': request.POST,
                    'escolas_selecionadas': escolas_ids,
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
        
        try:
            # Cria o usuário automaticamente
            usuario = criar_usuario_funcionario(nome, bi, funcao, escolas_ids)
            
            # Cria o funcionário
            funcionario = Funcionario.objects.create(
                usuario=usuario,
                nome=nome,
                bi=bi,
                genero=genero,
                funcao=funcao,
                telefone=telefone,
                email=email if email else None,
                nivel_academico=nivel_academico,
                area_formacao=area_formacao,
                salario=salario,
                ativo=ativo,
            )
            
            # Adiciona as escolas
            funcionario.escolas.set(escolas_ids)
            
            if usuario:
                messages.success(
                    request, 
                    f'Funcionário "{nome}" cadastrado com sucesso! '
                    f'Credenciais de acesso: {usuario.username}'
                )
            else:
                messages.warning(
                    request, 
                    f'Funcionário "{nome}" cadastrado, mas houve erro ao criar o usuário de acesso.'
                )
            
            return redirect('escola:form_funcionario')
            
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar funcionário: {str(e)}')
            return redirect('escola:funcionario_criar')
    perfil = request.user.perfil
    usuario = request.user
    if perfil in ['admin_central']:
        return render(request, 'escola/funcionario_form.html', {
            'escolas': Escola.objects.all(),
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

@login_required
def funcionario_editar(request, pk):
    """Editar funcionário"""
    funcionario = get_object_or_404(Funcionario, pk=pk)
    
    if request.method == 'POST':
        escolas_ids = request.POST.getlist('escolas')
        funcionario.nome = request.POST.get('nome', '').strip()
        bi_novo = request.POST.get('bi', '').strip()
        funcionario.genero = request.POST.get('genero', '')
        funcionario.funcao = request.POST.get('funcao', '')
        funcionario.telefone = request.POST.get('telefone', '').strip()
        funcionario.email = request.POST.get('email', '').strip()
        funcionario.nivel_academico = request.POST.get('nivel_academico', '').strip()
        funcionario.area_formacao = request.POST.get('area_formacao', '').strip()
        funcionario.ativo = request.POST.get('ativo') == 'on'
        
        salario = request.POST.get('salario', '0').replace(',', '.')
        
        # Validações
        erros = []
        
        if not escolas_ids:
            erros.append('Selecione pelo menos uma escola.')
        if not funcionario.nome:
            erros.append('O nome é obrigatório.')
        if not bi_novo:
            erros.append('O BI é obrigatório.')
        if not funcionario.genero:
            erros.append('O gênero é obrigatório.')
        if not funcionario.funcao:
            erros.append('A função é obrigatória.')
        if not funcionario.telefone:
            erros.append('O telefone é obrigatório.')
        
        # Verifica BI duplicado (excluindo o atual)
        if Funcionario.objects.filter(bi=bi_novo).exclude(pk=pk).exists():
            erros.append(f'Já existe outro funcionário com o BI nº {bi_novo}')
        
        try:
            funcionario.salario = float(salario) if salario else 0
            if funcionario.salario < 0:
                erros.append('O salário não pode ser negativo.')
        except ValueError:
            erros.append('Valor de salário inválido.')
        
        if erros:
            for erro in erros:
                messages.error(request, erro)
            perfil = request.user.perfil
            usuario = request.user
            if perfil in ['admin_central']:
                return render(request, 'escola/funcionario_form.html', {
                    'escolas': Escola.objects.all(),
                    'funcionario': funcionario,
                    'escolas_selecionadas': escolas_ids,
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
        
        # Atualiza o BI
        funcionario.bi = bi_novo
        
        # Salva o funcionário
        funcionario.save()
        
        # Atualiza as escolas
        funcionario.escolas.set(escolas_ids)
        
        # Atualiza o usuário se existir
        if funcionario.usuario:
            usuario = funcionario.usuario
            usuario.first_name = funcionario.nome.split()[0]
            usuario.last_name = ' '.join(funcionario.nome.split()[1:]) if len(funcionario.nome.split()) > 1 else ''
            usuario.save()
        
        messages.success(request, f'Funcionário "{funcionario.nome}" atualizado com sucesso!')
        return redirect('escola:form_funcionario')
    
    # GET - Prepara dados para o formulário
    escolas_selecionadas = list(funcionario.escolas.values_list('id', flat=True))
    perfil = request.user.perfil
    usuario = request.user
    if perfil in ['admin_central']:
        return render(request, 'escola/funcionario_form.html', {
            'escolas': Escola.objects.all(),
            'funcionario': funcionario,
            'escolas_selecionadas': escolas_selecionadas,
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

@login_required
def funcionario_deletar(request, pk):
    """Deletar funcionário"""
    funcionario = get_object_or_404(Funcionario, pk=pk)
    
    if request.method == 'POST':
        nome = funcionario.nome
        
        # Remove o usuário vinculado
        if funcionario.usuario:
            funcionario.usuario.delete()
        
        funcionario.delete()
        messages.success(request, f'Funcionário "{nome}" removido com sucesso!')
        return redirect('escola:form_funcionario')
    perfil = request.user.perfil
    usuario = request.user
    if perfil in ['admin_central']:
        return render(request, 'escola/funcionario_confirm_delete.html', {
            'funcionario': funcionario,
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

# Decorator para verificar se é admin central
def admin_central_required(view_func):
    decorated_func = login_required(view_func)
    return user_passes_test(
        lambda u: u.is_authenticated and u.perfil == 'admin_central',
        login_url='/login/',
        redirect_field_name=None
    )(decorated_func)

@admin_central_required
def configuracoes_sistema(request):
    """Página principal de configurações do sistema"""
    
    # Buscar ou criar configurações
    config, created = ConfiguracaoSistema.objects.get_or_create(id=1)
    
    # Buscar backups
    backups = BackupSistema.objects.all().order_by('-data_criacao')
    
    # Buscar logs recentes
    logs = LogSistema.objects.all().order_by('-data')[:50]
    
    # Estatísticas do sistema
    tamanho_banco = get_database_size()
    espaco_utilizado = get_media_storage_size()
    percentagem_espaco = calculate_storage_percentage(espaco_utilizado)
    total_usuarios = get_user_count()
    
    # Anos lectivos disponíveis
    anos_lectivos = AnoLectivo.objects.values('ano').distinct().order_by('-ano')
    ano_lectivo_corrente = config.ano_lectivo_corrente or datetime.now().year
    
    context = {
        'config': config,
        'backups': backups,
        'logs': logs,
        'tamanho_banco': tamanho_banco,
        'espaco_utilizado': espaco_utilizado,
        'percentagem_espaco': percentagem_espaco,
        'total_usuarios': total_usuarios,
        'anos_lectivos': anos_lectivos,
        'ano_lectivo_corrente': ano_lectivo_corrente,
        'versao_sistema': get_system_version(),
        'versao_django': django_version(),
        'ultima_atualizacao': get_last_update_date(),
    }
    
    return render(request, 'escola/configuracoes.html', context)

@admin_central_required
def criar_backup(request):
    """Cria um backup completo do sistema"""
    
    if request.method == 'POST':
        try:
            descricao = request.POST.get('descricao', '')
            incluir_media = request.POST.get('backupMedia') == 'on'
            incluir_config = request.POST.get('backupConfig') == 'on'
            
            # Criar diretório de backups se não existir
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Nome do arquivo de backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_backup = f'backup_sigesc_{timestamp}.zip'
            caminho_backup = os.path.join(backup_dir, nome_backup)
            
            # Criar arquivo ZIP
            with zipfile.ZipFile(caminho_backup, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 1. Backup do banco de dados (SQL)
                sql_backup = export_database_to_sql()
                zipf.writestr(f'backup_{timestamp}/database.sql', sql_backup)
                
                # 2. Backup dos arquivos de mídia
                if incluir_media:
                    add_media_to_zip(zipf, timestamp)
                
                # 3. Backup das configurações
                if incluir_config:
                    config_data = export_configurations()
                    zipf.writestr(f'backup_{timestamp}/configuracoes.json', json.dumps(config_data, indent=2))
                
                # 4. Informações do backup
                info = {
                    'versao_sistema': get_system_version(),
                    'data_criacao': datetime.now().isoformat(),
                    'criado_por': request.user.username,
                    'descricao': descricao,
                    'incluir_media': incluir_media,
                    'incluir_config': incluir_config,
                }
                zipf.writestr(f'backup_{timestamp}/info.json', json.dumps(info, indent=2))
            
            # Calcular tamanho do arquivo
            tamanho = os.path.getsize(caminho_backup)
            tamanho_formatado = format_file_size(tamanho)
            
            # Salvar registro do backup
            backup = BackupSistema.objects.create(
                nome=nome_backup,
                caminho=caminho_backup,
                tamanho=tamanho_formatado,
                descricao=descricao,
                criado_por=request.user
            )
            
            # Registrar log
            LogSistema.objects.create(
                usuario=request.user,
                acao='Criar Backup',
                tipo='success',
                detalhes=f'Backup criado: {nome_backup}',
                ip=get_client_ip(request)
            )
            
            messages.success(request, f'Backup criado com sucesso! Tamanho: {tamanho_formatado}')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar backup: {str(e)}')
            LogSistema.objects.create(
                usuario=request.user,
                acao='Criar Backup',
                tipo='error',
                detalhes=f'Erro: {str(e)}',
                ip=get_client_ip(request)
            )
    
    return redirect('escola:configuracoes')

@admin_central_required
def baixar_backup(request, backup_id):
    """Faz o download de um arquivo de backup"""
    
    backup = get_object_or_404(BackupSistema, id=backup_id)
    
    if not os.path.exists(backup.caminho):
        messages.error(request, 'Arquivo de backup não encontrado no servidor.')
        return redirect('escola:configuracoes')
    
    # Registrar log
    LogSistema.objects.create(
        usuario=request.user,
        acao='Baixar Backup',
        tipo='info',
        detalhes=f'Download do backup: {backup.nome}',
        ip=get_client_ip(request)
    )
    
    # Enviar arquivo
    response = FileResponse(
        open(backup.caminho, 'rb'),
        content_type='application/zip',
        as_attachment=True,
        filename=backup.nome
    )
    return response

@admin_central_required
def restaurar_backup(request):
    """Restaura um backup enviado por upload"""
    
    if request.method == 'POST' and request.FILES.get('arquivo_backup'):
        arquivo = request.FILES['arquivo_backup']
        
        # Validar extensão
        if not arquivo.name.endswith(('.zip', '.sql', '.gz')):
            messages.error(request, 'Formato de arquivo inválido. Use ZIP, SQL ou GZ.')
            return redirect('escola:configuracoes')
        
        try:
            # Salvar arquivo temporariamente
            temp_dir = os.path.join(settings.BASE_DIR, 'temp')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            temp_path = os.path.join(temp_dir, arquivo.name)
            with open(temp_path, 'wb+') as dest:
                for chunk in arquivo.chunks():
                    dest.write(chunk)
            
            # Processar restauração
            if arquivo.name.endswith('.zip'):
                restaurar_de_zip(temp_path, request.user)
            elif arquivo.name.endswith('.sql'):
                restaurar_de_sql(temp_path, request.user)
            elif arquivo.name.endswith('.gz'):
                restaurar_de_gz(temp_path, request.user)
            
            # Limpar arquivo temporário
            os.remove(temp_path)
            
            messages.success(request, 'Backup restaurado com sucesso! O sistema foi atualizado.')
            
        except Exception as e:
            messages.error(request, f'Erro ao restaurar backup: {str(e)}')
    
    return redirect('escola:configuracoes')

@admin_central_required
def restaurar_backup_arquivo(request):
    """Restaura um backup existente no servidor"""
    
    if request.method == 'POST':
        backup_id = request.POST.get('backup_id')
        backup = get_object_or_404(BackupSistema, id=backup_id)
        
        if not os.path.exists(backup.caminho):
            messages.error(request, 'Arquivo de backup não encontrado.')
            return redirect('escola:configuracoes')
        
        try:
            # Processar restauração
            if backup.nome.endswith('.zip'):
                restaurar_de_zip(backup.caminho, request.user)
            else:
                messages.error(request, 'Formato de backup não suportado.')
                return redirect('escola:configuracoes')
            
            messages.success(request, 'Backup restaurado com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao restaurar: {str(e)}')
    
    return redirect('escola:configuracoes')

@admin_central_required
def excluir_backup(request):
    """Exclui um arquivo de backup"""
    
    if request.method == 'POST':
        backup_id = request.POST.get('backup_id')
        backup = get_object_or_404(BackupSistema, id=backup_id)
        
        try:
            # Remover arquivo físico
            if os.path.exists(backup.caminho):
                os.remove(backup.caminho)
            
            # Remover registro
            backup.delete()
            
            messages.success(request, f'Backup {backup.nome} excluído com sucesso!')
            
            LogSistema.objects.create(
                usuario=request.user,
                acao='Excluir Backup',
                tipo='warning',
                detalhes=f'Backup excluído: {backup.nome}',
                ip=get_client_ip(request)
            )
            
        except Exception as e:
            messages.error(request, f'Erro ao excluir backup: {str(e)}')
    
    return redirect('escola:configuracoes')

@admin_central_required
def salvar_configuracoes(request):
    """Salva as configurações do sistema"""
    
    if request.method == 'POST':
        config, created = ConfiguracaoSistema.objects.get_or_create(id=1)
        
        # Configurações básicas
        config.nome_sistema = request.POST.get('nome_sistema', config.nome_sistema)
        config.ano_lectivo_corrente = request.POST.get('ano_lectivo_corrente')
        config.timezone = request.POST.get('timezone', config.timezone)
        
        # Backup automático
        config.backup_auto = request.POST.get('backup_auto') == 'on'
        config.backup_frequencia = request.POST.get('backup_frequencia', 'daily')
        config.manter_backups_dias = int(request.POST.get('manter_backups_dias', 30))
        
        # Configurações de email
        config.smtp_server = request.POST.get('smtp_server', '')
        config.smtp_port = int(request.POST.get('smtp_port', 587))
        config.smtp_user = request.POST.get('smtp_user', '')
        config.email_sistema = request.POST.get('email_sistema', '')
        
        # Senha do email (só atualiza se fornecida)
        nova_senha = request.POST.get('smtp_password', '')
        if nova_senha:
            config.smtp_password = nova_senha
        
        config.save()
        
        # Atualizar configurações do Django
        update_django_settings(config)
        
        messages.success(request, 'Configurações salvas com sucesso!')
        
        LogSistema.objects.create(
            usuario=request.user,
            acao='Salvar Configurações',
            tipo='success',
            detalhes='Configurações do sistema atualizadas',
            ip=get_client_ip(request)
        )
    
    return redirect('escola:configuracoes')

@admin_central_required
def limpar_cache(request):
    """Limpa o cache do sistema"""
    
    try:
        # Limpar cache de templates
        call_command('clear_cache', verbosity=0)
        
        # Limpar sessões expiradas
        call_command('clearsessions', verbosity=0)
        
        messages.success(request, 'Cache do sistema limpo com sucesso!')
        
        LogSistema.objects.create(
            usuario=request.user,
            acao='Limpar Cache',
            tipo='success',
            detalhes='Cache do sistema limpo',
            ip=get_client_ip(request)
        )
        
    except Exception as e:
        messages.error(request, f'Erro ao limpar cache: {str(e)}')
    
    return redirect('escola:configuracoes')

@admin_central_required
def otimizar_banco(request):
    """Otimiza o banco de dados"""
    
    try:
        with connection.cursor() as cursor:
            if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                cursor.execute('VACUUM;')
            elif 'postgresql' in settings.DATABASES['default']['ENGINE']:
                cursor.execute('VACUUM ANALYZE;')
            elif 'mysql' in settings.DATABASES['default']['ENGINE']:
                cursor.execute('OPTIMIZE TABLES;')
        
        messages.success(request, 'Banco de dados otimizado com sucesso!')
        
        LogSistema.objects.create(
            usuario=request.user,
            acao='Otimizar Banco',
            tipo='success',
            detalhes='Otimização do banco de dados realizada',
            ip=get_client_ip(request)
        )
        
    except Exception as e:
        messages.error(request, f'Erro ao otimizar banco: {str(e)}')
    
    return redirect('escola:configuracoes')

@admin_central_required
def relatorio_sistema(request):
    """Gera relatório completo do sistema"""
    
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    
    # Criar resposta PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_sistema_{datetime.now().strftime("%Y%m%d")}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=30
    )
    story.append(Paragraph("Relatório do Sistema SIGESC", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Estatísticas Gerais
    story.append(Paragraph("Estatísticas Gerais", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    total_escolas = Escola.objects.count()
    total_alunos = Aluno.objects.count()
    total_funcionarios = Funcionario.objects.count()
    
    data = [
        ['Métrica', 'Valor'],
        ['Total de Escolas', str(total_escolas)],
        ['Total de Alunos', str(total_alunos)],
        ['Total de Funcionários', str(total_funcionarios)],
        ['Tamanho do Banco de Dados', get_database_size()],
        ['Espaço de Mídia Utilizado', get_media_storage_size()],
    ]
    
    table = Table(data, colWidths=[8*cm, 8*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(table)
    story.append(Spacer(1, 30))
    
    # Configurações do Sistema
    story.append(Paragraph("Configurações do Sistema", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    config = ConfiguracaoSistema.objects.first()
    if config:
        config_data = [
            ['Configuração', 'Valor'],
            ['Nome do Sistema', config.nome_sistema],
            ['Ano Lectivo Corrente', config.ano_lectivo_corrente or 'N/A'],
            ['Timezone', config.timezone],
            ['Backup Automático', 'Ativado' if config.backup_auto else 'Desativado'],
            ['Frequência Backup', config.get_backup_frequencia_display() if config.backup_auto else 'N/A'],
        ]
        
        config_table = Table(config_data, colWidths=[8*cm, 8*cm])
        config_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4caf50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(config_table)
    
    doc.build(story)
    
    LogSistema.objects.create(
        usuario=request.user,
        acao='Gerar Relatório',
        tipo='info',
        detalhes='Relatório do sistema gerado',
        ip=get_client_ip(request)
    )
    
    return response

# ==================== FUNÇÕES AUXILIARES ====================

def get_database_size():
    """Retorna o tamanho do banco de dados"""
    try:
        if 'sqlite' in settings.DATABASES['default']['ENGINE']:
            db_path = settings.DATABASES['default']['NAME']
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                return format_file_size(size)
        elif 'postgresql' in settings.DATABASES['default']['ENGINE']:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_database_size(current_database())")
                size = cursor.fetchone()[0]
                return format_file_size(size)
        elif 'mysql' in settings.DATABASES['default']['ENGINE']:
            with connection.cursor() as cursor:
                cursor.execute("SELECT data_length + index_length FROM information_schema.tables WHERE table_schema = DATABASE()")
                rows = cursor.fetchall()
                size = sum(row[0] for row in rows)
                return format_file_size(size)
    except:
        pass
    return "N/A"

def get_media_storage_size():
    """Retorna o tamanho dos arquivos de mídia"""
    try:
        media_path = settings.MEDIA_ROOT
        if os.path.exists(media_path):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(media_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
            return format_file_size(total_size)
    except:
        pass
    return "N/A"

def calculate_storage_percentage(used_space_str):
    """Calcula percentagem de espaço usado"""
    try:
        # Converter string como "150 MB" para bytes
        if 'GB' in used_space_str:
            used = float(used_space_str.replace(' GB', '')) * 1024 * 1024 * 1024
        elif 'MB' in used_space_str:
            used = float(used_space_str.replace(' MB', '')) * 1024 * 1024
        elif 'KB' in used_space_str:
            used = float(used_space_str.replace(' KB', '')) * 1024
        else:
            return 0
        
        # Espaço total aproximado (1GB para exemplo)
        total = 1 * 1024 * 1024 * 1024
        percentage = (used / total) * 100
        return min(100, int(percentage))
    except:
        return 0

def get_user_count():
    """Retorna total de usuários"""
    from core.models import Usuario
    return Usuario.objects.count()

def format_file_size(size):
    """Formata tamanho de arquivo"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def get_system_version():
    """Retorna versão do sistema"""
    try:
        version_file = os.path.join(settings.BASE_DIR, 'version.txt')
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                return f.read().strip()
    except:
        pass
    return "1.0.0"

def django_version():
    """Retorna versão do Django"""
    import django
    return django.get_version()

def get_last_update_date():
    """Retorna data da última atualização"""
    try:
        # Pega a data do último backup ou configuração salva
        last_backup = BackupSistema.objects.first()
        if last_backup:
            return last_backup.data_criacao.date()
        
        last_config = ConfiguracaoSistema.objects.first()
        if last_config:
            return last_config.atualizado_em.date()
    except:
        pass
    return None

def get_client_ip(request):
    """Obtém IP do cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def export_database_to_sql():
    """Exporta banco de dados para SQL"""
    from io import StringIO
    
    output = StringIO()
    
    if 'sqlite' in settings.DATABASES['default']['ENGINE']:
        with connection.cursor() as cursor:
            # Obter todas as tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                # Obter schema
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                schema = cursor.fetchone()
                if schema:
                    output.write(f"{schema[0]};\n\n")
                
                # Obter dados
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                if rows:
                    # Obter nomes das colunas
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    for row in rows:
                        values = []
                        for val in row:
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, str):
                                escaped = val.replace("'", "''")
                                values.append(f"'{escaped}'")
                            else:
                                values.append(str(val))
                        
                        output.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")
                    output.write("\n")
    
    return output.getvalue()

def add_media_to_zip(zipf, timestamp):
    """Adiciona arquivos de mídia ao ZIP"""
    media_path = settings.MEDIA_ROOT
    if os.path.exists(media_path):
        for root, dirs, files in os.walk(media_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.join(f'backup_{timestamp}/media', os.path.relpath(file_path, media_path))
                zipf.write(file_path, arcname)

def export_configurations():
    """Exporta configurações para JSON"""
    config = ConfiguracaoSistema.objects.first()
    if config:
        return {
            'nome_sistema': config.nome_sistema,
            'ano_lectivo_corrente': config.ano_lectivo_corrente,
            'timezone': config.timezone,
            'backup_auto': config.backup_auto,
            'backup_frequencia': config.backup_frequencia,
            'manter_backups_dias': config.manter_backups_dias,
            'smtp_server': config.smtp_server,
            'smtp_port': config.smtp_port,
            'smtp_user': config.smtp_user,
            'email_sistema': config.email_sistema,
        }
    return {}

def restaurar_de_zip(zip_path, usuario, request=None):
    """Restaura sistema a partir de arquivo ZIP"""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        # Encontrar arquivos extraídos
        extracted_dirs = [d for d in os.listdir(temp_dir) if d.startswith('backup_')]
        if extracted_dirs:
            backup_dir = os.path.join(temp_dir, extracted_dirs[0])
            
            # Restaurar SQL
            sql_file = os.path.join(backup_dir, 'database.sql')
            if os.path.exists(sql_file):
                restaurar_de_sql(sql_file, usuario, request)
            
            # Restaurar mídia
            media_dir = os.path.join(backup_dir, 'media')
            if os.path.exists(media_dir):
                for item in os.listdir(media_dir):
                    src = os.path.join(media_dir, item)
                    dst = os.path.join(settings.MEDIA_ROOT, item)
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
            
            # Restaurar configurações
            config_file = os.path.join(backup_dir, 'configuracoes.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8', errors='ignore') as f:
                    config_data = json.load(f)
                    restaurar_configuracoes(config_data)
    
    finally:
        shutil.rmtree(temp_dir)

def restaurar_de_sql(sql_path, usuario, request=None):
    """Restaura banco a partir de arquivo SQL"""
    with open(sql_path, 'r', encoding='utf-8', errors='ignore') as f:
        sql_content = f.read()
    
    with connection.cursor() as cursor:
        # Executar comandos SQL separadamente
        for statement in sql_content.split(';'):
            if statement.strip():
                try:
                    cursor.execute(statement)
                except Exception as e:
                    print(f"Erro ao executar SQL: {e}")
    
    LogSistema.objects.create(
        usuario=usuario,
        acao='Restaurar Backup',
        tipo='success',
        detalhes='Banco de dados restaurado com sucesso',
        ip=get_client_ip(request) if request else None
    )

def restaurar_de_gz(gz_path, usuario, request=None):
    """Restaura banco a partir de arquivo GZ"""
    import gzip
    import tempfile
    
    with gzip.open(gz_path, 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        restaurar_de_sql(tmp_path, usuario, request)
    finally:
        os.remove(tmp_path)

def restaurar_configuracoes(config_data):
    """Restaura configurações do sistema"""
    config, created = ConfiguracaoSistema.objects.get_or_create(id=1)
    
    config.nome_sistema = config_data.get('nome_sistema', config.nome_sistema)
    config.ano_lectivo_corrente = config_data.get('ano_lectivo_corrente')
    config.timezone = config_data.get('timezone', config.timezone)
    config.backup_auto = config_data.get('backup_auto', config.backup_auto)
    config.backup_frequencia = config_data.get('backup_frequencia', config.backup_frequencia)
    config.manter_backups_dias = config_data.get('manter_backups_dias', config.manter_backups_dias)
    config.smtp_server = config_data.get('smtp_server', config.smtp_server)
    config.smtp_port = config_data.get('smtp_port', config.smtp_port)
    config.smtp_user = config_data.get('smtp_user', config.smtp_user)
    config.email_sistema = config_data.get('email_sistema', config.email_sistema)
    
    config.save()
    update_django_settings(config)

def update_django_settings(config):
    """Atualiza configurações do Django"""
    # Atualizar settings em runtime (se necessário)
    settings.TIME_ZONE = config.timezone
    
    # Configurações de email
    if config.smtp_server and config.smtp_user:
        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        settings.EMAIL_HOST = config.smtp_server
        settings.EMAIL_PORT = config.smtp_port
        settings.EMAIL_HOST_USER = config.smtp_user
        settings.EMAIL_HOST_PASSWORD = config.smtp_password
        settings.EMAIL_USE_TLS = True
        settings.DEFAULT_FROM_EMAIL = config.email_sistema

# Agendador para backup automático
def verificar_backup_automatico():
    """Verifica se deve executar backup automático"""
    try:
        config = ConfiguracaoSistema.objects.first()
        if not config or not config.backup_auto:
            return
        
        # Verificar último backup
        ultimo_backup = BackupSistema.objects.first()
        
        deve_executar = False
        
        if config.backup_frequencia == 'daily':
            if not ultimo_backup or ultimo_backup.data_criacao.date() < timezone.now().date():
                deve_executar = True
        elif config.backup_frequencia == 'weekly':
            if not ultimo_backup or ultimo_backup.data_criacao < timezone.now() - timedelta(days=7):
                deve_executar = True
        elif config.backup_frequencia == 'monthly':
            if not ultimo_backup or ultimo_backup.data_criacao < timezone.now() - timedelta(days=30):
                deve_executar = True
        
        if deve_executar:
            # Executar backup automático
            criar_backup_automatico()
            
            # Limpar backups antigos
            limpar_backups_antigos(config.manter_backups_dias)
            
    except Exception as e:
        print(f"Erro no backup automático: {e}")

def criar_backup_automatico():
    """Cria backup automático do sistema"""
    try:
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_backup = f'backup_auto_{timestamp}.zip'
        caminho_backup = os.path.join(backup_dir, nome_backup)
        
        with zipfile.ZipFile(caminho_backup, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Backup do banco de dados
            sql_backup = export_database_to_sql()
            zipf.writestr(f'backup_auto_{timestamp}/database.sql', sql_backup)
            
            # Backup de mídia
            add_media_to_zip(zipf, f'backup_auto_{timestamp}')
            
            # Informações
            info = {
                'tipo': 'automático',
                'data_criacao': datetime.now().isoformat(),
            }
            zipf.writestr(f'backup_auto_{timestamp}/info.json', json.dumps(info, indent=2))
        
        tamanho = os.path.getsize(caminho_backup)
        
        BackupSistema.objects.create(
            nome=nome_backup,
            caminho=caminho_backup,
            tamanho=format_file_size(tamanho),
            descricao='Backup automático do sistema',
            criado_por=None
        )
        
    except Exception as e:
        print(f"Erro no backup automático: {e}")

def limpar_backups_antigos(dias_manter):
    """Remove backups mais antigos que o período definido"""
    try:
        data_limite = timezone.now() - timedelta(days=dias_manter)
        backups_antigos = BackupSistema.objects.filter(data_criacao__lt=data_limite)
        
        for backup in backups_antigos:
            if os.path.exists(backup.caminho):
                os.remove(backup.caminho)
            backup.delete()
            
    except Exception as e:
        print(f"Erro ao limpar backups antigos: {e}")