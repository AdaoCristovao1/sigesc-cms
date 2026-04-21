from pyexpat.errors import messages
from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from administracao.models import *
from pedagogico.models import *
from django.http import HttpResponse, JsonResponse # type: ignore
from decimal import Decimal, ROUND_HALF_UP
from financeiro.models import *
from django.db.models import Avg, Count, Q
from decimal import Decimal
import json

@login_required
def aluno_home(request):
    
    perfil = request.user.perfil
    usuario = request.user
    aluno = Aluno.objects.get(usuario=usuario)

    return render(request, 'estudante/aluno-home.html', {"usuario":usuario, "aluno": aluno})

@login_required
def alunos_geral(request):
    query = request.GET.get('q', '').strip()
    
    alunos = Aluno.objects.select_related('usuario', 'turma', 'classe', 'curso', 'sala')

    if query:
        alunos = alunos.filter(
            Q(nome_completo__icontains=query) |
            Q(bi__icontains=query) |
            Q(numero_mecanografico__icontains=query)
        )
    
    alunos = alunos.order_by('nome_completo')

    classes = Classe.objects.all()
    turmas = Turma.objects.select_related('classe', 'curso', 'sala')

    # JSON para o JS
    import json
    from django.core.serializers.json import DjangoJSONEncoder

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
    perfil = request.user.perfil  
    usuario = request.user 
     
    if perfil == 'diretor_geral':
        return render(request, 'estudante/alunos-dg.html', {
            'alunos': alunos,
            'classes': classes,
            'turmas': turmas,
            'turmas_json': turmas_json,
            'search_query': query,
            'usuario':usuario
        })
    if perfil == 'diretor_pedagogico':
        return render(request, 'estudante/alunos-dp.html', {
            'alunos': alunos,
            'classes': classes,
            'turmas': turmas,
            'turmas_json': turmas_json,
            'search_query': query,
            'usuario':usuario
        })
    
    elif perfil == 'secretario_ped':
        return render(request, 'estudante/alunos-sec.html', {
            'alunos': alunos,
            'classes': classes,
            'turmas': turmas,
            'turmas_json': turmas_json,
            'search_query': query,
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
def meus_professores(request):
    usuario = request.user
    
    # Obter o aluno logado
    aluno = Aluno.objects.filter(usuario=usuario).first()
    if not aluno:
        messages.error(request, "Nenhum aluno associado a este usuário.")
        return redirect("estudante:aluno_home")

    # Buscar a turma activa via Reconfirmacao
    reconf = Reconfirmacao.objects.filter(aluno=aluno).last()

    if not reconf:
        messages.error(request, "Nenhuma reconfirmação/turma encontrada para este aluno.")
        return redirect("estudante:aluno_home")

    turma = reconf.turma

    # Buscar os professores ligados à mesma turma
    professores = ProfessorVinculo.objects.filter(turma=turma).select_related(
        "professor", "disciplina"
    )

    return render(
        request,
        "estudante/meus-professores.html",
        {
            "usuario": usuario,
            "aluno": aluno,
            "turma": turma,
            "professores": professores,
        }
    )

@login_required
def historico_academico(request):
    usuario = request.user

    # Obter aluno logado
    aluno = get_object_or_404(Aluno, usuario=usuario)

    # Todas as notas do aluno
    notas = Nota.objects.filter(aluno=aluno).select_related(
        'disciplina', 'classe'
    ).order_by('classe__numero', 'disciplina__nome', 'trimestre')

    
    medias = {} 

    for nota in notas:
        ano = nota.classe.numero  
        disciplina = nota.disciplina.nome
        trimestre = nota.trimestre
        valor = nota.valor

        if ano not in medias:
            medias[ano] = {}

        if disciplina not in medias[ano]:
            medias[ano][disciplina] = {"notas": {}, "media": "--"}

        medias[ano][disciplina]["notas"][trimestre] = valor

    # Calcular médias por disciplina
    for ano, disciplinas in medias.items():
        for nome, dados in disciplinas.items():
            notes = dados["notas"]

            t1 = notes.get(1)
            t2 = notes.get(2)
            t3 = notes.get(3)
            exame = notes.get(4)

            if t1 and t2 and t3 and exame:
                # Média ponderada exemplo — ajuste conforme regra da tua escola
                media = ((t1 + t2 + t3) / 3 * Decimal("0.4")) + (exame * Decimal("0.6"))
                media = Decimal(media).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
                dados["media"] = float(media)

    return render(
        request,
        "estudante/historico-academico.html",
        {"usuario": usuario, "aluno": aluno, "historico": medias}
    )

@login_required
def historico_financeiro(request):
    usuario = request.user
    aluno = usuario.aluno  # Assumindo relação OneToOne entre User e Aluno

    # Buscar todos os pagamentos do aluno
    pagamentos = Pagamento.objects.filter(aluno=aluno).order_by("ano_lectivo", "data_pagamento")

    # Agrupar por ano lectivo
    historico = {}
    for p in pagamentos:
        ano = p.ano_lectivo  # <-- já é string, não precisa de .ano
        if ano not in historico:
            historico[ano] = []
        historico[ano].append(p)

    context = {
        "usuario": usuario,
        "historico": historico,
    }
    return render(request, "estudante/historico-financeiro.html", context)

@login_required
def recados(request):
    usuario = request.user
    aluno = usuario.aluno
    return render(request, 'estudante/recados.html', {
        "usuario": usuario,
    })

@login_required
def aproveitamento_escolar(request):
    usuario = request.user
    aluno = usuario.aluno
    
    # Buscar anos letivos disponíveis
    anos_letivos = AnoLectivo.objects.all().order_by('-ano')
    
    # Buscar disciplinas do aluno
    disciplinas = Disciplina.objects.filter(
        nota__aluno=aluno
    ).distinct()
    
    # Buscar classes do aluno
    classes = Classe.objects.filter(
        nota__aluno=aluno
    ).distinct()
    
    # Dados para o template
    context = {
        "usuario": usuario,
        "anos_letivos": anos_letivos,
        "disciplinas": disciplinas,
        "classes": classes,
    }
    
    return render(request, 'estudante/aproveitamento-escolar.html', context)

@login_required
def dados_aproveitamento(request):
    if request.method == 'GET':
        usuario = request.user
        aluno = usuario.aluno
        
        # Parâmetros de filtro
        ano_id = request.GET.get('ano')
        trimestre = request.GET.get('trimestre')
        disciplina_id = request.GET.get('disciplina')
        classe_id = request.GET.get('classe')
        
        # Query base
        notas_query = Nota.objects.filter(aluno=aluno)
        
        # Aplicar filtros
        if ano_id and ano_id != 'all':
            notas_query = notas_query.filter(ano_lectivo_id=ano_id)
        
        if trimestre and trimestre != 'all':
            notas_query = notas_query.filter(trimestre=trimestre)
        
        if disciplina_id and disciplina_id != 'all':
            notas_query = notas_query.filter(disciplina_id=disciplina_id)
        
        if classe_id and classe_id != 'all':
            notas_query = notas_query.filter(classe_id=classe_id)
        
        # Estatísticas gerais
        media_geral = notas_query.aggregate(media=Avg('valor'))['media'] or 0
        if media_geral:
            media_geral = round(media_geral, 2)
        
        # Taxa de aprovação (considerando média >= 10)
        total_notas = notas_query.count()
        notas_aprovadas = notas_query.filter(valor__gte=10).count()
        taxa_aprovacao = round((notas_aprovadas / total_notas * 100), 2) if total_notas > 0 else 0
        
        # Melhor disciplina
        melhor_disciplina_query = notas_query.values('disciplina__nome').annotate(
            media=Avg('valor')
        ).order_by('-media').first()
        
        melhor_disciplina = melhor_disciplina_query['disciplina__nome'] if melhor_disciplina_query else "N/A"
        
        # Dados para gráfico de desempenho por disciplina
        desempenho_disciplinas = notas_query.values('disciplina__nome').annotate(
            media=Avg('valor')
        ).order_by('disciplina__nome')
        
        labels_disciplinas = [item['disciplina__nome'] for item in desempenho_disciplinas]
        valores_disciplinas = [float(item['media']) for item in desempenho_disciplinas]
        
        # Dados para gráfico de evolução por trimestre
        evolucao_trimestral = notas_query.values('trimestre').annotate(
            media=Avg('valor')
        ).order_by('trimestre')
        
        labels_trimestres = [f"T{item['trimestre']}" for item in evolucao_trimestral]
        valores_trimestres = [float(item['media']) for item in evolucao_trimestral]
        
        # Dados para gráfico de distribuição de notas
        distribuicao_notas = {
            '0-4': notas_query.filter(valor__range=(0, 4.99)).count(),
            '5-9': notas_query.filter(valor__range=(5, 9.99)).count(),
            '10-13': notas_query.filter(valor__range=(10, 13.99)).count(),
            '14-17': notas_query.filter(valor__range=(14, 17.99)).count(),
            '18-20': notas_query.filter(valor__range=(18, 20)).count(),
        }
        
        # Tabela de notas detalhadas
        notas_detalhadas = notas_query.select_related(
            'disciplina', 'ano_lectivo', 'classe'
        ).order_by('disciplina__nome', 'trimestre')
        
        tabela_notas = []
        for nota in notas_detalhadas:

            # REGRA DE APROVAÇÃO
            # Se classe > 6 → média mínima = 10
            # Se classe <= 6 → média mínima = 5
            limite_aprovacao = 10 if nota.classe.numero > 6 else 5

            tabela_notas.append({
                'disciplina': nota.disciplina.nome,
                'trimestre': nota.get_trimestre_display(),
                'nota': float(nota.valor),
                'ano_letivo': nota.ano_lectivo.ano,
                'classe': nota.classe.numero,
                'status': 'Aprovado' if nota.valor >= limite_aprovacao else 'Reprovado'
            })
        
        return JsonResponse({
            'media_geral': media_geral,
            'taxa_aprovacao': taxa_aprovacao,
            'melhor_disciplina': melhor_disciplina,
            'desempenho_disciplinas': {
                'labels': labels_disciplinas,
                'valores': valores_disciplinas
            },
            'evolucao_trimestral': {
                'labels': labels_trimestres,
                'valores': valores_trimestres
            },
            'distribuicao_notas': distribuicao_notas,
            'tabela_notas': tabela_notas
        })
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

@login_required
def pagamentos(request):
    usuario = request.user
    aluno = usuario.aluno
    # Dados para o template
    context = {
        "usuario": usuario,
    }
    return render(request, 'estudante/pagamentos.html', context)
