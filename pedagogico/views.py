import uuid
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from administracao.models import *
from django.contrib import messages
from . models import *
import json
from django.core.serializers.json import DjangoJSONEncoder
import random
import string
import unicodedata
from datetime import datetime 
from datetime import date
from django.db import transaction
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models import Prefetch
from pedagogico.models import Nota
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from financeiro.views import atualizar_estado_aluno
from reportlab.graphics.barcode import createBarcodeDrawing
import io
import base64
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth
import calendar

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

    if perfil == 'diretor_pedagogico': 
        return render(request, 'pedagogico/diretor_pedagogico/dashboard.html', context)
 
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/dashboard-secretario.html', context)
     
    elif perfil == 'professor':
        return render(request, 'pedagogico/professor/professor.html', context)
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

    if perfil == 'diretor_pedagogico': 
        return render(request, 'pedagogico/diretor_pedagogico/docentes.html',  {'funcionarios': funcionarios, 'usuario':usuario})
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/docentes.html',  {'funcionarios': funcionarios, 'usuario':usuario})
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
def vinculo_docente(request, professor_id):
    professor = Funcionario.objects.get(id=professor_id, funcao__icontains='professor')
    turmas = Turma.objects.select_related('classe','curso').all()
    disciplinas = Disciplina.objects.all()

    # Serializar turmas para JS
    turmas_json = json.dumps([
      {
        'id': t.id, 
        'turno': t.turno,
        'curso_nome': t.curso.nome,
        'classe_numero': t.classe.numero
      } for t in turmas
    ])

    if request.method == 'POST':
        turma = get_object_or_404(Turma, id=request.POST['turma'])
        disciplina = get_object_or_404(Disciplina, id=request.POST['disciplina'])
        ProfessorVinculo.objects.create(professor=professor, turma=turma, disciplina=disciplina)
        messages.success(request, 'Vínculo salvo!')
        return redirect('pedagogico:docentes')
    
    perfil = request.user.perfil
    usuario = request.user

    if perfil == 'diretor_pedagogico': 
        return render(request, 'pedagogico/diretor_pedagogico/vinculo-docente.html', {
        'professor': professor,
        'turmas': turmas,
        'disciplinas': disciplinas,
        'turmas_json': turmas_json,
        'usuario':usuario
        })
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/vinculo-docente.html', {
        'professor': professor,
        'turmas': turmas,
        'disciplinas': disciplinas,
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
def detalhes_professor(request, id):

    professor = get_object_or_404(
        Funcionario,
        pk=id,
        funcao__icontains='professor'
    )

    vinculos = professor.professorvinculo_set.select_related(
        'turma', 'disciplina', 'turma__classe', 'turma__curso'
    ).prefetch_related(
        models.Prefetch(
            'horarios',
            queryset=HorarioAula.objects.order_by('dia_semana', 'hora_inicio')
        )
    )

    data_detalhada = []

    for v in vinculos:
        horarios = v.horarios.all()
        for h in horarios:
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
                'vinculo_id': v.id,
            })

    data_detalhada.sort(key=lambda x: (x['dia'], x['inicio']))

    return JsonResponse({
        'nome': professor.nome,
        'nivel_academico': professor.nivel_academico or "---",
        'area_formacao': professor.area_formacao or "---",
        'horario_completo': data_detalhada,
        'total_horarios': len(data_detalhada),
    })

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

    if perfil == 'diretor_pedagogico': 
        return render(request, 'pedagogico/diretor_pedagogico/disciplinas.html', {'disciplinas': disciplinas, 'usuario':usuario, 'vinculacoes':vinculacoes, 'classes':classes})
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/disciplinas.html', {'disciplinas': disciplinas, 'usuario':usuario, 'vinculacoes':vinculacoes, 'classes':classes})
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
def criar_vinculo(request):
    if request.method == "POST":
        disciplina_id = request.POST.get("disciplina")
        classe_id = request.POST.get("classe")

        if not disciplina_id or not classe_id:
            messages.error(request, "Preencha todos os campos.")
            return redirect("pedagogico:disciplinas")

        disciplina = get_object_or_404(Disciplina, id=disciplina_id)
        classe = get_object_or_404(Classe, id=classe_id)

        DisciplinasClasse.objects.create(disciplina=disciplina, classe=classe)
        messages.success(request, "Vínculo criado com sucesso.")
        return redirect("pedagogico:disciplinas")

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
        return redirect("pedagogico:disciplinas")

@login_required
def excluir_vinculo(request, pk):
    vinculo = get_object_or_404(DisciplinasClasse, pk=pk)
    vinculo.delete()
    messages.success(request, "Vínculo excluído com sucesso.")
    return redirect("pedagogico:disciplinas")

@login_required
def criar_disciplina(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        if nome:
            Disciplina.objects.create(nome=nome, classe = 0)
            messages.success(request, 'Disciplina criada com sucesso.')
    return redirect('pedagogico:disciplinas')

@login_required
def editar_disciplina(request, id):
    disciplina = get_object_or_404(Disciplina, id=id)
    if request.method == 'POST':
        disciplina.nome = request.POST.get('nome')
        disciplina.save()
        messages.success(request, 'Disciplina atualizada.')
        return redirect('pedagogico:disciplinas')

@login_required
def deletar_disciplina(request, id):
    disciplina = get_object_or_404(Disciplina, id=id)
    if request.method == 'POST':
        senha = request.POST.get('password')
        
        disciplina.delete()
        messages.success(request, 'Disciplina deletada com sucesso.')

    return redirect('pedagogico:disciplinas')

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
        nome_completo = request.POST.get('nome_completo')
        bi = request.POST.get('bi')
        if not bi:
            caracteres = string.ascii_letters + string.digits
            bi = ''.join(random.choice(caracteres) for _ in range(14))
            
        genero = request.POST.get('genero')
        turma_id = request.POST.get('turma')
        classe_id = request.POST.get('classe')
        curso_id = request.POST.get('curso')

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

        # Criar usuário
        codigo_unico = str(uuid.uuid4())[:5]
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

                aluno = Aluno.objects.create(
                    usuario=user,
                    nome_completo=nome_completo,
                    numero_mecanografico=numero_mecanografico,
                    bi=bi,
                    genero=genero,
                    turma=turma,
                    sala=turma.sala,
                    classe=classe,
                    curso=curso,
                    turno=turma.turno
                )

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

        return redirect('pedagogico:comprovativo_matricula', aluno.id)
    
    perfil = request.user.perfil
    usuario = request.user

    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/matriculas.html', {
            'turmas': turmas,
            'classes': classes,
            'cursos': cursos,
            'turmas_json': turmas_json,
            'usuario':usuario
        })
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/matriculas.html', {
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

    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/comprovativo_matricula.html', {
            'aluno': aluno,
            'data': data_hoje,
            'atendido_por': request.user,
            'usuario':usuario,
            "barcode": barcode_base64,
        })
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/comprovativo_matricula.html', {
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
        if perfil == 'diretor_pedagogico':
            return render(request, 'pedagogico/diretor_pedagogico/reconfirmacao.html', context)
        elif perfil == 'secretario_ped':
            return render(request, 'pedagogico/secretario_ped/reconfirmacao.html', context)
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
            return redirect('pedagogico:reconfirmacao')
        
        # Verificar se já existe reconfirmação ativa para este aluno no ano letivo
        reconfirmacao_existente = Reconfirmacao.objects.filter(
            aluno=aluno,
            ano_letivo=ano_letivo,
            estado='Adimplente'
        ).first()
        
        if reconfirmacao_existente:
            messages.warning(request, f'Este aluno já foi reconfirmado para o ano letivo {ano_letivo}.')
            return redirect('pedagogico:reconfirmacao')
        
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
        return redirect('pedagogico:comprovativo_matricula', aluno_id=aluno.id)

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

        return redirect('pedagogico:turmas_e_salas')
    
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto').last()

    salas = Sala.objects.all().order_by('id')
    turmas = Turma.objects.filter(ano_letivo=ano_letivo).order_by('id')
    classes = Classe.objects.all().order_by('id')
    cursos = Curso.objects.all().order_by('id')
    salas = Sala.objects.all().order_by('id')
    perfil = request.user.perfil
    usuario = request.user

    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/turmas-salas.html', {'turmas': turmas, 'classes': classes, 'cursos': cursos, 'salas': salas,'total': salas.count(), 'usuario':usuario, 'ano_letivo':ano_letivo})
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/turmas-salas.html', {'turmas': turmas, 'classes': classes, 'cursos': cursos, 'salas': salas,'total': salas.count(), 'usuario':usuario, 'ano_letivo':ano_letivo})
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
def alunos(request):
    aluno = Aluno.objects.all()
    for a in aluno:
        atualizar_estado_aluno(a)
        
    anos_disponiveis = AnoLectivo.objects.all().order_by('-ano')
     
    ano_letivo = request.GET.get("ano_lectivo")

    if not ano_letivo:
        ano_letivo = AnoLectivo.objects.filter(estado='Aberto').last()

    query = request.GET.get('q', '')
    turmas = Turma.objects.all()
    disciplinas = Disciplina.objects.all()
    professores = Funcionario.objects.filter(funcao__icontains='professor').all()
    # Base query
    reconfirmacoes = Reconfirmacao.objects.select_related(
        'aluno', 'turma', 'sala', 'classe', 'curso'
    ).filter(ano_letivo=ano_letivo).order_by('aluno__nome_completo') 

    # Filtro de pesquisa
    if query:
        reconfirmacoes = reconfirmacoes.filter(
            Q(aluno__nome_completo__icontains=query) |
            Q(aluno__numero_mecanografico__icontains=query) | 
            Q(turma__nome__icontains=query)
        )

    perfil = request.user.perfil

    if perfil == 'professor':
        funcionario = Funcionario.objects.filter(usuario=request.user).first()
        print("Usuário logado:", request.user)
        print("ID:", request.user.id)
        print("Perfil:", request.user.perfil)

        funcionario = Funcionario.objects.filter(usuario=request.user).first()
        print("Funcionario encontrado:", funcionario)

        if funcionario:
            turmas_vinculadas = ProfessorVinculo.objects.filter(
                professor=funcionario
            ).values_list('turma_id', flat=True).distinct()

            reconfirmacoes = reconfirmacoes.filter(turma_id__in=turmas_vinculadas)
            turmas_vinculadas = ProfessorVinculo.objects.filter(professor=funcionario)
            
        else:
            reconfirmacoes = reconfirmacoes.none()

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
        'disciplinas':disciplinas,
        'professores':professores,
        'anos_disponiveis':anos_disponiveis
    }

    # Renderizar conforme perfil
    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/alunos.html', context)
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/alunos.html', context)
    elif perfil == 'professor':
        return render(request, 'pedagogico/professor/alunos.html', context)
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
    for ano, disciplinas_do_ano  in medias.items():
        for nome, dados in disciplinas_do_ano.items():
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

    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/aluno-detalhe.html', {
            'aluno': aluno,
            'ultima_reconfirmacao': ultima_reconfirmacao,
            'medias': medias,
            'disciplinas': disciplinas,
            'disc':disc,
            'usuario':usuario
        })
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/aluno-detalhe.html', {
            'aluno': aluno,
            'ultima_reconfirmacao': ultima_reconfirmacao,
            'medias': medias,
            'disciplinas': disciplinas,
            'disc':disc,
            'usuario':usuario
        })
    elif perfil == 'diretor_geral':
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
    elif perfil == 'professor':
        disciplinas_vinculadas = []
        
        professor = getattr(request.user, 'funcionario', None)
        if professor:
            disciplinas_vinculadas = ProfessorVinculo.objects.filter(
                professor=professor
            ).select_related('disciplina', 'turma') 

        nomes_disciplinas_vinculadas = set(
            vinculo.disciplina.nome for vinculo in disciplinas_vinculadas
        )

        # Filtra o dicionário de disciplinas para conter só as do professor
        disciplinas_filtradas = [
            d for d in disciplinas
            if d.nome in nomes_disciplinas_vinculadas
        ]

        usuario = request.user
        
        return render(request, 'pedagogico/professor/aluno-detalhe.html', {
            'aluno': aluno,
            'ultima_reconfirmacao': ultima_reconfirmacao,
            'medias': medias,
            'disciplinas': disciplinas_filtradas, 
            'disciplinas_vinculadas': disciplinas_vinculadas,
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
def pautas(request):
    perfil = request.user.perfil
    usuario = request.user

    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/pautas.html', {'usuario':usuario})
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/pautas.html', {'usuario':usuario})
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

    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/pautas_trimestre.html', {
            'turmas_agrupadas': turmas_agrupadas,
            'search_query': query,
            'trimestre': trimestre,
            'texto': texto,
            'usuario': usuario
        })
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/pautas_trimestre.html', {
            'turmas_agrupadas': turmas_agrupadas,
            'search_query': query,
            'trimestre': trimestre,
            'texto': texto,
            'usuario': usuario
        })
    elif perfil == 'professor':
        usuario = request.user
        funcionario = Funcionario.objects.filter(usuario=usuario).first()
        
        if not funcionario:
            messages.error(request, "O seu usuário não está vinculado a um funcionário. Contacte o administrador.")
            return redirect('pedagogico:coordenacoes')

        coordenacoes = Coordenacao.objects.filter(funcionario=funcionario)

        if not coordenacoes:
            messages.error(request, "O seu usuário não está vinculado a uma Coordenação. Contacte a área pedagógica.")
            return redirect('pedagogico:coordenacoes')

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

        turmas_agrupadas_prof = {}

        for r in reconfirmacoes.order_by('classe__numero', 'turma__nome'):
            key = f"{r.classe.numero}ª Classe - Turma: {r.turma.nome} - Sala: {r.sala.nome if r.sala else '---'} - Curso: {r.curso.nome if r.curso else '---'} - Turno: {r.turno}"
            
            if key not in turmas_agrupadas_prof:
                turmas_agrupadas_prof[key] = {
                    'alunos': [],
                    'disciplinas_turma': set()
                }

            aluno = r.aluno
            classe_numero = r.classe.numero
            
            # Buscar notas do aluno com filtro de disciplinas se aplicável
            notas_query = Nota.objects.filter(
                aluno=aluno,
                trimestre=trimestre
            )
            
            if disciplinas_filtradas:
                notas_query = notas_query.filter(disciplina__in=disciplinas_filtradas)
            
            notas_aluno = notas_query.select_related('disciplina')
            
            linha = {
                'aluno': aluno.nome_completo,
                'disciplinas': {},
                'estado': 'Aprovado'
            }
            
            tem_todas_notas = True
            
            for nota in notas_aluno:
                disciplina = nota.disciplina
                valor_nota = nota.valor
                
                # Adicionar disciplina ao set da turma
                turmas_agrupadas_prof[key]['disciplinas_turma'].add(disciplina)
                
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
            
            turmas_agrupadas_prof[key]['alunos'].append(linha)
        
        # Processar dados finais para o professor
        for key, dados_turma in turmas_agrupadas_prof.items():
            disciplinas_ordenadas = sorted(
                list(dados_turma['disciplinas_turma']),
                key=lambda x: x.nome
            )
            turmas_agrupadas_prof[key]['disciplinas_ordenadas'] = disciplinas_ordenadas
            
            alunos_final = []
            for aluno_data in dados_turma['alunos']:
                aluno_final = {
                    'aluno': aluno_data['aluno'],
                    'estado': aluno_data['estado'],
                    'notas_por_disciplina': {}
                }
                
                for disciplina in disciplinas_ordenadas:
                    nota_disciplina = aluno_data['disciplinas'].get(disciplina.id, {'valor': None})
                    aluno_final['notas_por_disciplina'][disciplina.id] = nota_disciplina['valor']
                
                alunos_final.append(aluno_final)
            
            turmas_agrupadas_prof[key]['alunos_final'] = alunos_final

        return render(request, 'pedagogico/professor/pautas_trimestre.html', {
            'turmas_agrupadas': turmas_agrupadas_prof,
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

    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/pautas_finais.html', {
            'turmas_agrupadas': turmas_final,
            'usuario': usuario
        })
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/pautas_finais.html', {
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
def upload_foto_aluno(request, id):
    aluno = get_object_or_404(Aluno, pk=id)

    if request.method == 'POST' and request.FILES.get('foto'):
        aluno.foto = request.FILES['foto']
        aluno.save()
        messages.success(request, 'Foto atualizada com sucesso.')
    else:
        messages.error(request, 'Nenhuma imagem foi enviada.')

    return redirect('pedagogico:aluno_detalhes', id=aluno.id)

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
        ano_lectivo = AnoLectivo.objects.filter(estado='Aberto').last()

        # validação de valor
        if not valor:
            messages.error(request, "O campo valor é obrigatório.")
            return redirect('pedagogico:aluno_detalhes', aluno_id)

        try:
            valor = float(valor)
        except ValueError:
            messages.error(request, "O valor deve ser numérico.")
            return redirect('pedagogico:aluno_detalhes', aluno_id)

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

    return redirect('pedagogico:aluno_detalhes', aluno_id)

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

    if perfil == 'professor':
        professor = Funcionario.objects.filter(usuario=request.user).first()
        if not professor:
            return render(request, 'pedagogico/professor/coordenacoes.html', contexto)

        # Buscar as coordenações do professor filtrando por tipo
        coord_turmas = Coordenacao.objects.filter(funcionario=professor, tipo='turma')
        coord_disciplinas = Coordenacao.objects.filter(funcionario=professor, tipo='disciplina')

        turmas_agrupadas = {}
        for coord in coord_turmas:
            if coord.turma:  # garantir que tem turma vinculada
                turmas_agrupadas[coord.turma.nome] = montar_pauta_por_turma(coord.turma)

        disciplinas_agrupadas = {}
        for coord in coord_disciplinas:
            
            turmas = []
            if coord.turma:
                turmas = [coord.turma]
            else:
                # Pega turmas que o professor tem vínculo para essa disciplina
                turmas = Turma.objects.filter(professorvinculo__professor=professor, professorvinculo__disciplina=coord.disciplina).distinct()

            disciplinas_agrupadas[coord.disciplina.nome] = montar_pauta_por_disciplina(coord.disciplina, turmas)
        usuario = request.user
        contexto.update({
            'turmas_agrupadas': turmas_agrupadas,
            'disciplinas_agrupadas': disciplinas_agrupadas,
            'trimestre': trimestre,
            'usuario':usuario
        })

        return render(request, 'pedagogico/professor/coordenacoes.html', contexto)
    

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
        'usuario':usuario
    })

    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/coordenacoes.html', contexto)
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/coordenacoes.html', contexto)
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
    return redirect('pedagogico:coordenacoes')


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
        return redirect('pedagogico:coordenacoes')

    return redirect('pedagogico:coordenacoes')

@login_required
def eliminar_coordenacao(request, pk):
    coord = get_object_or_404(Coordenacao, pk=pk)
    if request.method == 'POST':
        coord.delete()
        messages.success(request, "Coordenação eliminada com sucesso.")
    return redirect('pedagogico:coordenacoes')

def logout_view(request):
    logout(request)
    return redirect('core:login') 

def monografias(request):
    perfil = request.user.perfil   
    usuario = request.user
    
    # Obter todas as monografias
    monografias_list = Monografia.objects.all().order_by('-data_submissao')
    
    # Filtros via GET
    estado = request.GET.get('estado')
    ano = request.GET.get('ano')
    curso = request.GET.get('curso')
    search = request.GET.get('search')
    
    if estado:
        monografias_list = monografias_list.filter(estado=estado)
    if ano:
        monografias_list = monografias_list.filter(ano_academico=ano)
    if curso:
        monografias_list = monografias_list.filter(autor_curso__icontains=curso)
    if search:
        monografias_list = monografias_list.filter(
            models.Q(titulo__icontains=search) |
            models.Q(autor__icontains=search) |
            models.Q(orientador__icontains=search)
        )
    
    # Paginação
    paginator = Paginator(monografias_list, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    monografias_page = paginator.get_page(page_number)
    
    # Estatísticas
    total_monografias = Monografia.objects.count()
    pendentes_avaliacao = Monografia.objects.filter(estado='avaliacao').count()
    monografias_aprovadas = Monografia.objects.filter(estado='aprovado').count()
    necessitam_correcao = Monografia.objects.filter(estado='reprovado').count()
    
    contexto = {
        'monografias': monografias_page,
        'total_monografias': total_monografias, 
        'pendentes_avaliacao': pendentes_avaliacao,
        'monografias_aprovadas': monografias_aprovadas,
        'necessitam_correcao': necessitam_correcao,
        'usuario': usuario,
        'anos': AnoLectivo.objects.all()
    }
     
    if perfil == 'diretor_geral':
        return render(request, 'core/monografias.html', contexto)
    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/monografias.html', contexto)
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/monografias.html', contexto)
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
def salvar_monografia(request):
    if request.method != "POST":
        return JsonResponse({"erro": "Método inválido"}, status=405)

    try:
        titulo = request.POST.get("titulo")

        # Verificar duplicidade
        if Monografia.objects.filter(titulo__iexact=titulo).exists():
            return JsonResponse({
                "status": "erro",
                "erro": "Já existe uma monografia com este tema."
            }, status=400)

        monografia = Monografia.objects.create(
            titulo=titulo,
            autor=request.POST.get("autor"),
            autor_email=request.POST.get("autor_email"),
            autor_telefone=request.POST.get("autor_telefone"),
            autor_curso=request.POST.get("autor_curso"),
            orientador=request.POST.get("orientador"),
            orientador_telefone=request.POST.get("orientador_telefone"),
            ano_academico=request.POST.get("ano_academico"),
            resumo=request.POST.get("resumo"),
            arquivo=request.FILES.get("arquivo"),
        )

        return JsonResponse({"status": "ok", "id": monografia.id})

    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=500)

def avaliacoes(request):
    perfil = request.user.tipo_usuario
    usuario = request.user
    
    # Filtros
    estado_filter = request.GET.get('estado', '')
    avaliador_filter = request.GET.get('avaliador', '')
    
    # Obter avaliações
    avaliacoes_list = Avaliacao.objects.select_related('monografia').all()
    
    if estado_filter:
        avaliacoes_list = avaliacoes_list.filter(estado=estado_filter)
    
    if avaliador_filter:
        avaliacoes_list = avaliacoes_list.filter(avaliador__icontains=avaliador_filter)
    
    # Paginação
    paginator = Paginator(avaliacoes_list, 15)
    page_number = request.GET.get('page')
    avaliacoes_page = paginator.get_page(page_number)
    
    # Estatísticas
    total_avaliacoes = Avaliacao.objects.count()
    avaliacoes_pendentes = Avaliacao.objects.filter(estado='pendente').count()
    avaliacoes_concluidas = Avaliacao.objects.filter(estado='concluida').count()
    avaliacoes_atrasadas = Avaliacao.objects.filter(estado='pendente').count()  # Simplificado
    
    # Média de notas
    media_notas = Avaliacao.objects.filter(nota__isnull=False).aggregate(
        avg_nota=Avg('nota')
    )['avg_nota'] or 0
    
    contexto = {
        'avaliacoes': avaliacoes_page,
        'total_avaliacoes': total_avaliacoes,
        'avaliacoes_pendentes': avaliacoes_pendentes,
        'avaliacoes_concluidas': avaliacoes_concluidas,
        'avaliacoes_atrasadas': avaliacoes_atrasadas,
        'media_notas': round(media_notas, 2),
        'estados': Avaliacao.ESTADO_AVALIACAO,
        'user': request.user,
        'filtro_estado': estado_filter,
        'filtro_avaliador': avaliador_filter,
    }
    
    if perfil == 'director_geral':
        return render(request, 'core/director_geral/avaliacoes.html', contexto)
    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/avaliacoes.html', contexto)
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/avaliacoes.html', contexto)
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

def editar_monografia(request, monografia_id):
    monografia = get_object_or_404(Monografia, id=monografia_id)

    data = {
        "id": monografia.id,
        "titulo": monografia.titulo,
        "autor": monografia.autor,
        "autor_email": monografia.autor_email,
        "autor_telefone": monografia.autor_telefone,
        "autor_curso": monografia.autor_curso,
        "orientador": monografia.orientador, 
        "orientador_telefone": monografia.orientador_telefone or "",  
        "ano_academico": monografia.ano_academico, 
        "resumo": monografia.resumo or "",
        "estado": monografia.estado,  
        "nota_final": str(monografia.nota_final) if monografia.nota_final else "",  
        "nome_arquivo": monografia.get_nome_arquivo() if hasattr(monografia, 'get_nome_arquivo') else "",
        "url_arquivo": monografia.arquivo.url if monografia.arquivo else "",
    }
    
    return JsonResponse(data)

@csrf_exempt
def atualizar_monografia(request, monografia_id):
    if request.method != "POST":
        return JsonResponse({"erro": "Método inválido"}, status=400)

    try:
        monografia = get_object_or_404(Monografia, id=monografia_id)
        
        # Atualizar campos do formulário
        monografia.titulo = request.POST.get("titulo")
        monografia.autor = request.POST.get("autor")
        monografia.autor_email = request.POST.get("autor_email")
        monografia.autor_telefone = request.POST.get("autor_telefone")
        monografia.autor_curso = request.POST.get("autor_curso")
        monografia.orientador = request.POST.get("orientador")
        monografia.orientador_telefone = request.POST.get("orientador_telefone")
        monografia.ano_academico = request.POST.get("ano_academico")
        monografia.resumo = request.POST.get("resumo", "")
        
        # Estado e nota final (podem ser opcionais)
        estado = request.POST.get("estado")
        if estado in dict(Monografia._meta.get_field('estado').choices):
            monografia.estado = estado
        
        nota_final = request.POST.get("nota_final")
        if nota_final:
            try:
                monografia.nota_final = float(nota_final)
            except ValueError:
                pass

        # Atualizar arquivo se o usuário enviar outro
        if "arquivo" in request.FILES:
            arquivo = request.FILES["arquivo"]
            # Validar extensão
            import os
            extensao = os.path.splitext(arquivo.name)[1].lower()
            if extensao not in ['.pdf', '.doc', '.docx']:
                return JsonResponse({"erro": "Formato de arquivo inválido. Use PDF, DOC ou DOCX."}, status=400)
            
            # Validar tamanho (opcional, 10MB máximo)
            if arquivo.size > 10 * 1024 * 1024:
                return JsonResponse({"erro": "Arquivo muito grande. Máximo 10MB."}, status=400)
            
            monografia.arquivo = arquivo

        monografia.save()

        return JsonResponse({"status": "ok"})
    
    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=500)
    
@csrf_exempt
def excluir_monografia(request, monografia_id):
    """Versão simplificada para exclusão de monografia."""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
    
    # Buscar monografia
    monografia = get_object_or_404(Monografia, id=monografia_id)
    
    # Extrair senha dos dados
    senha = None
    
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            senha = data.get('senha')
        except:
            return JsonResponse({'error': 'Dados inválidos'}, status=400)
    else:
        senha = request.POST.get('senha')
    
    if not senha:
        return JsonResponse({'error': 'Senha não fornecida'}, status=400)
    
    # Verificar senha
    user = authenticate(username=request.user.username, password=senha)
    if not user:
        return JsonResponse({'error': 'Senha incorreta'}, status=400)
    
    # Excluir
    try:
        titulo = monografia.titulo
        monografia.delete()
        return JsonResponse({
            'status': 'success',
            'message': f'Monografia "{titulo}" excluída!'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def detalhe_monografia(request, monografia_id):
    # Obter a monografia ou retornar 404
    monografia = get_object_or_404(Monografia, id=monografia_id)
    
    # Verificar perfil do usuário
    perfil = request.user.perfil   
    usuario = request.user
    
    # Contexto com os dados da monografia
    contexto = {
        'monografia': monografia,
        'usuario': usuario,
        'perfil': perfil,
    }
    
    # Renderizar template baseado no perfil
    if perfil == 'diretor_geral':
        return render(request, 'core/detalhes-monografia.html', contexto)
    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/detalhes-monografia.html', contexto)
    elif perfil == 'secretario_ped':
        return render(request, 'pedagogico/secretario_ped/detalhes-monografia.html', contexto)
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
def submeter_avaliacao(request, monografia_id):
    if request.method == 'POST':
        monografia = get_object_or_404(Monografia, id=monografia_id)
        
        try:
            # Criar nova avaliação com os campos do modelo atual
            avaliacao = Avaliacao.objects.create(
                monografia=monografia,
                avaliador=request.POST.get('avaliador'),
                nota=request.POST.get('nota') if request.POST.get('nota') else None,
                recomendacao=request.POST.get('recomendacao'),
                parecer=request.POST.get('parecer', ''),
                
                # Campos do modelo atual
                data_atribuicao=timezone.now(),
                data_conclusao=timezone.now(),  # Preenche com a data atual
                estado='concluida'  # Usando o estado do modelo
            )
            
            messages.success(request, 'Avaliação submetida com sucesso!')
            
            # Atualizar estado da monografia
            if monografia.estado == 'submetido':
                monografia.estado = 'avaliacao'
                
            # Se tiver uma nota, atualizar a nota final
            if avaliacao.nota:
                avaliacoes_concluidas = monografia.avaliacoes.filter(estado='concluida')
                notas_validas = [av.nota for av in avaliacoes_concluidas if av.nota is not None]
                if notas_validas:
                    monografia.nota_final = sum(notas_validas) / len(notas_validas)
            
            monografia.save()
            
        except Exception as e:
            messages.error(request, f'Erro ao submeter avaliação: {str(e)}')
            return redirect('pedagogico:detalhe_monografia', monografia_id=monografia_id)
        
        return redirect('pedagogico:detalhe_monografia', monografia_id=monografia_id)
    
    return redirect('pedagogico:monografias')

@login_required
def relatorio_pedagogico(request):
    """
    View para gerar o relatório pedagógico completo
    """
    # Obter ano letivo selecionado (padrão: ano atual)
    ano_lectivo = request.GET.get("ano_lectivo")
    
    # Lista de anos letivos disponíveis
    anos_lectivos = AnoLectivo.objects.all().values_list('ano', flat=True)
    if not ano_lectivo:
        ano_lectivo = AnoLectivo.objects.filter(estado='Aberto').last()
    
    # ============ ESTATÍSTICAS GERAIS ============
    
    # Totais gerais
    total_alunos = Aluno.objects.count()
    total_professores = Funcionario.objects.filter(funcao__icontains='professor').count()
    total_funcionarios = Funcionario.objects.count()
    total_turmas = Turma.objects.filter(ano_letivo=ano_lectivo).count()
    total_disciplinas = Disciplina.objects.count()
    
    # Alunos por gênero
    alunos_masculino = Aluno.objects.filter(genero='M').count()
    alunos_feminino = Aluno.objects.filter(genero='F').count()
    
    # Professores por gênero
    professores_masculino = Funcionario.objects.filter(
        funcao__icontains='professor', genero='M'
    ).count()
    professores_feminino = Funcionario.objects.filter(
        funcao__icontains='professor', genero='F'
    ).count()
    
    # ============ DADOS DE MATRÍCULAS ============
    
    # Alunos por turma (para o ano letivo selecionado)
    alunos_por_turma = Turma.objects.filter(ano_letivo=ano_lectivo).annotate(
        quantidade_alunos=Count('aluno')
    ).order_by('-quantidade_alunos')
    
    total_alunos_ano = Aluno.objects.filter(turma__ano_letivo=ano_lectivo).count()
    
   # Alunos por classe
    alunos_por_classe = []
    classes = Classe.objects.all().order_by('numero')

    # Preparar dados para os gráficos
    labels_classes = []  # Para o gráfico (números das classes)
    dados_classes = []   # Para o gráfico (quantidades)

    for classe in classes:
        quantidade = Aluno.objects.filter(
            turma__ano_letivo=ano_lectivo,
            turma__classe=classe
        ).count()
        
        if quantidade > 0:
            percentual = (quantidade / total_alunos_ano * 100) if total_alunos_ano > 0 else 0
            alunos_por_classe.append({
                'classe': classe,
                'classe_numero': classe.numero,  # Adicionar o número separadamente
                'classe_designacao': classe.designacao,
                'quantidade': quantidade,
                'percentual': percentual
            })
            
            # Adicionar aos dados do gráfico
            labels_classes.append(f"{classe.numero}ª")  # Formato: "10ª", "11ª", etc.
            dados_classes.append(quantidade)

    # Se não houver dados, criar listas vazias
    if not labels_classes:
        labels_classes = []
        dados_classes = []
    
    # Alunos por turno
    alunos_por_turno = []
    for turno in ['Manhã', 'Tarde', 'Noite']:
        quantidade = Aluno.objects.filter(
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
    cursos = Curso.objects.all()
    for curso in cursos:
        quantidade = Aluno.objects.filter(
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
    disciplinas = Disciplina.objects.all()[:10]  # Top 10 disciplinas
    
    for disciplina in disciplinas:
        notas = Nota.objects.filter(
            disciplina=disciplina,
            ano_lectivo__ano=ano_lectivo,
            trimestre__in=[1, 2, 3]  # Apenas trimestres, não exame
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
            turma__ano_letivo=ano_lectivo,
            turma__classe=classe
        )
        
        if alunos_classe.exists():
            # Calcular média geral da classe (baseado nas notas de todas disciplinas)
            notas_classe = Nota.objects.filter(
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
        turma__ano_letivo=ano_lectivo
    ).values(
        'disciplina__nome', 'disciplina__id'
    ).annotate(
        quantidade=Count('professor', distinct=True),
        turmas=Count('turma', distinct=True)
    ).order_by('-quantidade')
    
    # Média de alunos por professor
    total_vinculos = ProfessorVinculo.objects.filter(turma__ano_letivo=ano_lectivo).count()
    media_alunos_professor = total_alunos_ano / total_vinculos if total_vinculos > 0 else 0
    
    # Coordenações
    coordenacoes_por_tipo = Coordenacao.objects.values('tipo').annotate(
        quantidade=Count('id')
    )
    
    # ============ DADOS DE MONOGRAFIAS ============
    
    # Monografias por estado
    monografias_estado = Monografia.objects.values('estado').annotate(
        quantidade=Count('id')
    )
    
    total_monografias = Monografia.objects.count()
    
    # Média de notas das monografias
    media_notas_monografias = Avaliacao.objects.filter(
        nota__isnull=False
    ).aggregate(Avg('nota'))['nota__avg'] or 0
    
    # ============ DADOS PARA GRÁFICOS ============
    
    # Dados para gráfico de evolução de matrículas (últimos 5 anos)
    anos_evolucao = ['2025-2026', '2026-2027', '2027-2028', '2028-2029', '2029-2030']
    matriculas_evolucao = []
    
    for ano in anos_evolucao:
        quantidade = Aluno.objects.filter(turma__ano_letivo=ano).count()
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
    ultimas_notas = Nota.objects.select_related(
        'aluno', 'disciplina', 'ano_lectivo'
    ).order_by('-id')[:10]
    
    # Últimos alunos matriculados
    ultimos_alunos = Aluno.objects.select_related(
        'turma', 'classe', 'curso'
    ).order_by('-id')[:10]
    
    # Últimas monografias submetidas
    ultimas_monografias = Monografia.objects.order_by('-data_submissao')[:5]
    perfil = request.user.perfil
    usuario = request.user
    
    context = {
        # Filtros
        'ano_lectivo': ano_lectivo,
        'anos_lectivos_disponiveis': anos_lectivos,
        'usuario':usuario,
        
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
    }

    if perfil == 'diretor_pedagogico':
        return render(request, 'pedagogico/diretor_pedagogico/relatorio-pedagogico.html', context)
    elif perfil == 'diretor_geral':
        return render(request, 'core/relatorio-pedagogico.html', context)
