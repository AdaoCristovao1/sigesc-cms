from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Usuario
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from administracao.models import Funcionario
from django.contrib.auth.hashers import make_password
import unicodedata
from .models import *
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
import json
from django.utils.timezone import now
import random
import string
import unicodedata
from datetime import datetime
from datetime import date
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from pedagogico.models import Nota
from django.contrib.auth import get_user_model
from financeiro.views import atualizar_estado_aluno
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPM
from reportlab.graphics.barcode import createBarcodeDrawing
import io
import base64
from django.http import HttpResponse
import uuid

@login_required
def dashboard(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola inválida.')
        return redirect('financa:despesas')

    alunos = (
        Aluno.objects
        .filter(escola=escola_usuario)
        .select_related(
            'turma',
            'sala',
            'classe',
            'curso',
            'usuario',
            'escola'
        )
    )
    for aluno in alunos:
        atualizar_estado_aluno(aluno, escola_usuario) 

    perfil = request.user.perfil
    usuario = request.user

    ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
    professores_total = Funcionario.objects.filter(funcao__icontains='professor', escolas=escola_usuario).count()
    funcionarios_total = Funcionario.objects.exclude(funcao__icontains='professor').filter(escolas=escola_usuario).count()
    aluno_total = Reconfirmacao.objects.filter(ano_letivo=ano_letivo, escola=escola_usuario).count()
    aluno_inadimplentes_total = Reconfirmacao.objects.filter(ano_letivo=ano_letivo, estado='Inadimplente', escola=escola_usuario).count()
    context ={
        'usuario':usuario,
        'professores_total': professores_total,
        'funcionarios_total':funcionarios_total,
        'aluno_total':aluno_total,
        'aluno_inadimplentes_total':aluno_inadimplentes_total,
        'escola': escola_usuario
    }

    if perfil == 'diretor_admin':
        return render(request, 'administracao/diretor_admin/dashboard.html', context)

    elif perfil == 'secretario_admin':
        return render(request, 'administracao/secretario_admin/dashboard-secretario.html', context)

    elif perfil == 'coordenador_turno':
        return render(request, 'administracao/coordenador_turno/dashboard-coordenador.html', context)
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    q = request.GET.get('q')
    if q:
        filtro = Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        alunos = Usuario.objects.filter(filtro, escola=escola_usuario, perfil='aluno')
        outros = Usuario.objects.filter(filtro, escola=escola_usuario).exclude(perfil='aluno')
    else:
        alunos = Usuario.objects.filter(escola=escola_usuario, perfil='aluno')
        outros = Usuario.objects.exclude(escola=escola_usuario, perfil='aluno')

    perfil = request.user.perfil  
    usuario = request.user  
    if perfil == 'diretor_admin':
        return render(request, 'administracao/diretor_admin/usuarios-list.html', {
            'alunos': alunos,
            'outros': outros,
            'usuario':usuario,
            'escola':escola_usuario
        })
    elif perfil == 'secretario_admin':
        return render(request, 'administracao/secretario_admin/usuarios-list.html', {
                'alunos': alunos,
                'outros': outros,
                'usuario':usuario,
                'escola':escola_usuario
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
                return redirect('administracao:usuarios')
        else:
            messages.error(request, 'Senha incorreta.')
            return redirect('administracao:usuarios')
        
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
            return redirect('administracao:cadastrar_funcionario')

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
            codigo_unico = str(uuid.uuid4())[:4]
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
            return redirect('administracao:cadastrar_funcionario')

        return redirect('administracao:cadastrar_funcionario')

def remover_acentos(texto):
    # Remove acentos e caracteres especiais
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).replace('ç', 'c').replace('Ç', 'C')

User = get_user_model()
@login_required
def cadastrar_funcionario(request):

    # Obtém a escola da sessão
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        bilhete = request.POST.get('bi') 
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
        # Adiciona a escola da sessão (single)
        funcionario.escolas.add(escola_usuario)

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
            perfil=mapear_perfil_para_funcao(funcao),
            escola=escola_usuario
        )

        funcionario.usuario = usuario
        funcionario.save()

        messages.success(request, f"Funcionário {nome} cadastrado com sucesso!")
        return redirect('administracao:cadastrar_funcionario')

    # Busca
    q = request.GET.get('q')
    if q:
        filtro = (
            Q(nome__icontains=q) |
            Q(bi__icontains=q) |
            Q(funcao__icontains=q) |
            Q(telefone__icontains=q)
        )
        funcionarios = Funcionario.objects.filter(filtro, escolas=escola_usuario)
    else:
        funcionarios = Funcionario.objects.filter(escolas=escola_usuario)

    perfil = request.user.perfil   
    usuario = request.user 

    if perfil == 'diretor_admin':
        return render(request, 'administracao/diretor_admin/form-func.html', {
        'funcionarios': funcionarios,
        'usuario':usuario,
        'escola': escola_usuario
        })
    
    elif perfil == 'secretario_admin':
        return render(request, 'administracao/secretario_admin/form-func.html', {
        'funcionarios': funcionarios,
        'usuario':usuario,
         'escola': escola_usuario
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

def mapear_perfil_para_funcao(funcao):
    """Mapeia a função do funcionário para o perfil no sistema"""
    mapa = {
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
    }
    return mapa.get(funcao, 'funcionario')

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
            return redirect('administracao:cadastrar_funcionario')

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
            return redirect('administracao:cadastrar_funcionario')

        return redirect('administracao:cadastrar_funcionario')


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
        return redirect('administracao:cadastrar_funcionario')
    
@login_required
def classes(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')

    classes = Classe.objects.filter(escola=escola_usuario).order_by('numero')

    perfil = request.user.perfil 
    usuario = request.user   
     
    if perfil == 'diretor_admin':
        return render(request, 'administracao/diretor_admin/classes.html', {'classes': classes, 'usuario':usuario, 'escola': escola_usuario})
    elif perfil == 'secretario_admin':
        return render(request, 'administracao/secretario_admin/classes.html', {'classes': classes, 'usuario':usuario, 'escola': escola_usuario})
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
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')
    
    if request.method == 'POST':
        Classe.objects.create(
            escola=escola_usuario,
            designacao=request.POST['designacao'],
            numero=request.POST['numero']
        )
    return redirect('administracao:classes')

@login_required
def atualizar_classe(request):
    if request.method == 'POST':
        classe = get_object_or_404(Classe, pk=request.POST['id'])
        classe.designacao = request.POST['designacao']
        classe.numero = request.POST['numero']
        classe.save()
    return redirect('administracao:classes')

@login_required
def eliminar_classe(request, id):
    classe = get_object_or_404(Classe, pk=id)
    classe.delete()
    return redirect('administracao:classes')

@login_required
def cursos(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')
    
    cursos = Curso.objects.filter(escola=escola_usuario).order_by('nome')
    perfil = request.user.perfil   
    usuario = request.user
     
    if perfil == 'diretor_admin':
        return render(request, 'administracao/diretor_admin/cursos.html', {'cursos': cursos, 'usuario':usuario, 'escola': escola_usuario})
    elif perfil == 'secretario_admin':
        return render(request, 'administracao/secretario_admin/cursos.html', {'cursos': cursos, 'usuario':usuario, 'escola': escola_usuario})
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
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')
    
    if request.method == 'POST':
        Curso.objects.create(
            escola=escola_usuario,
            nome=request.POST['nome'],
        )
    return redirect('administracao:cursos')

@login_required
def atualizar_curso(request):
    if request.method == 'POST':
        curso = get_object_or_404(Curso, pk=request.POST['id'])
        curso.nome = request.POST['nome']
        curso.save()
    return redirect('administracao:cursos')

@login_required
def eliminar_curso(request, id):
    curso = get_object_or_404(Curso, pk=id)
    curso.delete()
    return redirect('administracao:cursos')

@login_required
def turmas_e_salas(request):
    # Obtém a escola da sessão
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')

    if request.method == 'POST':
        qtd_salas = int(request.POST.get('quantidade', 0))
        total_existentes = Sala.objects.filter(escola=escola_usuario).count() 

        if qtd_salas > total_existentes:
            for i in range(total_existentes + 1, qtd_salas + 1):
                Sala.objects.create(escola=escola_usuario, nome=str(i))
        elif qtd_salas < total_existentes:
            salas_para_excluir = Sala.objects.filter(escola=escola_usuario).order_by('-id')[:total_existentes - qtd_salas]
            for sala in salas_para_excluir:
               sala.delete()

        return redirect('administracao:turmas_e_salas')
    
    ano_letivo = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()

    salas = Sala.objects.filter(escola=escola_usuario).order_by('id')
    turmas = Turma.objects.filter(escola=escola_usuario, ano_letivo=ano_letivo).order_by('id')
    classes = Classe.objects.filter(escola=escola_usuario).order_by('id')
    cursos = Curso.objects.filter(escola=escola_usuario).order_by('id')
    salas = Sala.objects.filter(escola=escola_usuario).order_by('id')

    perfil = request.user.perfil 
    usuario = request.user   
     
    if perfil == 'diretor_admin':
        return render(request, 'administracao/diretor_admin/turmas-salas.html', {'turmas': turmas, 'classes': classes, 'cursos': cursos, 'salas': salas,'total': salas.count(), 'usuario':usuario, 'ano_letivo':ano_letivo, 'escola': escola_usuario})
    elif perfil == 'secretario_admin':
        return render(request, 'administracao/secretario_admin/turmas-salas.html', {'turmas': turmas, 'classes': classes, 'cursos': cursos, 'salas': salas,'total': salas.count(), 'usuario':usuario, 'ano_letivo':ano_letivo, 'escola': escola_usuario})
    elif perfil == 'coordenador_turno':
        return render(request, 'administracao/coordenador_turno/turmas-salas.html', {'turmas': turmas, 'classes': classes, 'cursos': cursos, 'salas': salas,'total': salas.count(), 'usuario':usuario, 'ano_letivo':ano_letivo, 'escola': escola_usuario})
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
    # Obtém a escola da sessão
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        turno = request.POST.get('turno')
        classe_id = request.POST.get('classe')
        curso_id = request.POST.get('curso')
        sala_id = request.POST.get('sala')
        ano_letivo = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()

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
            quantidade_turmas = Turma.objects.filter(escola=escola_usuario, sala_id=sala_id, ano_letivo=ano_letivo).count()
            if quantidade_turmas >= 3:
                messages.error(request, "Essa sala já está associada ao número máximo de 3 turmas.")
                return redirect(request.META.get('HTTP_REFERER'))

        # Verifica se já existe uma turma igual
        turma_existente = Turma.objects.filter(
            escola=escola_usuario,
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
            escola=escola_usuario,
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

def normalizar_nome(nome):
    # Remove acentos e converte para minúsculas
    nome_sem_acentos = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')
    partes = nome_sem_acentos.lower().split()
    if len(partes) >= 2:
        return f"{partes[0]}{partes[-1]}"
    return nome_sem_acentos.replace(" ", ".")

@login_required
def matriculas_view(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')
    
    turmas = Turma.objects.select_related('classe', 'curso', 'sala').filter(escola=escola_usuario)
    classes = Classe.objects.filter(escola=escola_usuario)
    cursos = Curso.objects.filter(escola=escola_usuario)
    ano_letivo = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()
    
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
            turma = Turma.objects.filter(escola=escola_usuario).select_related('sala', 'classe', 'curso').get(id=turma_id)
            classe = Classe.objects.filter(escola=escola_usuario).get(id=classe_id)
            curso = Curso.objects.filter(escola=escola_usuario).get(id=curso_id)
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
                    perfil='aluno',
                    escola=escola_usuario
                )

                # Criar aluno com todos os campos
                aluno = Aluno.objects.create(
                    escola=escola_usuario,
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
                    escola=escola_usuario,
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

        return redirect('administracao:comprovativo_matricula', aluno.id)
    
    perfil = request.user.perfil  
    usuario = request.user  
     
    if perfil == 'diretor_admin':

        return render(request, 'administracao/diretor_admin/matriculas.html', {
            'turmas': turmas,
            'classes': classes,
            'cursos': cursos,
            'turmas_json': turmas_json,
            'usuario':usuario,
            'escola': escola_usuario
        })
    elif perfil == 'secretario_admin':
        return render(request, 'administracao/secretario_admin/matriculas.html', {
            'turmas': turmas,
            'classes': classes,
            'cursos': cursos,
            'turmas_json': turmas_json,
            'usuario':usuario,
            'escola': escola_usuario
        })
    elif perfil == 'coordenador_turno':
        return render(request, 'administracao/coordenador_turno/matriculas.html', {
            'turmas': turmas,
            'classes': classes,
            'cursos': cursos,
            'turmas_json': turmas_json,
            'usuario':usuario,
            'escola': escola_usuario
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
     
    if perfil == 'diretor_admin':
        return render(request, 'administracao/diretor_admin/comprovativo_matricula.html', {
            'aluno': aluno,
            'data': data_hoje,
            'atendido_por': request.user,
            'usuario':usuario,
            "barcode": barcode_base64,
        })
    elif perfil == 'secretario_admin':
        return render(request, 'administracao/secretario_admin/comprovativo_matricula.html', {
            'aluno': aluno,
            'data': data_hoje,
            'atendido_por': request.user,
            'usuario':usuario,
            "barcode": barcode_base64,
        })
    elif perfil == 'coordenador_turno':
        return render(request, 'administracao/coordenador_turno/comprovativo_matricula.html', {
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
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')
    
    ano_letivo = AnoLectivo.objects.filter(escola=escola_usuario, estado='Fechado').last()
    ano_aberto = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()

    if request.method == 'GET':
        query = request.GET.get('q', '')

        # Base query
        reconfirmacoes = Reconfirmacao.objects.select_related(
            'aluno', 'turma', 'sala', 'classe', 'curso' 
        ).filter(escola=escola_usuario, ano_letivo=ano_letivo)

        turmas = Turma.objects.select_related('classe', 'curso', 'sala').filter(escola=escola_usuario, ano_letivo=ano_aberto)
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
                Q(turma__nome__icontains=query, escola=escola_usuario)
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
            'classes': Classe.objects.filter(escola=escola_usuario),
            'turmas_json': turmas_json,
            'escola': escola_usuario,
        }
        
        perfil = request.user.perfil
        if perfil == 'diretor_admin':
            return render(request, 'administracao/diretor_admin/reconfirmacao.html', context)
        elif perfil == 'secretario_admin':
            return render(request, 'administracao/secretario_admin/reconfirmacao.html', context)
        elif perfil == 'coordenador_turno':
            return render(request, 'administracao/coordenador_turno/reconfirmacao.html', context)
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
        ano_aberto = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').first()
        if not ano_aberto:
            messages.error(request, 'Não há ano letivo aberto para realizar a reconfirmação.')
            return redirect('administracao:reconfirmacao')
        
        # Verificar se já existe reconfirmação ativa para este aluno no ano letivo
        reconfirmacao_existente = Reconfirmacao.objects.filter(
            escola=escola_usuario,
            aluno=aluno,
            ano_letivo=ano_letivo,
            estado='Adimplente'
        ).first()
        
        if reconfirmacao_existente:
            messages.warning(request, f'Este aluno já foi reconfirmado para o ano letivo {ano_letivo}.')
            return redirect('administracao:reconfirmacao')
        
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
            escola=escola_usuario,
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
        return redirect('administracao:comprovativo_matricula', aluno_id=aluno.id)

@login_required
def alunos_view(request):
    # Obtém a escola da sessão
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')
        
    anos_disponiveis = AnoLectivo.objects.filter(escola=escola_usuario).order_by('-ano')
     
    ano_letivo = request.GET.get("ano_lectivo")

    if not ano_letivo:
        ano_letivo = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()

    query = request.GET.get('q', '')
    turmas = Turma.objects.filter(escola=escola_usuario, ano_letivo=ano_letivo)
    # Base query
    reconfirmacoes = Reconfirmacao.objects.select_related(
        'aluno', 'turma', 'sala', 'classe', 'curso' 
    ).filter(escola=escola_usuario, ano_letivo=ano_letivo)

    turmas = Turma.objects.select_related('classe', 'curso', 'sala').filter(escola=escola_usuario, ano_letivo=ano_letivo)
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
            Q(turma__nome__icontains=query, escola=escola_usuario)
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
        'classes': Classe.objects.filter(escola=escola_usuario),
        'turmas_json':turmas_json,
        'anos_disponiveis':anos_disponiveis,
        'escola': escola_usuario
    }
     
    if perfil == 'diretor_admin':
        return render(request, 'administracao/diretor_admin/alunos.html', context)
    
    elif perfil == 'secretario_admin':
        return render(request, 'administracao/secretario_admin/alunos.html', context)
    elif perfil == 'coordenador_turno':
        return render(request, 'administracao/coordenador_turno/alunos.html', context)
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
        return redirect('administracao:alunos_lista')
    
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
    
    return redirect('administracao:alunos_lista')

@login_required
def deletar_aluno(request, aluno_id):
    if request.method == "POST":
        senha = request.POST.get('password')
        user = request.user

        # Verifica se a senha está correta
        if not user.check_password(senha):
            messages.error(request, "Senha incorreta! A exclusão não foi realizada.")
            return redirect('administracao:alunos_lista')

        aluno = get_object_or_404(Aluno, id=aluno_id)

        # Apaga o usuário vinculado ao aluno  
        if aluno.usuario:
            aluno.usuario.delete()

        # Apaga o próprio aluno
        aluno.delete()

        messages.success(request, "Aluno e usuário deletados com sucesso.")
        return redirect('administracao:alunos_lista')

    return redirect('administracao:alunos_lista')

@login_required
def aluno_detalhes(request, id):
    # Obtém a escola da sessão
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')
    
    aluno = get_object_or_404(Aluno, pk=id)
    atualizar_estado_aluno(aluno, escola_usuario)
    
    ultima_reconfirmacao = Reconfirmacao.objects.filter(escola=escola_usuario, aluno=aluno).order_by('-ano_letivo').last()
    
    notas = Nota.objects.filter(escola=escola_usuario, aluno=aluno).select_related('disciplina', 'classe')
    
    medias = {}

    for nota in notas.order_by('classe__numero', 'disciplina__nome', 'trimestre'):
        ano = nota.classe.numero
        nome_disciplina = nota.disciplina.nome
        trimestre = nota.trimestre
        valor = nota.valor

        # Inicialização da estrutura
        if ano not in medias:
            medias[ano] = {}
        if nome_disciplina not in medias[ano]:
            medias[ano][nome_disciplina] = {
                'notas': {},
                'media': '--'
            }

        # Guardar nota
        medias[ano][nome_disciplina]['notas'][trimestre] = valor

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
     
    if perfil == 'diretor_admin':
        return render(request, 'administracao/diretor_admin/aluno-detalhe.html', {
            'aluno': aluno,
            'ultima_reconfirmacao': ultima_reconfirmacao,
            'medias': medias,
            'usuario':usuario,
            'escola': escola_usuario,
        })
    elif perfil == 'secretario_admin':
        return render(request, 'administracao/secretario_admin/aluno-detalhe.html', {
            'aluno': aluno,
            'ultima_reconfirmacao': ultima_reconfirmacao,
            'medias': medias,
            'usuario':usuario,
            'escola': escola_usuario,
        })
    elif perfil == 'coordenador_turno':
        return render(request, 'administracao/coordenador_turno/aluno-detalhe.html', {
            'aluno': aluno,
            'ultima_reconfirmacao': ultima_reconfirmacao,
            'medias': medias,
            'usuario':usuario,
            'escola': escola_usuario,
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

    return redirect('administracao:aluno_detalhes', id=aluno.id)

@login_required
def ano_lectivo(request): 
    # Obtém a escola da sessão
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')
    
    anos = AnoLectivo.objects.filter(escola=escola_usuario).order_by("-id") 

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
            AnoLectivo.objects.create(escola=escola_usuario, ano=ano_valor, estado="Aberto")
            messages.success(request, "Ano lectivo cadastrado com sucesso.")

        return redirect("administracao:ano_lectivo")

    perfil = request.user.perfil
    usuario = request.user
    if perfil == 'diretor_admin':
        return render(request, "administracao/diretor_admin/ano-lectivo.html", {"anos": anos, "usuario":usuario, "escola": escola_usuario})
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
     
def logout_view(request): 
    logout(request)  
    return redirect('core:login') 
