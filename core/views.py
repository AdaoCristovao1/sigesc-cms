from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Usuario
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from administracao.models import *
from django.contrib.auth.hashers import make_password
import unicodedata
from django.core.serializers.json import DjangoJSONEncoder
from pedagogico.models import *
from django.http import JsonResponse
import json
from decimal import Decimal, ROUND_HALF_UP
from financeiro.views import atualizar_estado_aluno
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponse
from datetime import datetime
import random 
import string
from django.db import transaction
from reportlab.graphics.barcode import createBarcodeDrawing
import io
import base64 
from django.http import HttpResponse
import uuid

def login_view(request):
    aluno = Aluno.objects.all()
    for a in aluno:
        atualizar_estado_aluno(a)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            
            perfil = user.perfil
 
            # Redirecionamento baseado no perfil 
            if perfil in ['admin_central', 'diretor_geral', 'secretario_geral']:
                return redirect('core:dashboard')
            elif perfil in ['diretor_admin', 'secretario_admin', 'coordenador_turno']:
                return redirect('administracao:dashboard')
            elif perfil in ['diretor_pedagogico', 'secretario_ped', 'coordenador_turma', 'coordenador_disc', 'professor']:
                return redirect('pedagogico:dashboard')
            elif perfil in ['aluno']:
                return redirect('estudante:aluno_home')
            else:
                messages.error(request, 'Perfil de usuário não reconhecido.')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'core/index.html')

def logout_view(request):
    logout(request)
    return redirect('core:login')

@login_required
def dashboard(request):
    aluno = Aluno.objects.all()
    for a in aluno:
        atualizar_estado_aluno(a)

    perfil = request.user.perfil
    usuario = request.user

    ano_letivo = AnoLectivo.objects.filter(estado='Aberto').last()
    professores_total = Funcionario.objects.filter(funcao__icontains='professor').count()
    funcionarios_total = Funcionario.objects.exclude(funcao__icontains='professor').count()
    aluno_total = Reconfirmacao.objects.filter(ano_letivo=ano_letivo).count()
    aluno_inadimplentes_total = Reconfirmacao.objects.filter(ano_letivo=ano_letivo, estado='Inadimplente').count()
    context ={
        'usuario':usuario,
        'professores_total': professores_total,
        'funcionarios_total':funcionarios_total,
        'aluno_total':aluno_total,
        'aluno_inadimplentes_total':aluno_inadimplentes_total,
    }

    if perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/dashboard-sg.html', context)
        
    elif perfil == 'diretor_geral':
        return render(request, 'core/dashboard.html', context)
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
def usuarios(request):
    q = request.GET.get('q')
    if q:
        filtro = Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        alunos = Usuario.objects.filter(filtro, perfil='aluno')
        outros = Usuario.objects.filter(filtro).exclude(perfil='aluno')
    else:
        alunos = Usuario.objects.filter(perfil='aluno')
        outros = Usuario.objects.exclude(perfil='aluno')
    
    perfil = request.user.perfil
    usuario = request.user

    if perfil == 'diretor_geral':
        return render(request, 'core/usuarios-list.html', {
            'alunos': alunos,
            'outros': outros,
            'usuario':usuario,
        })
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/usuarios-list.html', {
            'alunos': alunos,
            'outros': outros,
            'usuario':usuario,
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

@csrf_exempt
@login_required
def verificar_acao_usuario(request):
    if request.method == 'POST':
        senha = request.POST.get('senha')
        acao = request.POST.get('acao')
        usuario_id = request.POST.get('usuario_id')
        usuario_alvo = get_object_or_404(Usuario, id=usuario_id)

        user = authenticate(username=request.user.username, password=senha)

        if user is not None:
            if acao == 'editar':
                pass
            elif acao == 'excluir':
                usuario_alvo.delete()
                messages.success(request, 'Usuário excluído com sucesso.')
                return redirect('core:usuarios')
        else:
            messages.error(request, 'Senha incorreta.')
            return redirect('core:usuarios')
        
@csrf_exempt
@login_required
def confirmar_acao_funcionario(request):
    if request.method == 'POST':
        acao = request.POST.get('acao')
        funcionario_id = request.POST.get('funcionario_id')
        senha = request.POST.get('senha')

        usuario = request.user
        autenticado = authenticate(username=usuario.username, password=senha)

        if not autenticado:
            messages.error(request, 'Senha incorreta.')
            return redirect('core:cadastrar_funcionario')

        if acao == 'editar':
            nome = request.POST.get('nome')
            bi = request.POST.get('bilhete')
            genero = request.POST.get('genero')
            funcao = request.POST.get('funcao')
            telefone = request.POST.get('telefone')

            funcionario = Funcionario.objects.get(id=funcionario_id)
            funcionario.nome = nome
            funcionario.bi = bi
            funcionario.genero = genero
            funcionario.funcao = funcao
            funcionario.telefone = telefone
            funcionario.save()

            # Atualiza o usuário correspondente
            nomes = remover_acentos(nome.lower()).split()
            primeiro_nome = nomes[0]
            ultimo_nome = nomes[-1] if len(nomes) > 1 else nomes[0]
            codigo_unico = str(uuid.uuid4())[:5]
            email = f"{primeiro_nome}{ultimo_nome}{codigo_unico}@sigesc.co.ao"

            try:
                usuario_sistema = Usuario.objects.get(username__iexact=email)
            except Usuario.DoesNotExist:
                # Se não existir, cria novo
                usuario_sistema = Usuario.objects.create_user(
                    username=email,
                    email=email,
                    password=bi,
                    first_name=primeiro_nome,
                    last_name=ultimo_nome,
                    perfil=funcao
                )
            else:
                # Se existir, atualiza
                usuario_sistema.username = email
                usuario_sistema.email = email
                usuario_sistema.first_name = primeiro_nome
                usuario_sistema.last_name = ultimo_nome
                usuario_sistema.perfil = funcao
                usuario_sistema.save() 

            messages.success(request, f"Funcionário '{nome}' atualizado com sucesso.")

            return redirect('core:cadastrar_funcionario')

        return redirect('core:cadastrar_funcionario')

def remover_acentos(texto):
    # Remove acentos e caracteres especiais
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).replace('ç', 'c').replace('Ç', 'C')

@login_required
def cadastrar_funcionario(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        bilhete = request.POST.get('bilhete')
        genero = request.POST.get('genero')
        funcao = request.POST.get('funcao')
        telefone = request.POST.get('telefone')
        salario = request.POST.get('salario')

        # Salva o funcionário
        funcionario = Funcionario.objects.create(
            nome=nome,
            bi=bilhete,
            genero=genero,
            funcao=funcao,
            telefone=telefone,
            salario=salario
        )

        nomes = remover_acentos(nome.lower()).split()
        primeiro_nome = nomes[0] 
        ultimo_nome = nomes[-1] if len(nomes) > 1 else nomes[0]
        codigo_unico = str(uuid.uuid4())[:5]
        email = f"{primeiro_nome}{ultimo_nome}{codigo_unico}@sigesc.co.ao"

        # Cria o usuário vinculado
        usuario = Usuario.objects.create_user(
            username=email,
            email=email,
            password=bilhete,
            first_name=primeiro_nome,
            last_name=ultimo_nome,
            perfil=funcao,
        )

        funcionario.usuario = usuario
        funcionario.save()

        messages.success(request, f"Funcionário {nome} cadastrado com sucesso!")
        return redirect('core:cadastrar_funcionario')

    q = request.GET.get('q') 
    if q:
        filtro = (
            Q(nome__icontains=q) |
            Q(bi__icontains=q) |
            Q(funcao__icontains=q) |
            Q(telefone__icontains=q)
        )
        funcionarios = Funcionario.objects.filter(filtro)
    else:
        funcionarios = Funcionario.objects.all()
    perfil = request.user.perfil
    usuario = request.user

    if perfil == 'diretor_geral':
        return render(request, 'core/form-func.html', {
            'funcionarios': funcionarios,
            'usuario':usuario,
        })
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/form-func.html', {
            'funcionarios': funcionarios,
            'usuario':usuario,
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

@csrf_exempt
def confirmar_acao_funcionario(request):
    if request.method == 'POST':
        acao = request.POST.get('acao')
        funcionario_id = request.POST.get('funcionario_id')
        senha = request.POST.get('senha')

        usuario = request.user
        autenticado = authenticate(username=usuario.username, password=senha)

        if not autenticado:
            messages.error(request, 'Senha incorreta.')
            return redirect('core:cadastrar_funcionario')

        if acao == 'editar':
            nome = request.POST.get('nome')
            bi = request.POST.get('bilhete')
            genero = request.POST.get('genero')
            funcao = request.POST.get('funcao')
            telefone = request.POST.get('telefone')
            salario = request.POST.get('salario')

            funcionario = Funcionario.objects.get(id=funcionario_id)
            funcionario.nome = nome
            funcionario.bi = bi
            funcionario.genero = genero
            funcionario.funcao = funcao
            funcionario.telefone = telefone
            funcionario.salario = salario
            funcionario.save()

            # Atualiza o usuário correspondente
            nomes = remover_acentos(nome.lower()).split()
            primeiro_nome = nomes[0]
            ultimo_nome = nomes[-1] if len(nomes) > 1 else nomes[0]
            email = f"{primeiro_nome}{ultimo_nome}@sigesc.co.ao"

            try:
                usuario_sistema = Usuario.objects.get(username__iexact=email)
            except Usuario.DoesNotExist:
                # Se não existir, cria novo
                usuario_sistema = Usuario.objects.create_user(
                    username=email,
                    email=email,
                    password=bi,
                    first_name=primeiro_nome,
                    last_name=ultimo_nome,
                    perfil=funcao
                )
            else:
                # Se existir, atualiza
                usuario_sistema.username = email
                usuario_sistema.email = email
                usuario_sistema.set_password(bi)
                usuario_sistema.first_name = primeiro_nome
                usuario_sistema.last_name = ultimo_nome
                usuario_sistema.perfil = funcao
                usuario_sistema.save()

            messages.success(request, f"Funcionário '{nome}' atualizado com sucesso.")
            return redirect('core:cadastrar_funcionario')

        return redirect('core:cadastrar_funcionario')

@csrf_exempt
def excluir_funcionario(request):
    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario_id')
        funcionario = get_object_or_404(Funcionario, id=funcionario_id)

        nomes = remover_acentos(funcionario.nome.lower()).split()
        primeiro_nome = nomes[0]
        ultimo_nome = nomes[-1] if len(nomes) > 1 else primeiro_nome
        email_usuario = f"{primeiro_nome}{ultimo_nome}@sigesc.co.ao"

        try:
            usuario = Usuario.objects.get(username=email_usuario)
            usuario.delete()
        except Usuario.DoesNotExist:
            pass

        funcionario.delete()
        messages.success(request, f"Funcionário e usuário ({email_usuario}) excluídos com sucesso!")
        return redirect('core:cadastrar_funcionario')

@login_required
def docentes(request):
    q = request.GET.get('q') 
    if q:
        filtro = (
            Q(nome__icontains=q) |
            Q(bi__icontains=q) |
            Q(telefone__icontains=q)
        )
        funcionarios = Funcionario.objects.filter(filtro, funcao='professor')
    else:
        funcionarios = Funcionario.objects.filter(funcao='professor')

    perfil = request.user.perfil
    usuario = request.user 

    if perfil == 'diretor_geral':
        return render(request, 'core/docentes.html',  {'funcionarios': funcionarios, 'usuario':usuario})
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/docentes.html',  {'funcionarios': funcionarios, 'usuario':usuario})
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
def vinculo_docente(request, professor_id, vinculo_id=None):
    """
    View unificada para criar (se vinculo_id=None) ou editar vínculos de docentes.
    Gerencia tanto o vínculo quanto os horários associados.
    """
    # Verificar perfil do usuário primeiro
    perfil = request.user.perfil
    if perfil not in ['diretor_geral', 'secretario_geral', 'diretor_pedagogico', 'secretario_ped']:
        return HttpResponse("""
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
    
    # Obter professor
    professor = get_object_or_404(Funcionario, id=professor_id, funcao__icontains='professor')
    
    # Determinar se é criação ou edição
    modo_edicao = vinculo_id is not None
    
    if modo_edicao:
        # Modo edição - obter vínculo existente
        vinculo = get_object_or_404(ProfessorVinculo, id=vinculo_id, professor=professor)
    else:
        # Modo criação - vínculo será criado
        vinculo = None
    
    # Obter dados para o formulário
    turmas = Turma.objects.select_related('classe', 'curso').all()
    disciplinas = Disciplina.objects.all()
    
    # Serializar turmas para JS
    turmas_json = json.dumps([
        {
            'id': t.id,
            'nome': t.nome,
            'turno': t.turno,
            'curso_nome': t.curso.nome,
            'classe_numero': t.classe.numero
        } for t in turmas
    ])
    
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            turma_id = request.POST.get('turma')
            disciplina_id = request.POST.get('disciplina')
            
            # Validações
            if not turma_id or not disciplina_id:
                messages.error(request, 'Turma e disciplina são obrigatórios.')
            else:
                turma = get_object_or_404(Turma, id=turma_id)
                disciplina = get_object_or_404(Disciplina, id=disciplina_id)
                
                # Dados das listas de horários
                dias = request.POST.getlist('dia_semana[]')
                inicios = request.POST.getlist('hora_inicio[]')
                fims = request.POST.getlist('hora_fim[]')
                tempos = request.POST.getlist('tempo_aula[]')
                horarios_ids = request.POST.getlist('horario_id[]')  # IDs para edição
                
                # Verificar se há horários válidos
                horarios_validos = any(dias[i] and inicios[i] and fims[i] for i in range(len(dias)))
                if not horarios_validos:
                    messages.error(request, 'Pelo menos um horário válido deve ser definido.')
                else:
                    if modo_edicao:
                        # Atualizar vínculo existente
                        print("Editando....")
                        vinculo.turma = turma
                        vinculo.disciplina = disciplina
                        vinculo.save()
                        
                        # Criar lista de horários que devem ser mantidos
                        horarios_para_manter = []
                        
                        # Processar cada horário do formulário
                        for i in range(len(dias)):
                            if dias[i] and inicios[i] and fims[i]:
                                horario_data = {
                                    'vinculo': vinculo,
                                    'dia_semana': dias[i],
                                    'hora_inicio': inicios[i],
                                    'hora_fim': fims[i],
                                    'tempo_aula': tempos[i] if i < len(tempos) and tempos[i] else 1,
                                }
                                
                                # Verificar se é um horário existente (tem ID)
                                if i < len(horarios_ids) and horarios_ids[i]:
                                    # Atualizar horário existente
                                    horario = get_object_or_404(HorarioAula, id=horarios_ids[i], vinculo=vinculo)
                                    horario.dia_semana = horario_data['dia_semana']
                                    horario.hora_inicio = horario_data['hora_inicio']
                                    horario.hora_fim = horario_data['hora_fim']
                                    horario.tempo_aula = horario_data['tempo_aula']
                                    horario.save()
                                    horarios_para_manter.append(horario.id)
                                else:
                                    # Criar novo horário
                                    novo_horario = HorarioAula.objects.create(**horario_data)
                                    horarios_para_manter.append(novo_horario.id)
                        
                        # Remover horários que não estão mais no formulário
                        vinculo.horarios.exclude(id__in=horarios_para_manter).delete()
                        
                        messages.success(request, 'Vínculo atualizado com sucesso!')
                    else:
                        # Criar novo vínculo
                        vinculo = ProfessorVinculo.objects.create(
                            professor=professor,
                            disciplina=disciplina,
                            turma=turma
                        )
                        
                        # Criar os Horários associados
                        for i in range(len(dias)):
                            if dias[i] and inicios[i] and fims[i]:
                                HorarioAula.objects.create(
                                    vinculo=vinculo,
                                    dia_semana=dias[i],
                                    hora_inicio=inicios[i],
                                    hora_fim=fims[i],
                                    tempo_aula=tempos[i] if i < len(tempos) and tempos[i] else 1
                                )
                        
                        messages.success(request, 'Vínculo criado com sucesso!')
                    
                    # Redirecionar para a lista de docentes
                    if perfil == 'diretor_geral':
                        return redirect('core:docentes')
                    if perfil == 'diretor_pedagogico' or perfil == 'secretario_ped':
                        return redirect('pedagogico:docentes')
                    else:  # secretario_geral
                        return redirect('core:docentes')
        
        except Exception as e:
            messages.error(request, f'Erro ao salvar: {str(e)}')
    
    # Preparar contexto para o template
    context = {
        'professor': professor,
        'turmas': turmas,
        'disciplinas': disciplinas,
        'turmas_json': turmas_json,
        'usuario': request.user,
        'modo_edicao': modo_edicao,
        'vinculo': vinculo,
    }
    
    # Determinar qual template usar baseado no perfil
    if perfil == 'diretor_geral':
        template = 'core/vinculo-docente.html'
    if perfil == 'diretor_pedagogico':
        template = 'pedagogico/diretor_pedagogico/vinculo-docente.html'
    if perfil == 'secretario_ped':
        template = 'pedagogico/secretario_ped/vinculo-docente.html'
    else:  # secretario_geral
        template = 'core/secretario_geral/vinculo-docente.html'
    
    return render(request, template, context)

@login_required
def excluir_vinculo_docente(request, vinculo_id):
    """
    Excluir um vínculo e todos os seus horários
    """
    # Verificar perfil
    perfil = request.user.perfil
    
    # Obter e excluir o vínculo
    vinculo = get_object_or_404(ProfessorVinculo, id=vinculo_id)
    professor_nome = vinculo.professor.nome
    
    if request.method == 'POST':
        vinculo.delete()
        messages.success(request, f'Vínculo de {professor_nome} excluído com sucesso!')
        if perfil in ['diretor_pedagogico', 'secretario_ped']:
            return redirect('pedagogico:docentes')
        return redirect('core:docentes')
    
    # Se GET, mostrar página de confirmação
    context = {
        'vinculo': vinculo,
        'usuario': request.user,
    }
    
    if perfil == 'diretor_geral':
        return render(request, 'core/excluir_vinculo.html', context)
    elif perfil in ['diretor_pedagogico']:
        return render(request, 'pedagogico/diretor_pedagogico/excluir_vinculo.html', context)
    elif perfil in ['secretario_ped']:
        return render(request, 'pedagogico/secretario_ped/excluir_vinculo.html', context)
    else:
        return render(request, 'core/secretario_geral/excluir_vinculo.html', context)

@login_required
def detalhes_professor(request, id):
    print("==== INÍCIO detalhes_professor ====")
    print("ID recebido:", id)

    professor = get_object_or_404(
        Funcionario,
        pk=id,
        funcao__icontains='professor'
    )

    print("Professor:", professor.nome)

    vinculos = professor.professorvinculo_set.select_related(
        'turma', 'disciplina', 'turma__classe', 'turma__curso'
    ).prefetch_related(
        models.Prefetch(
            'horarios',
            queryset=HorarioAula.objects.order_by('dia_semana', 'hora_inicio')
        )
    )
    print("Professor ID:", professor.id)
    print("Vínculos encontrados:", professor.professorvinculo_set.count())

    print("Total de vínculos:", vinculos.count())

    data_detalhada = []

    for v in vinculos:
        print(f"\nVínculo ID: {v.id}")
        print("  Disciplina:", v.disciplina.nome)
        print("  Turma:", v.turma.nome)

        horarios = v.horarios.all()
        print("  Total de horários neste vínculo:", horarios.count())

        for h in horarios:
            print(
                f"    Horário -> Dia: {h.get_dia_semana_display()} | "
                f"Início: {h.hora_inicio} | Fim: {h.hora_fim}"
            )

            data_detalhada.append({
                'disciplina': v.disciplina.nome,
                'turma': v.turma.nome,
                'classe': f"{v.turma.classe.numero}ª",
                'curso': v.turma.curso.nome,
                'turno': v.turma.turno,
                'tempo': f"{h.tempo_aula}º tempo" if h.tempo_aula else "---",
                'dia': h.get_dia_semana_display(),
                'inicio': h.hora_inicio.strftime('%H:%M'),
                'fim': h.hora_fim.strftime('%H:%M'),
            })

    print("\nTotal de horários coletados:", len(data_detalhada))

    print("\nAntes da ordenação:")
    for d in data_detalhada:
        print(f"  {d['dia']} - {d['inicio']}")

    data_detalhada.sort(key=lambda x: (x['dia'], x['inicio']))

    print("\nDepois da ordenação:")
    for d in data_detalhada:
        print(f"  {d['dia']} - {d['inicio']}")

    print("==== FIM detalhes_professor ====\n")

    return JsonResponse({
        'nome': professor.nome,
        'nivel_academico': professor.nivel_academico or "---",
        'area_formacao': professor.area_formacao or "---",
        'horario_completo': data_detalhada,
        'total_horarios': len(data_detalhada)
    })

@login_required
def alunos(request):
    aluno = Aluno.objects.all()
    for a in aluno:
        atualizar_estado_aluno(a)
        
    anos_disponiveis = AnoLectivo.objects.all().order_by('-ano')
     
    ano_letivo = request.GET.get("ano_lectivo")

    if not ano_letivo:
        ano_letivo = AnoLectivo.objects.filter(estado='Aberto').last()

    query = request.GET.get('q', '')
    turmas = Turma.objects.select_related('classe', 'curso', 'sala').filter(ano_letivo=ano_letivo)
    turmas_json = json.dumps([
        {
            'id': turma.id,
            'nome': turma.nome,
            'classe': turma.classe.id if turma.classe else None,
            'curso_id': turma.curso.id if turma.curso else None,
            'curso_nome': turma.curso.nome if turma.curso else '',
            'sala_id': turma.sala.id if turma.sala else None,
            'sala_nome': turma.sala.nome if turma.sala else '',
            'turno': turma.turno
        }
        for turma in turmas
    ])

    professores = Funcionario.objects.filter(funcao__icontains='professor')
    disciplinas = Disciplina.objects.all

    # Base query
    reconfirmacoes = Reconfirmacao.objects.select_related(
        'aluno', 'turma', 'sala', 'classe', 'curso'
    ).filter(ano_letivo=ano_letivo)

    # Filtro de pesquisa
    if query:
        reconfirmacoes = reconfirmacoes.filter(
            Q(aluno__nome_completo__icontains=query) |
            Q(aluno__numero_mecanografico__icontains=query) |
            Q(turma__nome__icontains=query)
        )

    perfil = request.user.perfil

    # Agrupar já filtrado
    turmas_agrupadas = {}
    for r in reconfirmacoes.order_by('classe__numero', 'turma__nome', 'aluno__nome_completo'):
        key = (
            f"{r.classe.numero}ª Classe - Turma: {r.turma.nome} "
            f"- Sala: {r.sala.nome if r.sala else '---'} "
            f"- Curso: {r.curso.nome if r.curso else '---'} "
            f"- Turno: {getattr(r.turma, 'turno', '---')}"
        )
        turmas_agrupadas.setdefault(key, []).append(r.aluno)

    usuario = request.user

    context = {
        'turmas_agrupadas': turmas_agrupadas,
        'search_query': query,
        'ano_letivo': ano_letivo,
        'usuario':usuario,
        'turmas':turmas,
        'classes': Classe.objects.all(),
        'turmas_json':turmas_json,
        'professores':professores,
        'disciplinas':disciplinas,
        'anos_disponiveis':anos_disponiveis
    }

    # Renderizar conforme perfil
    if perfil == 'diretor_geral':
        return render(request, 'core/alunos.html', context)
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/alunos.html', context)
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
def editar_aluno(request, aluno_id):
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto').last()
    
    if request.method != 'POST':
        return redirect('core:alunos_lista')
    
    # Buscar o objeto Aluno
    aluno = get_object_or_404(Aluno, id=aluno_id)
    
    try:
        # Atualizar os dados pessoais do aluno
        aluno.nome_completo = request.POST.get('nome_completo', aluno.nome_completo)
        aluno.bi = request.POST.get('bi', aluno.bi)
        aluno.genero = request.POST.get('genero', aluno.genero)
        aluno.naturalidade = request.POST.get('naturalidade', aluno.naturalidade)
        
        # Atualizar data de nascimento
        aluno.dia_nasc = request.POST.get('dia_nasc', aluno.dia_nasc)
        aluno.mes_nasc = request.POST.get('mes_nasc', aluno.mes_nasc)
        aluno.ano_nasc = request.POST.get('ano_nasc', aluno.ano_nasc)
        
        # Atualizar nomes dos pais
        aluno.nome_pai = request.POST.get('nome_pai', aluno.nome_pai)
        aluno.nome_mae = request.POST.get('nome_mae', aluno.nome_mae)
        
        # Verificar se a turma foi alterada
        nova_turma_id = request.POST.get('turma')
        turma_alterada = False
        
        if nova_turma_id and str(aluno.turma_id) != nova_turma_id:
            nova_turma = get_object_or_404(Turma, id=nova_turma_id)
            aluno.turma = nova_turma
            turma_alterada = True
            
            # Atualizar campos relacionados à turma
            aluno.classe = nova_turma.classe
            aluno.curso = nova_turma.curso
            aluno.sala = nova_turma.sala
            aluno.turno = nova_turma.turno
        
        # Salvar alterações do aluno
        aluno.save()
        
        # Atualizar a reconfirmação se existir e o ano letivo estiver aberto
        if ano_letivo:
            reconfirmacao = Reconfirmacao.objects.filter(
                aluno=aluno, 
                ano_letivo=ano_letivo.ano 
            ).first()
            
            if reconfirmacao and turma_alterada:
                reconfirmacao.turma = aluno.turma
                reconfirmacao.sala = aluno.sala
                reconfirmacao.classe = aluno.classe
                reconfirmacao.curso = aluno.curso
                reconfirmacao.turno = aluno.turno
                reconfirmacao.save()
                messages.info(request, "A turma do aluno foi alterada e a reconfirmação atualizada.")
        
        messages.success(request, f"Aluno {aluno.nome_completo} atualizado com sucesso.")
        
    except Exception as e:
        messages.error(request, f"Erro ao atualizar aluno: {str(e)}")
    
    return redirect('core:alunos_lista')

@login_required
def aluno_detalhes(request, id): 
    aluno = get_object_or_404(Aluno, pk=id)
    atualizar_estado_aluno(aluno)
    
    ultima_reconfirmacao = Reconfirmacao.objects.filter(aluno=aluno).order_by('-ano_letivo').last()
    
    notas = Nota.objects.filter(aluno=aluno).select_related('disciplina', 'classe')
    
    medias = {}
    disciplinas = Disciplina.objects.all()
    disc = Disciplina.objects.all()

    for nota in notas.order_by('classe__numero', 'disciplina__nome', 'trimestre'):
        ano = nota.classe.numero
        nome_disciplina = nota.disciplina.nome
        trimestre = nota.trimestre
        valor = nota.valor 
        nota_id = nota.id 

        # Inicialização da estrutura
        if ano not in medias:
            medias[ano] = {}
        if nome_disciplina not in medias[ano]:
            medias[ano][nome_disciplina] = {
                'notas': {},
                'media': '--',
                'nota_ids': {}
            }

        # Guardar nota
        medias[ano][nome_disciplina]['notas'][trimestre] = valor
        medias[ano][nome_disciplina]['nota_ids'][trimestre] = nota_id

    # Calcular média
    for ano, disciplinas in medias.items():
        for nome, dados in disciplinas.items():
            notas_dict = dados['notas']
            t1 = notas_dict.get(1)
            t2 = notas_dict.get(2)
            t3 = notas_dict.get(3)
            t4 = notas_dict.get(4)

            if t1 is not None and t2 is not None and t3 is not None and t4 is not None:
                media = ((t1 + t2 + t3) / 3 * Decimal('0.4')) + (t4 * Decimal('0.6'))
                media = Decimal(media).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
                medias[ano][nome]['media'] = float(media)

    perfil = request.user.perfil
    usuario = request.user
    
    if perfil == 'diretor_geral':
        return render(request, 'core/aluno-detalhe.html', {
            'aluno': aluno,
            'ultima_reconfirmacao': ultima_reconfirmacao,
            'medias': medias,
            'disciplinas': disciplinas,
            'disc':disc,
            'usuario':usuario
        })
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/aluno-detalhe.html', {
            'aluno': aluno,
            'ultima_reconfirmacao': ultima_reconfirmacao,
            'medias': medias,
            'disciplinas': disciplinas,
            'disc':disc,
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

@login_required
def upload_foto_aluno(request, id):
    aluno = get_object_or_404(Aluno, pk=id)

    if request.method == 'POST' and request.FILES.get('foto'):
        aluno.foto = request.FILES['foto']
        aluno.save()
        messages.success(request, 'Foto atualizada com sucesso.')
    else:
        messages.error(request, 'Nenhuma imagem foi enviada.')

    return redirect('core:aluno_detalhes', id=aluno.id)

@login_required
def lancar_nota(request):
    if request.method == 'POST':
        aluno_id = request.POST.get('aluno_id')
        disciplina_id = request.POST.get('disciplina_id')
        classe_id = request.POST.get('classe_id')
        ano_letivo_id = AnoLectivo.objects.filter(estado='Aberto').last()
        if ano_letivo_id:
            ano_letivo_id = ano_letivo_id.id
 
        trimestre = request.POST.get('trimestre')
        valor = request.POST.get('valor')

        if not all([aluno_id, disciplina_id, classe_id, ano_letivo_id, trimestre, valor]):
            messages.error(request, 'Todos os campos são obrigatórios.')
            return redirect(request.META.get('HTTP_REFERER'))

        try:
            nota_existente = Nota.objects.filter(
                ano_lectivo=ano_letivo_id,
                aluno=aluno_id,
                classe=classe_id,
                disciplina=disciplina_id,
                trimestre=trimestre
            ).first()

            if nota_existente:
                messages.warning(request, 'Nota já foi lançada para este aluno nesta disciplina e trimestre.')
            else:
                Nota.objects.create(
                    aluno_id=aluno_id,
                    disciplina_id=disciplina_id,
                    classe_id=classe_id,
                    ano_lectivo_id=ano_letivo_id,
                    trimestre=trimestre,
                    valor=valor
                )
                messages.success(request, 'Nota lançada com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao lançar nota: {e}')

        return redirect(request.META.get('HTTP_REFERER')) 
    
@login_required
def deletar_nota(request):
    if request.method == 'POST':
        nota_id = request.POST.get('nota_id')
        trimestre = request.POST.get('trimestre')
        
        if not nota_id:
            messages.error(request, 'ID da nota não fornecido.')
            return redirect(request.META.get('HTTP_REFERER'))
        
        try:
            nota = Nota.objects.get(id=nota_id)
            
            # Verificar permissões baseado no perfil do usuário
            perfil = request.user.perfil
            if perfil not in ['diretor_geral', 'diretor_pedagogico']:
                messages.error(request, 'Você não tem permissão para deletar notas.')
                return redirect(request.META.get('HTTP_REFERER'))
            
            # Salvar informações para mensagem
            disciplina_nome = nota.disciplina.nome if nota.disciplina else "Desconhecida"
            valor_nota = nota.valor
            
            trimestre_nomes = {
                '1': '1º Trimestre',
                '2': '2º Trimestre', 
                '3': '3º Trimestre',
                '4': 'Exame'
            }
            trimestre_nome = trimestre_nomes.get(str(trimestre), f'Trimestre {trimestre}')
            
            # Deletar a nota
            nota.delete()
            
            messages.success(request, f'Nota {valor_nota} da disciplina {disciplina_nome} no {trimestre_nome} foi deletada com sucesso.')
            
        except Nota.DoesNotExist:
            messages.error(request, 'Nota não encontrada.')
        except Exception as e:
            messages.error(request, f'Erro ao deletar nota: {e}')
        
        return redirect(request.META.get('HTTP_REFERER'))
    
    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def classes(request):
    classes = Classe.objects.all().order_by('numero')

    perfil = request.user.perfil 
    usuario = request.user   
     
    if perfil == 'diretor_geral':
        return render(request, 'core/classes.html', {'classes': classes, 'usuario':usuario})
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
def criar_classe(request):
    if request.method == 'POST':
        Classe.objects.create(
            designacao=request.POST['designacao'],
            numero=request.POST['numero']
        )
    return redirect('core:classes')

@login_required
def atualizar_classe(request):
    if request.method == 'POST':
        classe = get_object_or_404(Classe, pk=request.POST['id'])
        classe.designacao = request.POST['designacao']
        classe.numero = request.POST['numero']
        classe.save()
    return redirect('core:classes')

@login_required
def eliminar_classe(request, id):
    classe = get_object_or_404(Classe, pk=id)
    classe.delete()
    return redirect('core:classes')

@login_required
def cursos(request):
    cursos = Curso.objects.all().order_by('nome')
    perfil = request.user.perfil   
    usuario = request.user
     
    if perfil == 'diretor_geral':
        return render(request, 'core/cursos.html', {'cursos': cursos, 'usuario':usuario})
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
def criar_curso(request):
    if request.method == 'POST':
        Curso.objects.create(
            nome=request.POST['nome'],
        )
    return redirect('core:cursos')

@login_required
def atualizar_curso(request):
    if request.method == 'POST':
        curso = get_object_or_404(Curso, pk=request.POST['id'])
        curso.nome = request.POST['nome']
        curso.save()
    return redirect('core:cursos')

@login_required
def eliminar_curso(request, id):
    curso = get_object_or_404(Curso, pk=id)
    curso.delete()
    return redirect('core:cursos')


@login_required
def editar_nota(request):
    if request.method == 'POST':
        aluno_id = request.POST.get('aluno_id')
        disciplina_nome = request.POST.get('disciplina_nome')
        classe_id = request.POST.get('classe_id')
        trimestre = int(request.POST.get('trimestre'))
        valor = request.POST.get('valor')

        aluno = get_object_or_404(Aluno, id=aluno_id)
        disciplina = get_object_or_404(Disciplina, nome=disciplina_nome)
        classe = get_object_or_404(Classe, id=classe_id)
        ano_letivo = AnoLectivo.objects.filter(estado='Aberto').last()

        # validação de valor
        if not valor:
            messages.error(request, "O campo valor é obrigatório.")
            return redirect('core:aluno_detalhes', aluno_id)

        try:
            valor = float(valor)
        except ValueError:
            messages.error(request, "O valor deve ser numérico.")
            return redirect('core:aluno_detalhes', aluno_id)

        nota, created = Nota.objects.get_or_create(
            aluno=aluno,
            disciplina=disciplina,
            trimestre=trimestre,
            ano_lectivo=ano_lectivo,
            defaults={
                'classe': classe,
                'valor': valor
            }
        )

        if not created:
            nota.valor = valor
            nota.classe = nota.classe  
            nota.save()

        messages.success(request, "Nota atualizada com sucesso.")

    return redirect('core:aluno_detalhes', aluno_id)

@login_required
def turmas_e_salas(request):
    if request.method == 'POST':
        qtd_salas = int(request.POST.get('quantidade', 0))
        total_existentes = Sala.objects.count()

        if qtd_salas > total_existentes:
            for i in range(total_existentes + 1, qtd_salas + 1):
                Sala.objects.create(nome=str(i))
        elif qtd_salas < total_existentes:
           salas_para_excluir = Sala.objects.all().order_by('-id')[:total_existentes - qtd_salas]
           for sala in salas_para_excluir:
               sala.delete()


        return redirect('core:turmas_e_salas')
    
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto').last()

    salas = Sala.objects.all().order_by('id')
    turmas = Turma.objects.filter(ano_letivo=ano_letivo).order_by('id')
    classes = Classe.objects.all().order_by('id')
    cursos = Curso.objects.all().order_by('id')
    salas = Sala.objects.all().order_by('id')

    perfil = request.user.perfil  
    usuario = request.user 
     
    if perfil == 'diretor_geral':
        return render(request, 'core/turmas-salas.html', {'turmas': turmas, 'classes': classes, 'cursos': cursos, 'salas': salas,'total': salas.count(), 'usuario':usuario, 'ano_letivo':ano_letivo})
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/turmas-salas.html', {'turmas': turmas, 'classes': classes, 'cursos': cursos, 'salas': salas,'total': salas.count(), 'usuario':usuario, 'ano_letivo':ano_letivo})
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
def criar_turma(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        turno = request.POST.get('turno')
        classe_id = request.POST.get('classe')
        curso_id = request.POST.get('curso')
        sala_id = request.POST.get('sala')
        ano_letivo = AnoLectivo.objects.filter(estado='Aberto').last()

        if not (nome and turno and classe_id and curso_id):
            messages.error(request, "Todos os campos obrigatórios devem ser preenchidos.")
            return redirect(request.META.get('HTTP_REFERER'))

        # Verifica se a classe e curso existem
        classe = get_object_or_404(Classe, id=classe_id)
        curso = get_object_or_404(Curso, id=curso_id)

        # Valida se curso é "Base" quando a classe <= 9
        if classe.numero <= 9 and curso.nome.lower() != "base":
            messages.error(request, "Para classes do 1º ao 9º ano, o curso deve ser 'Base'.")
            return redirect(request.META.get('HTTP_REFERER'))

        # Valida se a sala tem menos de 3 turmas
        if sala_id:
            quantidade_turmas = Turma.objects.filter(sala_id=sala_id, ano_letivo=ano_letivo).count()
            if quantidade_turmas >= 3:
                messages.error(request, "Essa sala já está associada ao número máximo de 3 turmas.")
                return redirect(request.META.get('HTTP_REFERER'))

        # Verifica se já existe uma turma igual
        turma_existente = Turma.objects.filter(
            nome=nome,
            turno=turno,
            sala_id=sala_id,
            ano_letivo=ano_letivo,
        ).exists()

        if turma_existente:
            messages.error(request, "Já existe uma turma com o mesmo nome, turno e sala.")
            return redirect(request.META.get('HTTP_REFERER'))

        # Criação da turma
        turma = Turma(
            nome=nome,
            turno=turno,
            classe=classe,
            curso=curso,
            sala_id=sala_id if sala_id else None,
            ano_letivo=ano_letivo
        )
        turma.save()
        messages.success(request, f"Turma '{turma.nome}' criada com sucesso.")
        return redirect(request.META.get('HTTP_REFERER'))

    messages.error(request, "Requisição inválida.")
    return redirect(request.META.get('HTTP_REFERER')) 

@login_required
def editar_turma(request):
    if request.method == 'POST':
        turma_id = request.POST.get('id')
        turma = get_object_or_404(Turma, pk=turma_id)

        nome = request.POST.get('nome')
        turno = request.POST.get('turno')
        classe_id = request.POST.get('classe')
        curso_id = request.POST.get('curso')
        sala_id = request.POST.get('sala') or None

        # Verifica se a nova sala (se for diferente) já possui 3 turmas
        if sala_id and str(turma.sala_id) != str(sala_id):
            quantidade_turmas = Turma.objects.filter(sala_id=sala_id).count()
            if quantidade_turmas >= 3:
                messages.error(request, "Essa sala já está associada ao número máximo de 3 turmas.")
                return redirect(request.META.get('HTTP_REFERER'))

        turma.nome = nome
        turma.turno = turno
        turma.classe_id = classe_id
        turma.curso_id = curso_id
        turma.sala_id = sala_id

        turma.save()
        messages.success(request, f"Turma '{turma.nome}' atualizada com sucesso.")
        return redirect(request.META.get('HTTP_REFERER'))

@login_required
def eliminar_turma(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)

    if request.method == 'POST':
        nome = turma.nome
        turma.delete()
        messages.success(request, f"Turma '{nome}' eliminada com sucesso.")
        return redirect(request.META.get('HTTP_REFERER'))
    
    messages.error(request, "Requisição inválida.")
    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def listar_disciplinas(request):
    query = request.GET.get('q')
    if query:
        disciplinas = Disciplina.objects.filter(nome__icontains=query)
    else:
        disciplinas = Disciplina.objects.all()

    vinculacoes = DisciplinasClasse.objects.select_related('disciplina', 'classe').all()
    classes = Classe.objects.all()

    perfil = request.user.perfil
    usuario = request.user

    # Preparar dados para JSON com designação
    classes_data = list(classes.values('id', 'numero', 'designacao'))
    vinculadas_data = list(DisciplinasClasse.objects.values('id', 'disciplina_id', 'classe_id'))

    context = {
        'disciplinas': disciplinas,
        'classes': classes,
        'vinculacoes': vinculacoes,
        'classes_json': json.dumps(classes_data),
        'vinculadas_json': json.dumps(vinculadas_data),
        'usuario': usuario,
    }
    
    if perfil == 'diretor_geral': 
        return render(request, 'core/disciplinas.html', context)
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/disciplinas.html', context)
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
def criar_disciplina(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if nome:
            Disciplina.objects.create(nome=nome, classe = 0)
            messages.success(request, 'Disciplina criada com sucesso.')
    return redirect('core:disciplinas')

@login_required
def editar_disciplina(request, id):
    disciplina = get_object_or_404(Disciplina, id=id)
    if request.method == 'POST':
        disciplina.nome = request.POST.get('nome')
        disciplina.save()
        messages.success(request, 'Disciplina atualizada.')
        return redirect('core:disciplinas') 

@login_required
def deletar_disciplina(request, id):
    disciplina = get_object_or_404(Disciplina, id=id)
    if request.method == 'POST':
        senha = request.POST.get('password')
        
        disciplina.delete()
        messages.success(request, 'Disciplina deletada com sucesso.')
    return redirect('core:disciplinas')

@login_required
def criar_vinculo(request):
    if request.method == "POST":
        disciplina_id = request.POST.get("disciplina")
        # Captura a lista de IDs das classes selecionadas no formulário
        classes_ids_recebidos = request.POST.getlist("classes")

        if not disciplina_id:
            messages.error(request, "Selecione uma disciplina.")
            return redirect("core:disciplinas")

        disciplina = get_object_or_404(Disciplina, id=disciplina_id)

        # 1. DESVINCULAR: Remove vínculos que existem no banco mas NÃO vieram no POST
        # Isso acontece quando o usuário desmarca um checkbox que estava marcado
        DisciplinasClasse.objects.filter(disciplina=disciplina).exclude(classe_id__in=classes_ids_recebidos).delete()

        # 2. VINCULAR/MANTER: Itera sobre os IDs recebidos
        vinculos_novos = 0
        for classe_id in classes_ids_recebidos:
            if classe_id: # Garante que o ID não está vazio
                classe = get_object_or_404(Classe, id=classe_id)
                
                # get_or_create garante que não criaremos duplicados
                obj, created = DisciplinasClasse.objects.get_or_create(
                    disciplina=disciplina, 
                    classe=classe
                )
                if created:
                    vinculos_novos += 1

        messages.success(request, f"Vínculos de '{disciplina.nome}' atualizados com sucesso.")
        return redirect("core:disciplinas")
    
@login_required
def editar_vinculo(request, pk):
    vinculo = get_object_or_404(DisciplinasClasse, pk=pk)
    if request.method == "POST":
        disciplina_id = request.POST.get("disciplina")
        classe_id = request.POST.get("classe")

        disciplina = get_object_or_404(Disciplina, id=disciplina_id)
        classe = get_object_or_404(Classe, id=classe_id)

        vinculo.disciplina = disciplina
        vinculo.classe = classe
        vinculo.save()

        messages.success(request, "Vínculo atualizado com sucesso.")
        return redirect("core:disciplinas")

@login_required
def excluir_vinculo(request, pk):
    vinculo = get_object_or_404(DisciplinasClasse, pk=pk)
    vinculo.delete()
    messages.success(request, "Vínculo excluído com sucesso.")
    return redirect("core:disciplinas")


def normalizar_nome(nome):
    # Remove acentos e converte para minúsculas
    nome_sem_acentos = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
    partes = nome_sem_acentos.lower().split()
    if len(partes) >= 2:
        return f"{partes[0]}{partes[-1]}"
    return nome_sem_acentos.replace(" ", ".")

@login_required
def matriculas_view(request):
    turmas = Turma.objects.select_related('classe', 'curso', 'sala').all()
    classes = Classe.objects.all()
    cursos = Curso.objects.all()
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto').last()
    
    # Gerar anos para o formulário (últimos 30 anos)
    ano_atual = datetime.now().year
    anos = list(range(ano_atual, ano_atual - 30, -1))

    turmas_json = json.dumps([
    {
        'id': t.id,
        'nome': t.nome,
        'classe': t.classe.id,
        'curso_id': t.curso.id,
        'curso_nome': t.curso.nome,
        'sala_id': t.sala.id if t.sala else None,
        'sala_nome': t.sala.nome if t.sala else 'Sem Sala',
        'turno': t.turno,
    } for t in turmas
    ], cls=DjangoJSONEncoder)

    if request.method == 'POST':
        # Coletar dados do formulário
        nome_completo = request.POST.get('nome_completo')
        bi = request.POST.get('bi')
        genero = request.POST.get('genero')
        turma_id = request.POST.get('turma')
        classe_id = request.POST.get('classe')
        curso_id = request.POST.get('curso')
        
        # Campos pessoais adicionais
        nome_pai = request.POST.get('nome_pai')
        nome_mae = request.POST.get('nome_mae')
        dia_nasc = request.POST.get('dia_nasc')
        mes_nasc = request.POST.get('mes_nasc')
        ano_nasc = request.POST.get('ano_nasc')
        naturalidade = request.POST.get('naturalidade')  # NOVO CAMPO

        # Gerar BI se não fornecido
        if not bi:
            caracteres = string.ascii_letters + string.digits
            bi = ''.join(random.choice(caracteres) for _ in range(14))

        # Validação
        if not (nome_completo and genero and turma_id and classe_id and curso_id):
            messages.error(request, "Preencha todos os campos obrigatórios.")
            return redirect(request.META.get('HTTP_REFERER'))

        try:
            turma = Turma.objects.select_related('sala', 'classe', 'curso').get(id=turma_id)
            classe = Classe.objects.get(id=classe_id)
            curso = Curso.objects.get(id=curso_id)
        except (Turma.DoesNotExist, Classe.DoesNotExist, Curso.DoesNotExist):
            messages.error(request, "Dados inválidos.")
            return redirect(request.META.get('HTTP_REFERER'))

        # Gerar número mecanográfico: ano + 4 dígitos aleatórios
        ano_atual = datetime.now().year
        numero_mecanografico = f"{ano_atual}{random.randint(1000, 9999)}"
        codigo_unico = str(uuid.uuid4())[:5]
        
        # Criar usuário
        username_base = normalizar_nome(nome_completo)
        username = f"{username_base}{codigo_unico}@sigesc.co.ao"
        senha = bi

        try:
            with transaction.atomic():
                user = Usuario.objects.create_user(
                    username=username,
                    password=senha,
                    first_name=nome_completo.split()[0],
                    last_name=" ".join(nome_completo.split()[1:]),
                    perfil='aluno'
                )

                # Criar aluno com todos os campos
                aluno = Aluno.objects.create(
                    usuario=user,
                    nome_completo=nome_completo,
                    numero_mecanografico=numero_mecanografico,
                    bi=bi,
                    genero=genero,
                    nome_pai=nome_pai if nome_pai else None,
                    nome_mae=nome_mae if nome_mae else None,
                    dia_nasc=dia_nasc if dia_nasc else None,
                    mes_nasc=mes_nasc if mes_nasc else None,
                    ano_nasc=ano_nasc if ano_nasc else None,
                    naturalidade=naturalidade if naturalidade else None,  # NOVO CAMPO
                    turma=turma,
                    sala=turma.sala,
                    classe=classe,
                    curso=curso,
                    turno=turma.turno
                )

                # Criar reconfirmação
                Reconfirmacao.objects.create(
                    aluno=aluno,
                    ano_letivo=ano_letivo,
                    turma=turma,
                    sala=turma.sala,
                    classe=classe,
                    curso=curso,
                    turno=turma.turno
                )

                messages.success(request, f"Aluno {aluno.nome_completo} matriculado com sucesso.")
        except Exception as e:
            messages.error(request, f"Erro ao matricular aluno: {str(e)}")

        return redirect('core:comprovativo_matricula', aluno.id)
    
    # Renderizar template com contexto
    perfil = request.user.perfil
    usuario = request.user
    
    if perfil == 'diretor_geral':
        return render(request, 'core/matriculas.html', {
            'turmas': turmas,
            'classes': classes,
            'cursos': cursos,
            'turmas_json': turmas_json,
            'usuario':usuario
        })
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/matriculas.html', {
            'turmas': turmas,
            'classes': classes,
            'cursos': cursos,
            'turmas_json': turmas_json,
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

@login_required
def comprovativo_matricula(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    data_hoje = datetime.now()
    # Número do recibo (sequência de pagamentos)
    recibo_numero = 0

    # Gerar código de barras
    barcode_value = str(aluno.numero_mecanografico)
    drawing = createBarcodeDrawing(
        'Code128',
        value=barcode_value,
        barHeight=40,
        barWidth=2.5,
        humanReadable=True
    )

    # Exportar para formato SVG em memória
    barcode_svg = drawing.asString('svg')

    # transformar em Base64 para embutir no HTML
    barcode_base64 = base64.b64encode(barcode_svg.encode("utf-8")).decode("utf-8")
    perfil = request.user.perfil
    usuario = request.user

    if perfil == 'diretor_geral':
        return render(request, 'core/comprovativo_matricula.html', {
            'aluno': aluno,
            'data': data_hoje,
            'atendido_por': request.user,
            'usuario':usuario,
            "barcode": barcode_base64,
        })
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/comprovativo_matricula.html', {
            'aluno': aluno,
            'data': data_hoje,
            'atendido_por': request.user,
            'usuario':usuario,
            "barcode": barcode_base64,
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
def reconfirmacao(request):
    ano_letivo = AnoLectivo.objects.filter(estado='Fechado').last()
    ano_aberto = AnoLectivo.objects.filter(estado='Aberto').last()

    if request.method == 'GET':
        query = request.GET.get('q', '')

        # Base query
        reconfirmacoes = Reconfirmacao.objects.select_related(
            'aluno', 'turma', 'sala', 'classe', 'curso' 
        ).filter(ano_letivo=ano_letivo)

        turmas = Turma.objects.select_related('classe', 'curso', 'sala').filter(ano_letivo=ano_aberto)
        turmas_json = json.dumps([
            {
                'id': turma.id,
                'nome': turma.nome,
                'classe': turma.classe.id if turma.classe else None,
                'curso_id': turma.curso.id if turma.curso else None,
                'curso_nome': turma.curso.nome if turma.curso else '',
                'sala_id': turma.sala.id if turma.sala else None,
                'sala_nome': turma.sala.nome if turma.sala else '',
                'turno': turma.turno
            }
            for turma in turmas
        ])
        
        # Filtro de pesquisa
        if query:
            reconfirmacoes = reconfirmacoes.filter(
                Q(aluno__nome_completo__icontains=query) |
                Q(aluno__numero_mecanografico__icontains=query) |
                Q(turma__nome__icontains=query)
            )

        # Agrupar já filtrado
        turmas_agrupadas = {}
        for r in reconfirmacoes.order_by('classe__numero', 'turma__nome'):
            key = (
                f"{r.classe.numero}ª Classe - Turma: {r.turma.nome} "
                f"- Sala: {r.sala.nome if r.sala else '---'} "
                f"- Curso: {r.curso.nome if r.curso else '---'} "
                f"- Turno: {getattr(r.turma, 'turno', '---')}"
            )
            turmas_agrupadas.setdefault(key, []).append(r.aluno)

        context = {
            'turmas_agrupadas': turmas_agrupadas,
            'search_query': query,
            'ano_letivo': ano_letivo,
            'usuario': request.user,
            'turmas': turmas,
            'classes': Classe.objects.all(),
            'turmas_json': turmas_json,
        }
        
        perfil = request.user.perfil
        if perfil == 'diretor_geral':
            return render(request, 'core/reconfirmacao.html', context)
        elif perfil == 'secretario_geral':
            return render(request, 'core/secretario_geral/reconfirmacao.html', context)
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
    
    # Se for uma requisição POST (processar reconfirmação)
    elif request.method == 'POST':
        # Obter o aluno
        aluno_id = request.POST.get('aluno_id')
        aluno = get_object_or_404(Aluno, id=aluno_id)
        
        # Obter dados do formulário
        nome_completo = request.POST.get('nome_completo')
        bi = request.POST.get('bi')
        genero = request.POST.get('genero')
        classe_id = request.POST.get('classe')
        turma_id = request.POST.get('turma')
        curso_id = request.POST.get('curso')
        sala_id = request.POST.get('sala')
        turno = request.POST.get('turno')
        
        # Obter ano letivo atual
        ano_aberto = AnoLectivo.objects.filter(estado='Aberto').first()
        if not ano_aberto:
            messages.error(request, 'Não há ano letivo aberto para realizar a reconfirmação.')
            return redirect('core:reconfirmacao')
        
        # Verificar se já existe reconfirmação ativa para este aluno no ano letivo
        reconfirmacao_existente = Reconfirmacao.objects.filter(
            aluno=aluno,
            ano_letivo=ano_letivo,
            estado='Adimplente'
        ).first()
        
        if reconfirmacao_existente:
            messages.warning(request, f'Este aluno já foi reconfirmado para o ano letivo {ano_letivo}.')
            return redirect('core:reconfirmacao')
        
        # Atualizar dados do aluno
        aluno.nome_completo = nome_completo
        aluno.bi = bi
        aluno.genero = genero
        aluno.save()
        
        # Obter objetos relacionados
        turma = get_object_or_404(Turma, id=turma_id)
        classe = get_object_or_404(Classe, id=classe_id) if classe_id else None
        curso = get_object_or_404(Curso, id=curso_id) if curso_id else None
        sala = get_object_or_404(Sala, id=sala_id) if sala_id else None
        
        # Criar nova reconfirmação
        nova_reconfirmacao = Reconfirmacao.objects.create(
            aluno=aluno,
            ano_letivo=ano_aberto,
            estado='Adimplente',
            estadoClasse='Pendente',
            turma=turma,
            sala=sala,
            classe=classe,
            curso=curso,
            turno=turno
        )
        
        messages.success(request, 'Reconfirmação realizada com sucesso!')
        
        # Redirecionar para o comprovativo
        return redirect('core:comprovativo_matricula', aluno_id=aluno.id)


@login_required
def pautas(request):
    perfil = request.user.perfil
    usuario = request.user

    if perfil == 'diretor_geral':
        return render(request, 'core/pautas.html', {'usuario':usuario})
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/pautas.html', {'usuario':usuario})
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
def pautas_trimestre(request, trimestre):
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
    
    for r in reconfirmacoes.order_by('classe__numero', 'turma__nome', 'aluno__nome_completo'):
        key = f"{r.classe.numero}ª Classe - Turma: {r.turma.nome} - Sala: {r.sala.nome if r.sala else '---'} - Curso: {r.curso.nome if r.curso else '---'} - Turno: {r.turno}"
        
        if key not in turmas_agrupadas:
            turmas_agrupadas[key] = {
                'alunos': [],
                'disciplinas_turma': set()  # Usaremos set para evitar duplicatas
            }

        aluno = r.aluno
        classe_numero = r.classe.numero
        
        # Buscar todas as notas do aluno no trimestre
        notas_aluno = Nota.objects.filter(
            aluno=aluno,
            trimestre=trimestre
        ).select_related('disciplina')
        
        linha = {
            'aluno': aluno.nome_completo,
            'disciplinas': {},
            'estado': 'Aprovado'
        }
        
        tem_todas_notas = True
        disciplinas_com_notas = set()
        
        for nota in notas_aluno:
            disciplina = nota.disciplina
            valor_nota = nota.valor
            
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
        
        # Verificar se aluno tem todas as disciplinas da turma
        if tem_todas_notas:
            # Verificar se existem disciplinas na turma que o aluno não tem nota
            for disciplina in turmas_agrupadas[key]['disciplinas_turma']:
                if disciplina.id not in linha['disciplinas']:
                    linha['disciplinas'][disciplina.id] = {
                        'nome': disciplina.nome,
                        'valor': None
                    }
                    tem_todas_notas = False
        
        if not tem_todas_notas:
            linha['estado'] = 'Pendente'
        
        turmas_agrupadas[key]['alunos'].append(linha)
    
    # Converter sets para listas ordenadas para cada turma
    for key, dados_turma in turmas_agrupadas.items():
        # Ordenar disciplinas pelo nome
        disciplinas_ordenadas = sorted(
            list(dados_turma['disciplinas_turma']),
            key=lambda x: x.nome
        )
        turmas_agrupadas[key]['disciplinas_ordenadas'] = disciplinas_ordenadas
        
        # Preparar lista final de alunos com dados organizados
        alunos_final = []
        for aluno_data in dados_turma['alunos']:
            aluno_final = {
                'aluno': aluno_data['aluno'],
                'estado': aluno_data['estado'],
                'notas_por_disciplina': {}
            }
            
            # Para cada disciplina da turma, buscar a nota do aluno
            for disciplina in disciplinas_ordenadas:
                nota_disciplina = aluno_data['disciplinas'].get(disciplina.id, {'valor': None})
                aluno_final['notas_por_disciplina'][disciplina.id] = nota_disciplina['valor']
            
            alunos_final.append(aluno_final)
        
        turmas_agrupadas[key]['alunos_final'] = alunos_final
    
    texto = ''
    if trimestre == 4:
        texto = 'Exame'

    perfil = request.user.perfil
    usuario = request.user

    if perfil == 'diretor_geral':
        return render(request, 'core/pautas_trimestre.html', {
            'turmas_agrupadas': turmas_agrupadas,
            'search_query': query,
            'trimestre': trimestre,
            'texto': texto,
            'usuario': usuario
        })
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/pautas_trimestre.html', {
            'turmas_agrupadas': turmas_agrupadas,
            'search_query': query,
            'trimestre': trimestre,
            'texto': texto,
            'usuario': usuario
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
def pautas_final(request):
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

    for r in reconfirmacoes.order_by('classe__numero', 'turma__nome', 'aluno__nome_completo'):
        key = f"{r.classe.numero}ª Classe - Turma: {r.turma.nome} - Sala: {r.sala.nome if r.sala else '---'} - Curso: {r.curso.nome if r.curso else '---'} - Turno: {r.turno}"
        
        if key not in turmas_agrupadas:
            turmas_agrupadas[key] = {
                'alunos': [],
                'disciplinas_turma': set()
            }

        aluno = r.aluno
        classe_numero = r.classe.numero
        
        # Buscar todas as notas do aluno para calcular média final
        notas_aluno = Nota.objects.filter(aluno=aluno).select_related('disciplina')
        
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
            if notas[1] is not None and notas[2] is not None and notas[3] is not None:
                if notas[4] is not None:  # Tem exame
                    media_trimestral = (notas[1] + notas[2] + notas[3]) / Decimal('3.0')
                    nota_final = (media_trimestral * Decimal('0.4')) + (notas[4] * Decimal('0.6'))
                    nota_final = round(nota_final, 1)
                    
                    # Verificar aprovação
                    if classe_numero < 7 and nota_final < 5:
                        linha['estado'] = 'Reprovado'
                    elif classe_numero >= 7 and nota_final < 10:
                        linha['estado'] = 'Reprovado'
                else:
                    # Sem exame, calcular média simples
                    nota_final = (notas[1] + notas[2] + notas[3]) / Decimal('3.0')
                    nota_final = round(nota_final, 1)
                    
                    # Verificar aprovação
                    if classe_numero < 7 and nota_final < 5:
                        linha['estado'] = 'Reprovado'
                    elif classe_numero >= 7 and nota_final < 10:
                        linha['estado'] = 'Reprovado'
            else:
                nota_final = None
                tem_todas_notas = False
            
            # Armazenar nota final
            linha['disciplinas'][disciplina_id] = {
                'nome': disciplina.nome,
                'valor': nota_final,
                't1': notas[1],
                't2': notas[2],
                't3': notas[3],
                't4': notas[4]
            }
        
        # Verificar se aluno tem todas as disciplinas da turma
        if tem_todas_notas:
            for disciplina in turmas_agrupadas[key]['disciplinas_turma']:
                if disciplina.id not in linha['disciplinas']:
                    linha['disciplinas'][disciplina.id] = {
                        'nome': disciplina.nome,
                        'valor': None,
                        't1': None,
                        't2': None,
                        't3': None,
                        't4': None
                    }
                    tem_todas_notas = False
        
        if not tem_todas_notas:
            linha['estado'] = 'Pendente'
        
        # Atualizar estado na reconfirmação
        reconfirmacao = Reconfirmacao.objects.filter(id=r.id).first()
        if reconfirmacao:
            if linha['estado'] == 'Reprovado':
                reconfirmacao.estadoClasse = 'Reprovado'
                reconfirmacao.save()
                print(f"Estado da classe atualizado para: {reconfirmacao.estadoClasse}")
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
            # Criar lista ordenada de notas
            notas_ordenadas = []
            for disciplina in disciplinas_ordenadas:
                if disciplina.id in aluno_data['disciplinas']:
                    notas_ordenadas.append(aluno_data['disciplinas'][disciplina.id]['valor'])
                else:
                    notas_ordenadas.append(None)
            
            alunos_final.append({
                'aluno': aluno_data['aluno'],
                'estado': aluno_data['estado'],
                'notas': notas_ordenadas,
                'detalhes': aluno_data['disciplinas']  # Manter detalhes se precisar
            })
        
        turmas_final[key] = {
            'disciplinas': disciplinas_ordenadas,
            'alunos': alunos_final
        }

    perfil = request.user.perfil
    usuario = request.user

    if perfil == 'diretor_geral':
        return render(request, 'core/pautas_finais.html', {
            'turmas_agrupadas': turmas_final,
            'usuario': usuario
        })
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/pautas_finais.html', {
            'turmas_agrupadas': turmas_final,
            'usuario': usuario
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
def coordenacoes(request):
    perfil = request.user.perfil
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto').last()
    if not ano_letivo:
        return HttpResponse(
            """
            <html>
                <head>
                    <title>Erro 500 - Ano Lectivo não definido</title>
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
                        <h1>500</h1>
                        <p><strong>Ano Lectivo não definido</strong></p>
                        <p>Necessita Cadastrar o Ano lectivo</p>
                    </div>
                </body>
            </html>
            """,
            status=500
        )

    try:
        trimestre = int(request.GET.get('trimestre', 1))  # padrão 1º trimestre
        if trimestre not in [1, 2, 3, 4]:
            trimestre = 1
    except ValueError:
        trimestre = 1

    contexto = {}

    def montar_pauta_por_turma(turma):
        alunos = Aluno.objects.filter(turma=turma)
        pauta_alunos = []
        for aluno in alunos:
            linha = {
                'aluno': aluno.nome_completo,
                'disciplinas': [],
                'estado': 'Aprovado'
            }
            tem_todas_notas = True

            disciplinas_classe = DisciplinasClasse.objects.filter(classe=turma.classe).select_related('disciplina')
            for disc_classe in disciplinas_classe:
                nota = Nota.objects.filter(
                    aluno=aluno,
                    disciplina=disc_classe.disciplina,
                    trimestre=trimestre,
                    ano_lectivo=ano_letivo,
                    classe=turma.classe
                ).first()
                valor = nota.valor if nota else None
                if valor is None:
                    tem_todas_notas = False
                else:
                    if turma.classe.numero < 7 and valor < 5:
                        linha['estado'] = 'Reprovado'
                    elif turma.classe.numero >= 7 and valor < 10:
                        linha['estado'] = 'Reprovado'

                linha['disciplinas'].append({'nome': disc_classe.disciplina.nome, 'valor': valor})

            if not tem_todas_notas:
                linha['estado'] = 'Pendente'

            pauta_alunos.append(linha)
        return pauta_alunos

    def montar_pauta_por_disciplina(disciplina, turmas):
        pauta_alunos = []
        for turma in turmas:
            alunos = Aluno.objects.filter(turma=turma)
            for aluno in alunos:
                nota = Nota.objects.filter(
                    aluno=aluno,
                    disciplina=disciplina,
                    trimestre=trimestre,
                    ano_lectivo=ano_letivo,
                    classe=turma.classe
                ).first()
                valor = nota.valor if nota else None
                estado = 'Aprovado'
                if valor is None:
                    estado = 'Pendente'
                else:
                    if turma.classe.numero < 7 and valor < 5:
                        estado = 'Reprovado'
                    elif turma.classe.numero >= 7 and valor < 10:
                        estado = 'Reprovado'

                pauta_alunos.append({
                    'aluno': aluno.nome_completo,
                    'disciplina': disciplina.nome,
                    'valor': valor,
                    'estado': estado,
                    'turma': turma.nome
                })
        return pauta_alunos

    # Para outros perfis, retorna tudo
    professores = Funcionario.objects.filter(funcao__icontains='professor')
    turmas = Turma.objects.all()
    disciplinas = Disciplina.objects.all()
    usuario = request.user

    contexto.update({
        'coordenacoes': Coordenacao.objects.select_related('funcionario', 'turma', 'disciplina'),
        'professores': professores,
        'turmas': turmas,
        'disciplinas': disciplinas,
        'trimestre': trimestre,
        'usuario':usuario,
    })

    if perfil == 'diretor_geral':
        return render(request, 'core/coordenacoes.html', contexto)
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/coordenacoes.html', contexto)
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

    return HttpResponse("Perfil não autorizado", status=403)
     
@login_required
def criar_coordenacao(request):
    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario_id')
        tipo = request.POST.get('tipo')
        turma_id = request.POST.get('turma_id') or None
        disciplina_id = request.POST.get('disciplina_id') or None

        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        turma = Turma.objects.filter(id=turma_id).first() if turma_id else None
        disciplina = Disciplina.objects.filter(id=disciplina_id).first() if disciplina_id else None

        Coordenacao.objects.create(
            funcionario=funcionario,
            tipo=tipo,
            turma=turma,
            disciplina=disciplina
        )

        messages.success(request, "Coordenação criada com sucesso.")
    return redirect('core:coordenacoes')

@login_required
def editar_coordenacao(request, pk):
    coord = get_object_or_404(Coordenacao, pk=pk)

    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario_id')
        tipo = request.POST.get('tipo')

        turma_id = request.POST.get('turma_id') or None
        disciplina_id = request.POST.get('disciplina_id') or None
        turno = request.POST.get('turno') or None

        coord.funcionario = get_object_or_404(Funcionario, id=funcionario_id) 
        coord.tipo = tipo

        # Zera os campos que não fazem sentido para o tipo escolhido 
        if tipo == "turno":
            coord.turno = turno
            coord.turma = None 
            coord.disciplina = None
        elif tipo == "turma":
            coord.turma = Turma.objects.filter(id=turma_id).first() if turma_id else None
            coord.disciplina = None
            coord.turno = None
        elif tipo == "disciplina":
            coord.disciplina = Disciplina.objects.filter(id=disciplina_id).first() if disciplina_id else None
            coord.turma = None
            coord.turno = None

        coord.save() 
        messages.success(request, "Coordenação atualizada com sucesso.")
        return redirect('core:coordenacoes')

    return redirect('core:coordenacoes')

@login_required
def eliminar_coordenacao(request, pk):
    coord = get_object_or_404(Coordenacao, pk=pk)
    if request.method == 'POST':
        coord.delete()
        messages.success(request, "Coordenação eliminada com sucesso.")
    return redirect('core:coordenacoes')

@login_required
def gerar_ata_prova(request):
    turmas = Turma.objects.all()
    professores = Professor.objects.all()

    return render(request, "core/alunos.html", {'turmas':turmas, 'professores':professores})

@login_required
def ano_lectivo(request):
    anos = AnoLectivo.objects.all().order_by("-id")

    if request.method == "POST":
        ano_id = request.POST.get("id")
        ano_valor = request.POST.get("ano")
        estado_valor = request.POST.get("estado")

        if ano_id:  # atualização
            ano_obj = get_object_or_404(AnoLectivo, id=ano_id)
            ano_obj.ano = ano_valor
            if estado_valor:
                ano_obj.estado = estado_valor
            ano_obj.save()
            messages.success(request, "Ano lectivo atualizado com sucesso.")
        else:  # criação
            # Fecha o último ano aberto
            ultimo_ano = AnoLectivo.objects.filter(estado="Aberto").last()
            if ultimo_ano:
                ultimo_ano.estado = "Fechado"
                ultimo_ano.save()
            AnoLectivo.objects.create(ano=ano_valor, estado="Aberto")
            messages.success(request, "Ano lectivo cadastrado com sucesso.")

        return redirect("core:ano_lectivo")

    perfil = request.user.perfil
    usuario = request.user
    if perfil == 'diretor_geral':
        return render(request, "core/ano-lectivo.html", {"anos": anos, "usuario":usuario})
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
def alterar_senha(request):
    if request.method == "POST":
        senha_atual = request.POST.get("senha_atual")
        nova_senha = request.POST.get("nova_senha")
        confirmar_senha = request.POST.get("confirmar_senha")

        user = request.user

        # Verifica se a senha atual está correta
        if not user.check_password(senha_atual):
            messages.error(request, "Senha atual incorreta.")
            return redirect(request.META.get("HTTP_REFERER"))

        # Verifica se nova senha e confirmação coincidem
        if nova_senha != confirmar_senha:
            messages.error(request, "A nova senha e a confirmação não coincidem.")
            return redirect(request.META.get("HTTP_REFERER"))

        # Altera a senha
        user.set_password(nova_senha)
        user.save()

        # Mantém o usuário logado após mudar a senha
        update_session_auth_hash(request, user)

        messages.success(request, "Senha alterada com sucesso. Termine secção para testar a nova senha")
        return redirect(request.META.get("HTTP_REFERER"))

    return redirect("core:logout")

def logout_view(request): 
    logout(request)  
    return redirect('core:login')     