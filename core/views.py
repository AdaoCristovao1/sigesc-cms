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
from escola.models import Escola

def login_view(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        perfis_sem_escola = ['admin_central']

        if user is not None:
            # Perfis que NÃO passam pela seleção de escola (acesso direto)
            # Removido 'professor' da lista abaixo
            perfis_acesso_direto = ['aluno']  # ← professor removido
            
            if user.perfil in perfis_acesso_direto:
                # acesso direto
                login(request, user)
                
                perfil = user.perfil
 
                # Redirecionamento baseado no perfil 
                if perfil in ['admin_central']:
                    return redirect('escola:dashboard')
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

            
            if user.perfil in perfis_sem_escola:
                login(request, user)

                if user.perfil == 'admin_central':
                    return redirect('escola:dashboard')         
            else:
                    
                # Para outros perfis (incluindo professor agora), verificar escolas vinculadas
                # Buscar escolas através do funcionário
                escolas_usuario = []
                
                try:
                    # Tenta encontrar o funcionário vinculado ao usuário
                    funcionario = Funcionario.objects.filter(usuario=user).first()
                    if funcionario:
                        escolas_usuario = funcionario.escolas.all()
                except:
                    pass
                
                # Se o usuário tiver escola diretamente no modelo Usuario
                if not escolas_usuario and user.escola:
                    escolas_usuario = [user.escola]
                
                if escolas_usuario:
                    # Se tiver apenas uma escola, pode redirecionar direto (opcional)
                    if len(escolas_usuario) == 1:
                        # Faz login direto sem perguntar
                        login(request, user)
                        request.session['escola_atual_id'] = escolas_usuario[0].id
                        request.session['escola_atual_nome'] = escolas_usuario[0].nome
                        
                        # Redireciona baseado no perfil
                        perfil = user.perfil
                        if perfil in ['admin_central']:
                            return redirect('escola:dashboard')
                        if perfil in ['diretor_geral', 'secretario_geral']:
                            return redirect('core:dashboard')
                        elif perfil in ['diretor_admin', 'secretario_admin', 'coordenador_turno']:
                            return redirect('administracao:dashboard')
                        elif perfil in ['diretor_pedagogico', 'secretario_ped', 'coordenador_turma', 'coordenador_disc', 'professor']:
                            return redirect('pedagogico:dashboard')
                        else:
                            return redirect('core:dashboard')
                    else:
                        # Armazena o usuário na sessão sem fazer login ainda
                        request.session['pre_login_user_id'] = user.id
                        request.session['pre_login_password'] = password 
                        
                        return render(request, 'core/selecionar_escola.html', {
                            'escolas': escolas_usuario,
                            'user_nome': user.get_full_name() or user.username,
                            'user_perfil': user.perfil
                        })
                else:
                    # Se não tiver escolas vinculadas
                    messages.error(request, 'Usuário não vinculado a nenhuma escola.')
                    return render(request, 'core/index.html')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'core/index.html')

def selecionar_escola(request):
    """View para processar a seleção da escola"""
    if request.method == 'POST':
        escola_id = request.POST.get('escola_id')
        user_id = request.session.get('pre_login_user_id')
        
        if not user_id:
            messages.error(request, 'Sessão expirada. Faça login novamente.')
            return redirect('core:login')
        
        try:
            from django.contrib.auth import authenticate
            # Recupera o usuário
            user = Usuario.objects.get(id=user_id)
            
            # Autentica o usuário novamente (você pode pedir a senha novamente por segurança)
            # Por simplicidade, vamos fazer o login direto, mas é recomendado reautenticar
            
            # Faz o login do usuário
            login(request, user)
            
            # Armazena a escola selecionada na sessão
            escola = Escola.objects.get(id=escola_id)
            request.session['escola_atual_id'] = escola.id
            request.session['escola_atual_nome'] = escola.nome
            
            # Limpa os dados de pré-login
            del request.session['pre_login_user_id']
            
            # Redireciona baseado no perfil
            perfil = user.perfil
            
            if perfil in ['admin_central', 'diretor_geral', 'secretario_geral']:
                return redirect('core:dashboard')
            elif perfil in ['diretor_admin', 'secretario_admin', 'coordenador_turno']:
                return redirect('administracao:dashboard')
            elif perfil in ['diretor_pedagogico', 'secretario_ped', 'coordenador_turma', 'coordenador_disc']:
                return redirect('pedagogico:dashboard')
            else:
                messages.error(request, 'Perfil de usuário não reconhecido.')
                return redirect('core:login')
                
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuário não encontrado.')
            return redirect('core:login')
        except Escola.DoesNotExist:
            messages.error(request, 'Escola não encontrada.')
            return redirect('core:login')
    
    return redirect('core:login')

def logout_view(request):
    logout(request)
    return redirect('core:login')

@login_required
def dashboard(request):
    # Verifica se há escola selecionada na sessão
    escola_id_sessao = request.session.get('escola_atual_id')
    
    # Perfis que NÃO usam seleção de escola
    perfis_sem_selecao = ['professor', 'aluno']
    
    if request.user.perfil not in perfis_sem_selecao:
        if not escola_id_sessao:
            # Se não tem escola na sessão, tenta buscar do funcionário
            try:
                funcionario = Funcionario.objects.filter(usuario=request.user).first()
                if funcionario and funcionario.escolas.count() == 1:
                    # Se tem apenas uma escola, seleciona automaticamente
                    escola = funcionario.escolas.first()
                    request.session['escola_atual_id'] = escola.id
                    request.session['escola_atual_nome'] = escola.nome
                    escola_usuario = escola
                else:
                    # Se tem múltiplas escolas, redireciona para seleção
                    return redirect('core:selecionar_escola')
            except:
                return redirect('core:selecionar_escola')
        else:
            # Usa a escola da sessão
            try:
                escola_usuario = Escola.objects.get(id=escola_id_sessao)
            except Escola.DoesNotExist:
                return redirect('core:selecionar_escola')
    else:
        # Para professor e aluno, usa a escola do usuário diretamente
        escola_usuario = request.user.escola
    
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

    # Ano letivo aberto
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
    
    # Dados filtrados pela escola do usuário
    professores_total = Funcionario.objects.filter(
        escolas=escola_usuario,
        funcao__icontains='professor'
    ).distinct().count()
    
    funcionarios_total = Funcionario.objects.filter(
        escolas=escola_usuario
    ).exclude(
        funcao__icontains='professor'
    ).distinct().count()
    
    # Total de alunos da escola
    if ano_letivo:
        aluno_total = Reconfirmacao.objects.filter(
            ano_letivo=ano_letivo,
            aluno__escola=escola_usuario
        ).count()
        
        aluno_inadimplentes_total = Reconfirmacao.objects.filter(
            ano_letivo=ano_letivo,
            aluno__escola=escola_usuario,
            estado='Inadimplente'
        ).count()
    else:
        aluno_total = 0
        aluno_inadimplentes_total = 0
    
    # Total de turmas da escola
    total_turmas = Turma.objects.filter(escola=escola_usuario).count()
    
    context = {
        'usuario': usuario,
        'escola': escola_usuario,
        'professores_total': professores_total,
        'funcionarios_total': funcionarios_total,
        'aluno_total': aluno_total,
        'aluno_inadimplentes_total': aluno_inadimplentes_total,
        'total_turmas': total_turmas,
        'ano_lectivo_atual': ano_letivo.ano if ano_letivo else datetime.now().year,
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
    # Obtém a escola da sessão
    escola_id_sessao = request.session.get('escola_atual_id')
    
    # Verifica se há uma escola selecionada na sessão (para perfis que não são aluno/professor)
    perfis_sem_selecao = ['aluno', 'professor']
    
    if request.user.perfil not in perfis_sem_selecao:
        if not escola_id_sessao:
            messages.warning(request, 'Por favor, selecione uma escola primeiro.')
            return redirect('core:selecionar_escola')
        
        try:
            escola_usuario = Escola.objects.get(id=escola_id_sessao)
        except Escola.DoesNotExist:
            messages.error(request, 'Escola não encontrada.')
            return redirect('core:selecionar_escola')
    else:
        # Para alunos e professores, usa a escola do próprio usuário
        escola_usuario = request.user.escola
    
    # Busca o funcionário vinculado ao usuário (para outros perfis)
    funcionario_usuario = None
    if request.user.perfil not in perfis_sem_selecao:
        try:
            funcionario_usuario = Funcionario.objects.filter(usuario=request.user).first()
        except:
            pass
    
    # Filtra usuários pela escola
    # Busca todos os usuários que pertencem à escola selecionada
    q = request.GET.get('q')
    
    # Alunos da escola selecionada (via modelo Aluno)
    from pedagogico.models import Aluno
    alunos_da_escola = Aluno.objects.filter(escola=escola_usuario).values_list('usuario_id', flat=True)
    
    # Funcionários da escola selecionada
    funcionarios_da_escola = Funcionario.objects.filter(escolas=escola_usuario).values_list('usuario_id', flat=True)
    
    # Combina os IDs dos usuários da escola
    usuarios_na_escola = set(list(alunos_da_escola) + list(funcionarios_da_escola))
    
    # Aplica o filtro de busca
    if q:
        filtro = Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
        # Filtra apenas usuários da escola e aplica busca
        usuarios_filtrados = Usuario.objects.filter(filtro, id__in=usuarios_na_escola)
    else:
        # Pega apenas usuários da escola
        usuarios_filtrados = Usuario.objects.filter(id__in=usuarios_na_escola)
    
    # Separa alunos e outros perfis
    alunos = usuarios_filtrados.filter(perfil='aluno')
    outros = usuarios_filtrados.exclude(perfil='aluno')
    
    # Para cada usuário, busca informações adicionais
    for usuario in outros:
        try:
            funcionario = Funcionario.objects.filter(usuario=usuario).first()
            if funcionario:
                usuario.funcao = funcionario.funcao
                usuario.escolas_vinculadas = funcionario.escolas.all()
            else:
                usuario.funcao = usuario.perfil
                usuario.escolas_vinculadas = [escola_usuario]
        except:
            usuario.funcao = usuario.perfil
            usuario.escolas_vinculadas = [escola_usuario]
    
    for aluno in alunos:
        try:
            aluno_obj = Aluno.objects.filter(usuario=aluno).first()
            if aluno_obj:
                aluno.turma_atual = aluno_obj.turma
                aluno.numero_processo = aluno_obj.numero_processo
        except:
            pass
    
    perfil = request.user.perfil
    usuario = request.user
    
    context = {
        'alunos': alunos,
        'outros': outros,
        'usuario': usuario,
        'escola': escola_usuario,
        'funcionario_usuario': funcionario_usuario,
        'total_usuarios': usuarios_filtrados.count(),
        'total_alunos': alunos.count(),
        'total_funcionarios': outros.count(),
    }

    if perfil == 'diretor_geral':
        return render(request, 'core/usuarios-list.html', context)
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/usuarios-list.html', context)
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
    # Obtém a escola da sessão
    escola_id_sessao = request.session.get('escola_atual_id')
    
    # Verifica permissão
    perfis_permitidos = ['diretor_geral', 'secretario_geral']
    if request.user.perfil not in perfis_permitidos:
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
    
    # Verifica se há escola selecionada
    if not escola_id_sessao:
        messages.warning(request, 'Por favor, selecione uma escola primeiro.')
        return redirect('core:selecionar_escola')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')
    
    # Processa formulário
    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario_id')
        nome = request.POST.get('nome')
        bi = request.POST.get('bi')
        genero = request.POST.get('genero')
        funcao = request.POST.get('funcao')
        telefone = request.POST.get('telefone')
        email = request.POST.get('email')
        salario = request.POST.get('salario', '0')
        nivel_academico = request.POST.get('nivel_academico', '')
        area_formacao = request.POST.get('area_formacao', '')
        ativo = request.POST.get('ativo') == 'on'
        
        # Validação
        erros = {}
        
        if not nome:
            erros['nome'] = 'Nome é obrigatório'
        if not bi:
            erros['bi'] = 'BI é obrigatório'
        if not genero:
            erros['genero'] = 'Gênero é obrigatório'
        if not funcao:
            erros['funcao'] = 'Função é obrigatória'
        if not telefone:
            erros['telefone'] = 'Telefone é obrigatório'
        
        # Verifica se BI já existe (exceto para o mesmo funcionário)
        if funcionario_id:
            bi_exists = Funcionario.objects.filter(bi=bi).exclude(id=funcionario_id).exists()
        else:
            bi_exists = Funcionario.objects.filter(bi=bi).exists()
        
        if bi_exists:
            erros['bi'] = 'Este BI já está cadastrado'
        
        if erros:
            # Retorna com erros
            q = request.GET.get('q')
            if q:
                filtro = (Q(nome__icontains=q) | Q(bi__icontains=q) | 
                         Q(funcao__icontains=q) | Q(telefone__icontains=q))
                funcionarios = Funcionario.objects.filter(filtro, escolas=escola_usuario).distinct()
            else:
                funcionarios = Funcionario.objects.filter(escolas=escola_usuario).distinct()
            
            context = {
                'funcionarios': funcionarios,
                'usuario': request.user,
                'escola': escola_usuario,
                'erros': erros,
                'dados_post': request.POST,
            }
            
            if request.user.perfil == 'diretor_geral':
                return render(request, 'core/form-func.html', context)
            else:
                return render(request, 'core/secretario_geral/form-func.html', context)
        
        # Processa salário
        try:
            salario = Decimal(salario.replace(',', '.')) if salario else Decimal('0')
        except:
            salario = Decimal('0')
        
        try:
            with transaction.atomic():
                if funcionario_id:
                    # Atualiza funcionário existente
                    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
                    funcionario.nome = nome
                    funcionario.bi = bi
                    funcionario.genero = genero
                    funcionario.funcao = funcao
                    funcionario.telefone = telefone
                    funcionario.email = email
                    funcionario.salario = salario
                    funcionario.nivel_academico = nivel_academico
                    funcionario.area_formacao = area_formacao
                    funcionario.ativo = ativo
                    funcionario.save()
                    
                    # Atualiza usuário se existir
                    if funcionario.usuario:
                        nomes = remover_acentos(nome.lower()).split()
                        primeiro_nome = nomes[0]
                        ultimo_nome = nomes[-1] if len(nomes) > 1 else nomes[0]
                        funcionario.usuario.first_name = primeiro_nome.capitalize()
                        funcionario.usuario.last_name = ultimo_nome.capitalize()
                        funcionario.usuario.perfil = mapear_perfil_para_funcao(funcao)
                        funcionario.usuario.save()
                    
                    messages.success(request, f'Funcionário {nome} atualizado com sucesso!')
                else:
                    # Cria novo funcionário
                    funcionario = Funcionario.objects.create(
                        nome=nome,
                        bi=bi,
                        genero=genero,
                        funcao=funcao,
                        telefone=telefone,
                        email=email,
                        salario=salario,
                        nivel_academico=nivel_academico,
                        area_formacao=area_formacao,
                        ativo=ativo
                    )
                    
                    # Adiciona a escola da sessão (single)
                    funcionario.escolas.add(escola_usuario)
                    import re
                    import random
                    import string

                    # 🔹 Nome original
                    print("NOME ORIGINAL:", nome)

                    # 🔹 Remove acentos
                    nome_processado = remover_acentos(nome.lower())
                    print("APÓS remover_acentos:", nome_processado)

                    # 🔹 Divide por underscore OU espaço
                    nomes = re.split(r'[_\s]+', nome_processado)
                    nomes = [n for n in nomes if n]  # remove vazios

                    print("LISTA NOMES:", nomes)

                    # 🔹 Primeiro e último nome corretos
                    primeiro_nome = nomes[0]
                    ultimo_nome = nomes[-1] if len(nomes) > 1 else nomes[0]

                    print("PRIMEIRO NOME:", primeiro_nome)
                    print("ÚLTIMO NOME:", ultimo_nome)

                    # 🔹 Gera código de 3 caracteres
                    def gerar_codigo(tamanho=3):
                        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=tamanho))

                    codigo = gerar_codigo()

                    # 🔹 Username final
                    username = f"{primeiro_nome}{ultimo_nome}{codigo}@sigesc.co.ao"
                    email = username

                    # 🔹 Garante que é único
                    while Usuario.objects.filter(username=username).exists():
                        codigo = gerar_codigo()
                        username = f"{primeiro_nome}{ultimo_nome}{codigo}@sigesc.co.ao"

                    print("USERNAME FINAL:", username)

                    # 🔹 Criação do usuário
                    usuario = Usuario.objects.create_user(
                        username=username,
                        email=email,
                        password=bi,
                        first_name=primeiro_nome.capitalize(),
                        last_name=ultimo_nome.capitalize(),
                        perfil=mapear_perfil_para_funcao(funcao),
                        escola=escola_usuario
                    )

                    print("USUÁRIO CRIADO COM SUCESSO!")
                    funcionario.usuario = usuario
                    funcionario.save()
                    
                    messages.success(
                        request, 
                        f'Funcionário {nome} cadastrado com sucesso!'
                        f'Usuário: {username}Senha inicial: {bi}'
                    )
                
                return redirect('core:cadastrar_funcionario')
                
        except Exception as e:
            messages.error(request, f'Erro ao salvar: {str(e)}')
            return redirect('core:cadastrar_funcionario')
    
    # GET - Busca funcionários da escola selecionada
    q = request.GET.get('q')
    funcionario_id = request.GET.get('editar')
    
    # Busca funcionário para edição
    funcionario_editar = None
    if funcionario_id:
        try:
            funcionario_editar = Funcionario.objects.get(id=funcionario_id, escolas=escola_usuario)
        except Funcionario.DoesNotExist:
            messages.error(request, 'Funcionário não encontrado nesta escola.')
    
    # Filtro de busca
    if q:
        filtro = (Q(nome__icontains=q) | Q(bi__icontains=q) | 
                 Q(funcao__icontains=q) | Q(telefone__icontains=q))
        funcionarios = Funcionario.objects.filter(filtro, escolas=escola_usuario).distinct()
    else:
        funcionarios = Funcionario.objects.filter(escolas=escola_usuario).distinct()
    
    # Ordenação
    funcionarios = funcionarios.order_by('-criado_em')
    
    context = {
        'funcionarios': funcionarios,
        'usuario': request.user,
        'escola': escola_usuario,
        'funcionario': funcionario_editar,
    }
    
    if request.user.perfil == 'diretor_geral':
        return render(request, 'core/form-func.html', context)
    else:
        return render(request, 'core/secretario_geral/form-func.html', context)

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

def remover_acentos(texto):
    """Remove acentos de uma string"""
    if not texto:
        return texto
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto.replace(' ', '_').lower()


@login_required
def editar_funcionario(request, pk):
    """View específica para edição via URL"""
    escola_id_sessao = request.session.get('escola_atual_id')
    
    if not escola_id_sessao:
        messages.warning(request, 'Por favor, selecione uma escola primeiro.')
        return redirect('core:selecionar_escola')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
        funcionario = get_object_or_404(Funcionario, id=pk, escolas=escola_usuario)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:cadastrar_funcionario')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        bi = request.POST.get('bi')
        genero = request.POST.get('genero')
        funcao = request.POST.get('funcao')
        telefone = request.POST.get('telefone')
        email = request.POST.get('email')
        salario = request.POST.get('salario', '0')
        nivel_academico = request.POST.get('nivel_academico', '')
        area_formacao = request.POST.get('area_formacao', '')
        ativo = request.POST.get('ativo') == 'on'
        
        # Verifica se BI já existe para outro funcionário
        if Funcionario.objects.filter(bi=bi).exclude(id=pk).exists():
            messages.error(request, 'Este BI já está cadastrado para outro funcionário.')
            return redirect('core:editar_funcionario', pk=pk)
        
        try:
            with transaction.atomic():
                funcionario.nome = nome
                funcionario.bi = bi
                funcionario.genero = genero
                funcionario.funcao = funcao
                funcionario.telefone = telefone
                funcionario.email = email
                funcionario.salario = Decimal(salario.replace(',', '.')) if salario else Decimal('0')
                funcionario.nivel_academico = nivel_academico
                funcionario.area_formacao = area_formacao
                funcionario.ativo = ativo
                funcionario.save()
                
                # Atualiza usuário
                if funcionario.usuario:
                    nomes = remover_acentos(nome.lower()).split()
                    primeiro_nome = nomes[0]
                    ultimo_nome = nomes[-1] if len(nomes) > 1 else nomes[0]
                    funcionario.usuario.first_name = primeiro_nome.capitalize()
                    funcionario.usuario.last_name = ultimo_nome.capitalize()
                    funcionario.usuario.perfil = mapear_perfil_para_funcao(funcao)
                    funcionario.usuario.save()
                
                messages.success(request, f'Funcionário {nome} atualizado com sucesso!')
                return redirect('core:cadastrar_funcionario')
                
        except Exception as e:
            messages.error(request, f'Erro ao atualizar: {str(e)}')
            return redirect('core:editar_funcionario', pk=pk)
    
    # GET - Mostra formulário de edição
    context = {
        'funcionario': funcionario,
        'usuario': request.user,
        'escola': escola_usuario,
        'modo_edicao': True,
    }
    
    return render(request, 'core/form-func.html', context)

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
    # Obtém a escola da sessão
    escola_id_sessao = request.session.get('escola_atual_id')
    
    # Verifica se o usuário tem permissão
    perfis_permitidos = ['diretor_geral', 'secretario_geral', 'diretor_pedagogico', 'secretario_ped']
    
    if request.user.perfil not in perfis_permitidos:
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
    
    # Verifica se há uma escola selecionada na sessão (para perfis que não são aluno/professor)
    perfis_sem_selecao = ['aluno', 'professor']
    
    if request.user.perfil not in perfis_sem_selecao:
        if not escola_id_sessao:
            messages.warning(request, 'Por favor, selecione uma escola primeiro.')
            return redirect('core:selecionar_escola')
        
        try:
            escola_usuario = Escola.objects.get(id=escola_id_sessao)
        except Escola.DoesNotExist:
            messages.error(request, 'Escola não encontrada.')
            return redirect('core:selecionar_escola')
    else:
        # Para professores, usa a escola do próprio usuário
        escola_usuario = request.user.escola
    
    # Busca funcionários com função de professor que estão vinculados à escola selecionada
    q = request.GET.get('q')
    tipo_filtro = request.GET.get('tipo')  # 'ativos', 'inativos', 'todos'
    
    # Query base
    funcionarios_query = Funcionario.objects.filter(
        funcao='Professor',
        escolas=escola_usuario
    ).distinct().select_related('usuario')
    
    # Aplica filtro de status
    if tipo_filtro == 'ativos':
        funcionarios_query = funcionarios_query.filter(ativo=True)
    elif tipo_filtro == 'inativos':
        funcionarios_query = funcionarios_query.filter(ativo=False)
    
    # Aplica busca
    if q:
        filtro = (
            Q(nome__icontains=q) |
            Q(bi__icontains=q) |
            Q(telefone__icontains=q) |
            Q(email__icontains=q) |
            Q(area_formacao__icontains=q) |
            Q(nivel_academico__icontains=q) |
            Q(usuario__username__icontains=q)
        )
        funcionarios = funcionarios_query.filter(filtro)
    else:
        funcionarios = funcionarios_query
    
    # Ordenação
    ordenar_por = request.GET.get('ordenar', 'nome')
    if ordenar_por == 'nome':
        funcionarios = funcionarios.order_by('nome')
    elif ordenar_por == 'data_criacao':
        funcionarios = funcionarios.order_by('-criado_em')
    elif ordenar_por == 'area_formacao':
        funcionarios = funcionarios.order_by('area_formacao')
    
    # Paginação
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    page = request.GET.get('page', 1)
    paginator = Paginator(funcionarios, 15)
    
    try:
        funcionarios_page = paginator.page(page)
    except PageNotAnInteger:
        funcionarios_page = paginator.page(1)
    except EmptyPage:
        funcionarios_page = paginator.page(paginator.num_pages)
    
    # Estatísticas
    total_docentes = funcionarios_query.count()
    docentes_ativos = funcionarios_query.filter(ativo=True).count()
    docentes_inativos = funcionarios_query.filter(ativo=False).count()
    
    # Agrupamento por área de formação
    from django.db.models import Count
    areas_formacao = funcionarios_query.values('area_formacao').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Agrupamento por nível acadêmico
    niveis_academicos = funcionarios_query.values('nivel_academico').annotate(
        total=Count('id')
    ).order_by('-total')
    
    perfil = request.user.perfil
    usuario = request.user
    
    # Busca informação do funcionário logado (se for professor)
    funcionario_logado = None
    if request.user.perfil == 'professor':
        try:
            funcionario_logado = Funcionario.objects.filter(
                usuario=request.user,
                escolas=escola_usuario
            ).first()
        except:
            pass
    
    context = {
        'funcionarios': funcionarios_page,
        'usuario': usuario,
        'escola': escola_usuario,
        'total_docentes': total_docentes,
        'docentes_ativos': docentes_ativos,
        'docentes_inativos': docentes_inativos,
        'areas_formacao': areas_formacao,
        'niveis_academicos': niveis_academicos,
        'q': q,
        'tipo_filtro': tipo_filtro,
        'ordenar_por': ordenar_por,
        'funcionario_logado': funcionario_logado,
    }

    if perfil == 'diretor_geral':
        return render(request, 'core/docentes.html', context)
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/docentes.html', context)
    elif perfil in ['diretor_pedagogico', 'secretario_ped']:
        return render(request, 'core/pedagogico/docentes.html', context)
    elif perfil == 'professor':
        return render(request, 'core/professor/docentes.html', context)
    else:
        return redirect('core:dashboard')
    
@login_required
def vinculo_docente(request, professor_id, vinculo_id=None):
    """
    View unificada para criar (se vinculo_id=None) ou editar vínculos de docentes.
    Gerencia tanto o vínculo quanto os horários associados.
    """
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'}) 
    
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
    professor = get_object_or_404(Funcionario, id=professor_id, funcao__icontains='professor', escolas=escola_usuario)
    
    # Determinar se é criação ou edição
    modo_edicao = vinculo_id is not None
    
    if modo_edicao:
        # Modo edição - obter vínculo existente
        vinculo = get_object_or_404(ProfessorVinculo, id=vinculo_id, professor=professor, escola=escola_usuario)
    else:
        # Modo criação - vínculo será criado
        vinculo = None
    
    # Obter dados para o formulário
    turmas = Turma.objects.select_related('classe', 'curso').filter(escola=escola_usuario)
    disciplinas = Disciplina.objects.filter(escola=escola_usuario)
    
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
                turma = get_object_or_404(Turma, id=turma_id, escola=escola_usuario)
                disciplina = get_object_or_404(Disciplina, id=disciplina_id, escola=escola_usuario)
                
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
                                    horario = get_object_or_404(HorarioAula, id=horarios_ids[i], vinculo=vinculo, escola=escola_usuario)
                                    horario.dia_semana = horario_data['dia_semana']
                                    horario.hora_inicio = horario_data['hora_inicio']
                                    horario.hora_fim = horario_data['hora_fim']
                                    horario.tempo_aula = horario_data['tempo_aula']
                                    horario.save()
                                    horarios_para_manter.append(horario.id)
                                else:
                                    # Criar novo horário
                                    novo_horario = HorarioAula.objects.create(escola=escola_usuario, **horario_data) 
                                    horarios_para_manter.append(novo_horario.id)
                        
                        # Remover horários que não estão mais no formulário
                        vinculo.horarios.exclude(id__in=horarios_para_manter).delete()
                        
                        messages.success(request, 'Vínculo atualizado com sucesso!')
                    else:
                        # Criar novo vínculo
                        vinculo = ProfessorVinculo.objects.create(
                            escola=escola_usuario,
                            professor=professor,
                            disciplina=disciplina,
                            turma=turma
                        )
                        
                        # Criar os Horários associados
                        for i in range(len(dias)):
                            if dias[i] and inicios[i] and fims[i]:
                                HorarioAula.objects.create(
                                    escola=escola_usuario,
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
        'escola': escola_usuario,
    }
    
    # Determinar qual template usar baseado no perfil
    if perfil == 'diretor_geral':
        template = 'core/vinculo-docente.html'
    if perfil == 'diretor_pedagogico':
        template = 'pedagogico/diretor_pedagogico/vinculo-docente.html'
    if perfil == 'secretario_ped':
        template = 'pedagogico/secretario_ped/vinculo-docente.html'
    if perfil == 'secretario_geral': 
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
    escola_id_sessao = request.session.get('escola_atual_id')
    aluno = Aluno.objects.filter(escola=escola_id_sessao)
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
        
    anos_disponiveis = AnoLectivo.objects.filter(escola=escola_usuario).order_by('-ano')
     
    ano_letivo = request.GET.get("ano_lectivo")

    if not ano_letivo:
        ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()

    query = request.GET.get('q', '')
    turmas = Turma.objects.select_related('classe', 'curso', 'sala').filter(ano_letivo=ano_letivo, escola=escola_usuario)
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

    professores = Funcionario.objects.filter(funcao__icontains='professor', escolas=escola_usuario)
    disciplinas = Disciplina.objects.filter(escola=escola_usuario)

    # Base query
    reconfirmacoes = Reconfirmacao.objects.select_related(
        'aluno', 'turma', 'sala', 'classe', 'curso'
    ).filter(ano_letivo=ano_letivo, escola=escola_usuario)

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
        'professores':professores,
        'disciplinas':disciplinas,
        'anos_disponiveis':anos_disponiveis,
        'escola': escola_usuario
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    aluno = get_object_or_404(Aluno, pk=id)
    atualizar_estado_aluno(aluno, escola_usuario)
    
    ultima_reconfirmacao = Reconfirmacao.objects.filter(escola=escola_usuario, aluno=aluno).order_by('-ano_letivo').last()
    
    notas = Nota.objects.filter(escola=escola_usuario, aluno=aluno).select_related('disciplina', 'classe')
    
    medias = {}
    disciplinas = Disciplina.objects.filter(escola=escola_usuario)
    disc = Disciplina.objects.filter(escola=escola_usuario)

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
            'usuario':usuario,
            "escola": escola_usuario
        })
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/aluno-detalhe.html', {
            'aluno': aluno,
            'ultima_reconfirmacao': ultima_reconfirmacao,
            'medias': medias,
            'disciplinas': disciplinas,
            'disc':disc,
            'usuario':usuario,
            "escola": escola_usuario
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    if request.method == 'POST':
        aluno_id = request.POST.get('aluno_id')
        disciplina_id = request.POST.get('disciplina_id')
        classe_id = request.POST.get('classe_id')
        ano_letivo_id = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()
        if ano_letivo_id:
            ano_letivo_id = ano_letivo_id.id
 
        trimestre = request.POST.get('trimestre')
        valor = request.POST.get('valor')

        if not all([aluno_id, disciplina_id, classe_id, ano_letivo_id, trimestre, valor]):
            messages.error(request, 'Todos os campos são obrigatórios.')
            return redirect(request.META.get('HTTP_REFERER'))

        try:
            nota_existente = Nota.objects.filter(
                escola=escola_usuario,
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
                    escola=escola_usuario,
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    classes = Classe.objects.filter(escola=escola_usuario).order_by('numero')

    perfil = request.user.perfil 
    usuario = request.user   
     
    if perfil == 'diretor_geral':
        return render(request, 'core/classes.html', {'classes': classes, 'usuario':usuario, 'escola':escola_usuario})
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
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    if request.method == 'POST':
        Classe.objects.create(
            escola=escola_usuario,
            designacao=request.POST['designacao'],
            numero=request.POST['numero']
        )
    return redirect('core:classes')

@login_required
def atualizar_classe(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    cursos = Curso.objects.filter(escola=escola_usuario).order_by('nome')
    perfil = request.user.perfil   
    usuario = request.user
     
    if perfil == 'diretor_geral':
        return render(request, 'core/cursos.html', {'cursos': cursos, 'usuario':usuario, 'escola': escola_usuario})
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
        return JsonResponse({
            'success': False,
            'message': 'Escola inválida.'
        })

    if request.method == 'POST':
        Curso.objects.create(
            escola=escola_usuario,
            nome=request.POST['nome'],
            tipo=request.POST['tipo'],
        )

    return redirect('core:cursos')

@login_required
def atualizar_curso(request):
    if request.method == 'POST':
        curso = get_object_or_404(Curso, pk=request.POST['id'])

        curso.nome = request.POST['nome']
        curso.tipo = request.POST['tipo']

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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    if request.method == 'POST':
        qtd_salas = int(request.POST.get('quantidade', 0))
        total_existentes = Sala.objects.filter(escola=escola_usuario).count()

        if qtd_salas > total_existentes:
            for i in range(total_existentes + 1, qtd_salas + 1):
                Sala.objects.create(nome=str(i), escola=escola_usuario)
        elif qtd_salas < total_existentes:
           salas_para_excluir = Sala.objects.filter(escola=escola_usuario).order_by('-id')[:total_existentes - qtd_salas]
           for sala in salas_para_excluir:
               sala.delete()


        return redirect('core:turmas_e_salas')
    
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()

    salas = Sala.objects.filter(escola=escola_usuario).order_by('id')
    turmas = Turma.objects.filter(ano_letivo=ano_letivo, escola=escola_usuario).order_by('id')
    classes = Classe.objects.filter(escola=escola_usuario).order_by('id')
    cursos = Curso.objects.filter(escola=escola_usuario).order_by('id')
    salas = Sala.objects.filter(escola=escola_usuario).order_by('id')

    perfil = request.user.perfil  
    usuario = request.user 
     
    if perfil == 'diretor_geral':
        return render(request, 'core/turmas-salas.html', {'turmas': turmas, 'classes': classes, 'cursos': cursos, 'salas': salas,'total': salas.count(), 'usuario':usuario, 'ano_letivo':ano_letivo, 'escola': escola_usuario})
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/turmas-salas.html', {'turmas': turmas, 'classes': classes, 'cursos': cursos, 'salas': salas,'total': salas.count(), 'usuario':usuario, 'ano_letivo':ano_letivo, 'escola': escola_usuario})
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        turno = request.POST.get('turno')
        classe_id = request.POST.get('classe')
        curso_id = request.POST.get('curso')
        sala_id = request.POST.get('sala')
        ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()

        if not (nome and turno and classe_id and curso_id):
            messages.error(request, "Todos os campos obrigatórios devem ser preenchidos.")
            return redirect(request.META.get('HTTP_REFERER'))

        # Verifica se a classe e curso existem
        classe = get_object_or_404(Classe, id=classe_id, escola=escola_usuario)
        curso = get_object_or_404(Curso, id=curso_id, escola=escola_usuario)

        # Valida se curso é "Base" quando a classe <= 9
        if classe.numero <= 9 and curso.nome.lower() != "base":
            messages.error(request, "Para classes do 1º ao 9º ano, o curso deve ser 'Base'.")
            return redirect(request.META.get('HTTP_REFERER'))

        # Valida se a sala tem menos de 3 turmas
        if sala_id:
            quantidade_turmas = Turma.objects.filter(sala_id=sala_id, ano_letivo=ano_letivo, escola=escola_usuario).count()
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
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
            quantidade_turmas = Turma.objects.filter(sala_id=sala_id, escola=escola_usuario).count()
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    query = request.GET.get('q')
    if query:
        disciplinas = Disciplina.objects.filter(nome__icontains=query, escola=escola_usuario)
    else:
        disciplinas = Disciplina.objects.filter(escola=escola_usuario)

    vinculacoes = DisciplinasClasse.objects.select_related('disciplina', 'classe').all()
    classes = Classe.objects.filter(escola=escola_usuario)

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
        'escola': escola_usuario,
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if nome:
            Disciplina.objects.create(escola=escola_usuario, nome=nome, classe = 0)
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    turmas = Turma.objects.select_related('classe', 'curso', 'sala').filter(escola=escola_usuario)
    classes = Classe.objects.filter(escola=escola_usuario)
    cursos = Curso.objects.filter(escola=escola_usuario)
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
    
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
                    escola=escola_usuario,
                    username=username,
                    password=senha,
                    first_name=nome_completo.split()[0],
                    last_name=" ".join(nome_completo.split()[1:]),
                    perfil='aluno'
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
            'usuario': usuario,
            'escola': escola_usuario,
        })
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/matriculas.html', {
            'turmas': turmas,
            'classes': classes,
            'cursos': cursos,
            'turmas_json': turmas_json,
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
def comprovativo_matricula(request, aluno_id):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
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
            'escola': escola_usuario,
        })
    elif perfil == 'secretario_geral': 
        return render(request, 'core/secretario_geral/comprovativo_matricula.html', {
            'aluno': aluno,
            'data': data_hoje,
            'atendido_por': request.user,
            'usuario':usuario,
            "barcode": barcode_base64,
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
def reconfirmacao(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    ano_letivo = AnoLectivo.objects.filter(estado='Fechado', escola=escola_usuario).last()
    ano_aberto = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()

    if request.method == 'GET':
        query = request.GET.get('q', '')

        # Base query
        reconfirmacoes = Reconfirmacao.objects.select_related(
            'aluno', 'turma', 'sala', 'classe', 'curso' 
        ).filter(ano_letivo=ano_letivo, escola=escola_usuario)

        turmas = Turma.objects.select_related('classe', 'curso', 'sala').filter(ano_letivo=ano_aberto, escola=escola_usuario)
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
                Q(turma__nome__icontains=query) |
                Q(escola=escola_usuario)
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
            'escola': escola_usuario
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
        ano_aberto = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).first()
        if not ano_aberto:
            messages.error(request, 'Não há ano letivo aberto para realizar a reconfirmação.')
            return redirect('core:reconfirmacao')
        
        # Verificar se já existe reconfirmação ativa para este aluno no ano letivo
        reconfirmacao_existente = Reconfirmacao.objects.filter(
            escola=escola_usuario,
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})

    perfil = request.user.perfil
    usuario = request.user

    if perfil == 'diretor_geral':
        return render(request, 'core/pautas.html', {'usuario':usuario, 'escola':escola_usuario})
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/pautas.html', {'usuario':usuario, 'escola':escola_usuario})
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    query = request.GET.get('q', '')
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()

    reconfirmacoes = Reconfirmacao.objects.select_related(
        'aluno', 'turma', 'sala', 'classe', 'curso'
    ).filter(ano_letivo=ano_letivo, escola=escola_usuario)

    if query:
        reconfirmacoes = reconfirmacoes.filter(
            Q(aluno__nome_completo__icontains=query) |
            Q(aluno__numero_mecanografico__icontains=query) |
            Q(turma__nome__icontains=query) |
            Q(escola=escola_usuario)
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
            escola=escola_usuario,
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
            'usuario': usuario,
            'escola': escola_usuario,
        })
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/pautas_trimestre.html', {
            'turmas_agrupadas': turmas_agrupadas,
            'search_query': query,
            'trimestre': trimestre,
            'texto': texto,
            'usuario': usuario,
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
def pautas_final(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    query = request.GET.get('q', '')
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()

    reconfirmacoes = Reconfirmacao.objects.select_related(
        'aluno', 'turma', 'sala', 'classe', 'curso'
    ).filter(ano_letivo=ano_letivo, escola=escola_usuario)

    if query:
        reconfirmacoes = reconfirmacoes.filter(
            Q(aluno__nome_completo__icontains=query) |
            Q(aluno__numero_mecanografico__icontains=query) |
            Q(turma__nome__icontains=query) |
            Q(escola=escola_usuario)
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
            'usuario': usuario, 
            'escola':escola_usuario
        })
    elif perfil == 'secretario_geral':
        return render(request, 'core/secretario_geral/pautas_finais.html', {
            'turmas_agrupadas': turmas_final,
            'usuario': usuario,
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

@login_required
def coordenacoes(request):
    perfil = request.user.perfil
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
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
        alunos = Aluno.objects.filter(turma=turma, escola=escola_usuario)
        pauta_alunos = []
        for aluno in alunos:
            linha = {
                'aluno': aluno.nome_completo,
                'disciplinas': [],
                'estado': 'Aprovado'
            }
            tem_todas_notas = True

            disciplinas_classe = DisciplinasClasse.objects.filter(classe=turma.classe, escola=escola_usuario).select_related('disciplina')
            for disc_classe in disciplinas_classe:
                nota = Nota.objects.filter(
                    escola=escola_usuario,
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
            alunos = Aluno.objects.filter(turma=turma, escola=escola_usuario)
            for aluno in alunos:
                nota = Nota.objects.filter(
                    escola=escola_usuario,
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
    professores = Funcionario.objects.filter(funcao__icontains='professor', escolas=escola_usuario)
    turmas = Turma.objects.filter(escola=escola_usuario)
    disciplinas = Disciplina.objects.filter(escola=escola_usuario)
    usuario = request.user

    contexto.update({
        'coordenacoes': Coordenacao.objects.select_related('funcionario', 'turma', 'disciplina').filter(escola=escola_usuario),
        'professores': professores,
        'turmas': turmas,
        'disciplinas': disciplinas,
        'trimestre': trimestre,
        'usuario':usuario,
        'escola': escola_usuario,
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
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario_id')
        tipo = request.POST.get('tipo')
        turma_id = request.POST.get('turma_id') or None
        disciplina_id = request.POST.get('disciplina_id') or None

        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        turma = Turma.objects.filter(id=turma_id).first() if turma_id else None
        disciplina = Disciplina.objects.filter(id=disciplina_id).first() if disciplina_id else None

        Coordenacao.objects.create(
            escola=escola_usuario,
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
    # Obtém a escola da sessão
    escola_id_sessao = request.session.get('escola_atual_id')
    
    # Verifica se o usuário tem permissão e se há escola selecionada
    if request.user.perfil != 'diretor_geral':
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
    
    # Verifica se há uma escola selecionada na sessão
    if not escola_id_sessao:
        messages.warning(request, 'Por favor, selecione uma escola primeiro.')
        return redirect('core:selecionar_escola')
    
    try:
        escola = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola não encontrada.')
        return redirect('core:selecionar_escola')
    
    # Filtra os anos lectivos pela escola selecionada
    anos = AnoLectivo.objects.filter(escola=escola).order_by("-id")

    if request.method == "POST":
        ano_id = request.POST.get("id")
        ano_valor = request.POST.get("ano")
        estado_valor = request.POST.get("estado")

        if ano_id:  # atualização
            ano_obj = get_object_or_404(AnoLectivo, id=ano_id, escola=escola)
            ano_obj.ano = ano_valor
            if estado_valor:
                # Se estiver fechando um ano, verificar se é o único aberto
                if estado_valor == "Fechado" and ano_obj.estado == "Aberto":
                    # Permite fechar o ano
                    ano_obj.estado = estado_valor
                elif estado_valor == "Aberto":
                    # Se for abrir um ano, fechar o último aberto da mesma escola
                    ultimo_ano_aberto = AnoLectivo.objects.filter(
                        escola=escola, 
                        estado="Aberto"
                    ).exclude(id=ano_id).last()
                    if ultimo_ano_aberto:
                        ultimo_ano_aberto.estado = "Fechado"
                        ultimo_ano_aberto.save()
                    ano_obj.estado = estado_valor
                else:
                    ano_obj.estado = estado_valor
            ano_obj.save()
            messages.success(request, "Ano lectivo atualizado com sucesso.")
        else:  # criação
            # Verifica se já existe um ano com o mesmo valor para esta escola
            if AnoLectivo.objects.filter(ano=ano_valor, escola=escola).exists():
                messages.error(request, f"O ano {ano_valor} já está cadastrado para esta escola.")
                return redirect("core:ano_lectivo")
            
            # Fecha o último ano aberto da mesma escola
            ultimo_ano_aberto = AnoLectivo.objects.filter(
                escola=escola, 
                estado="Aberto"
            ).last()
            if ultimo_ano_aberto:
                ultimo_ano_aberto.estado = "Fechado"
                ultimo_ano_aberto.save()
            
            # Cria o novo ano lectivo para a escola específica
            AnoLectivo.objects.create(
                ano=ano_valor, 
                estado="Aberto",
                escola=escola 
            )
            messages.success(request, "Ano lectivo cadastrado com sucesso.")

        return redirect("core:ano_lectivo")

    context = {
        "anos": anos, 
        "usuario": request.user,
        "escola": escola
    }
    
    return render(request, "core/ano-lectivo.html", context)

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