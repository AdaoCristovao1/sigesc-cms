from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.decorators import login_required
from datetime import datetime
import uuid
from administracao.models import *
from .models import *
from administracao.models import AnoLectivo
from django.utils import timezone
from datetime import date
from django.utils.timezone import now
from django.db.models import Sum, Count, F, DecimalField, Q
import calendar 
import logging 
import locale
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPM
from reportlab.graphics.barcode import createBarcodeDrawing
import io
import base64
from django.http import HttpResponse
from django.db.models.functions import ExtractMonth 
from decimal import Decimal
from django.http import JsonResponse
from django.db.models.functions import ExtractMonth
import calendar
from datetime import datetime
from django.template.loader import render_to_string

@login_required
def financas(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
    query = request.GET.get('q', '').strip()

    aluno = None
    historico = []

    if query:
        # Busca por nome, número mecanográfico ou BI (insensível a maiúsculas/minúsculas)
        aluno = Aluno.objects.select_related('usuario', 'turma', 'classe', 'curso', 'sala') \
            .filter(
                escola=escola_usuario 
            ).filter(
                Q(nome_completo__icontains=query) |
                Q(numero_mecanografico__icontains=query) |
                Q(bi__icontains=query)
            ).first()

        if aluno:
            historico = Pagamento.objects.filter(aluno=aluno, ano_lectivo=ano_letivo, escola=escola_usuario).order_by('-data_pagamento')
        else:
            messages.error(request, "Aluno não encontrado.")

    # Registrar pagamento
    if request.method == 'POST':
        aluno_id = request.POST.get('aluno_id')
        tipo_id = request.POST.get('tipo_pagamento')
        valor = request.POST.get('valor')

        aluno = Aluno.objects.filter(id=aluno_id, escola=escola_usuario).first()
        tipo_pagamento = TipoPagamento.objects.filter(id=tipo_id, escola=escola_usuario).first()

        if not aluno or not tipo_pagamento:
            messages.error(request, "Aluno ou tipo de pagamento inválido.")
            return redirect(request.path)

        try:
            valor_decimal = float(valor)
        except ValueError:
            messages.error(request, "Valor inválido!")
            return redirect(request.path)

        with transaction.atomic():
            pagamento = Pagamento.objects.create(
                escola=escola_usuario,
                aluno=aluno,
                tipo=tipo_pagamento,
                valor=valor_decimal,
                ano_lectivo=ano_letivo
            )

            Recibo.objects.create(
                escola=escola_usuario,
                pagamento=pagamento,
                codigo=f"REC-{uuid.uuid4().hex[:8].upper()}"
            )

        messages.success(request, f"Pagamento de {valor_decimal:.2f} Kz registrado com sucesso!")
        return redirect(f"{request.path}?q={aluno.nome_completo}")

    tipos_pagamento = TipoPagamento.objects.filter(escola=escola_usuario)
    perfil = request.user.perfil 
    usuario = request.user   

    if perfil == 'diretor_geral':
        return render(request, 'financeiro/diretor_geral/financas.html', {
            'search_query': query,
            'aluno': aluno,
            'historico': historico,
            'tipos_pagamento': tipos_pagamento, 
            "usuario":usuario,
            'escola':escola_usuario
        }) 
    elif perfil == 'diretor_admin':
        return render(request, 'financeiro/diretor_admin/financas.html', {
            'search_query': query,
            'aluno': aluno,
            'historico': historico,
            'tipos_pagamento': tipos_pagamento,
            "usuario":usuario,
            'escola':escola_usuario
        })
    elif perfil == 'secretario_admin':
        return render(request, 'financeiro/secretario_admin/financas.html', {
            'search_query': query,
            'aluno': aluno,
            'historico': historico,
            'tipos_pagamento': tipos_pagamento,
            "usuario":usuario,
            'escola':escola_usuario
        })
    elif perfil == 'secretario_geral':
        return render(request, 'financeiro/secretario_geral/financas.html', {
            'search_query': query,
            'aluno': aluno,
            'historico': historico,
            'tipos_pagamento': tipos_pagamento,
            "usuario":usuario,
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
def pagamento_servico(request, aluno_id, servico):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})
    
    aluno = get_object_or_404(Aluno, id=aluno_id, escola=escola_usuario)
    tipos_pagamento = TipoPagamento.objects.filter(escola=escola_usuario)
    hoje = date.today()

    if servico.lower() == 'propina':
        ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
        
        # Buscar todos os emolumentos que contenham "propina" no nome (case insensitive)
        emolumentos_propina = Emolumentos.objects.filter(nome__icontains='propina', escola=escola_usuario)
        
        if not emolumentos_propina.exists():
            messages.error(request, "Nenhum tipo de propina encontrado.")
            return redirect("financa:financas")
            
        # Se um emolumento específico foi selecionado via GET
        emolumento_id = request.GET.get('emolumento_id')
        if emolumento_id:
            emolumento_selecionado = get_object_or_404(Emolumentos, id=emolumento_id, escola=escola_usuario)
        else:
            # Seleciona o primeiro por padrão
            emolumento_selecionado = emolumentos_propina.first()

        meses = MesesPagar.objects.exclude(
            id__in=Pagamento.objects.filter( 
                escola=escola_usuario,
                aluno=aluno,
                tipoServico=emolumento_selecionado,
                ano_lectivo=ano_letivo
            ).values_list('mes_id', flat=True)
        ).order_by('numero')

        # Aplicar multa se necessário
        for mes in meses:
            mes.multa_valor = emolumento_selecionado.multas.filter(aplicar_multa=True).first().valor_multa if emolumento_selecionado.multas.exists() else 0

        perfil = request.user.perfil 
        usuario = request.user   
        if perfil == 'diretor_geral':
            return render(request, 'financeiro/diretor_geral/pagamento_servico.html', {
                'aluno': aluno,
                'servico': servico,
                'emolumento': emolumento_selecionado,
                'emolumentos_propina': emolumentos_propina,
                'meses': meses,
                'tipos_pagamento': tipos_pagamento,
                "usuario":usuario,
                'escola':escola_usuario
            })  
        elif perfil == 'diretor_admin':
            return render(request, 'financeiro/diretor_admin/pagamento_servico.html', {
                'aluno': aluno,
                'servico': servico,
                'emolumento': emolumento_selecionado,
                'emolumentos_propina': emolumentos_propina, 
                'meses': meses,
                'tipos_pagamento': tipos_pagamento,
                "usuario":usuario,
                'escola':escola_usuario
            })
        elif perfil == 'secretario_admin':
            return render(request, 'financeiro/secretario_admin/pagamento_servico.html', {
                'aluno': aluno,
                'servico': servico,
                'emolumento': emolumento_selecionado,
                'emolumentos_propina': emolumentos_propina,
                'meses': meses,
                'tipos_pagamento': tipos_pagamento,
                "usuario":usuario,
                'escola':escola_usuario
            })
        elif perfil == 'secretario_geral':
            return render(request, 'financeiro/secretario_geral/pagamento_servico.html', {
                'aluno': aluno,
                'servico': servico,
                'emolumento': emolumento_selecionado,
                'emolumentos_propina': emolumentos_propina,
                'meses': meses,
                'tipos_pagamento': tipos_pagamento,
                "usuario":usuario,
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

    else:
        ano_letivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
        if not ano_letivo:
            messages.error(request, "Nenhum ano letivo encontrado.")
            return redirect("financa:financas")

        # Serviços diferentes de "Propina"
        emolumentos = Emolumentos.objects.exclude(nome__icontains="propina").filter(escola=escola_usuario)

        # Serviços que o aluno já pagou no ano letivo atual
        pagos_ids = Pagamento.objects.filter(
            escola=escola_usuario,
            aluno=aluno,
            ano_lectivo=ano_letivo
        ).values_list("tipoServico_id", flat=True)

        emolumento_id = request.GET.get('emolumento_id')
        if emolumento_id:
            emolumento_selecionado = get_object_or_404(Emolumentos, id=emolumento_id, escola=escola_usuario)
        else:
            # Seleciona o primeiro por padrão
            emolumento_selecionado = emolumentos.first()

        meses = MesesPagar.objects.exclude(
            id__in=Pagamento.objects.filter( 
                escola=escola_usuario,
                aluno=aluno,
                tipoServico=emolumento_selecionado,
                ano_lectivo=ano_letivo,
                mes__isnull=False  # Só considerar pagamentos com mês associado
            ).values_list('mes_id', flat=True)
        ).order_by('numero') 

        # Verificar multa em cada emolumento
        emolumentos_com_multa = []
        for e in emolumentos:
            multa = e.multas.filter(aplicar_multa=True).first()
            if multa and hoje.day > multa.data_aplicacao:
                emolumentos_com_multa.append({ 
                    "emolumento": e,
                    "multa": multa.valor_multa,
                    "mensagem": f"Multa aplicada ({multa.valor_multa} Kz)"
                })

        perfil = request.user.perfil
        usuario = request.user
        contexto = {
            "aluno": aluno,
            "servico": servico,
            "emolumentos": emolumentos,
            'emolumento': emolumento_selecionado,
            "tipos_pagamento": tipos_pagamento,
            "emolumentos_com_multa": emolumentos_com_multa,
            'meses': meses,
            "usuario":usuario,
            'escola': escola_usuario
        }
        if perfil == 'diretor_geral':
           return render(request, "financeiro/diretor_geral/pagamento_servico.html", contexto)
        elif perfil == "diretor_admin":
            return render(request, "financeiro/diretor_admin/pagamento_servico.html", contexto)
        elif perfil == "secretario_admin":
            return render(request, "financeiro/secretario_admin/pagamento_servico.html", contexto)
        elif perfil == "secretario_geral":
            return render(request, "financeiro/secretario_geral/pagamento_servico.html", contexto)
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
def processar_pagamento_propina(request, aluno_id):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'}) 
    
    aluno = get_object_or_404(Aluno, id=aluno_id, escola=escola_usuario)
    tipos_pagamento = TipoPagamento.objects.all()

    if request.method == "POST":
        emolumento_id = request.POST.get("emolumento_id")
        emolumento = get_object_or_404(Emolumentos, id=emolumento_id, escola=escola_usuario)
    
        meses_selecionados = request.POST.getlist("meses")
        multas_selecionadas = request.POST.getlist("multas") 
        tipo_pagamento_id = request.POST.get("tipo_pagamento")
        tipo_pagamento = get_object_or_404(TipoPagamento, id=tipo_pagamento_id, escola=escola_usuario)

        ano_lectivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
        data_pagamento = timezone.now()

        meses_info = []
        total_pago = 0

        for mes_id in meses_selecionados:
            mes_obj = MesesPagar.objects.get(id=mes_id)

            multa_valor = 0
            if mes_id in multas_selecionadas:
                multa = emolumento.multas.filter(aplicar_multa=True).first()
                if multa:
                    multa_valor = multa.valor_multa

            valor_total_mes = emolumento.valor + multa_valor

            # Garantir que não seja duplicado
            pagamento, created = Pagamento.objects.get_or_create(
                escola=escola_usuario,
                aluno=aluno,
                tipo=tipo_pagamento,
                tipoServico=emolumento,
                mes=mes_obj,
                ano_lectivo=ano_lectivo,
                defaults={
                    "valor": valor_total_mes,
                    "data_pagamento": data_pagamento,
                }
            )

            if created:  # Só adiciona ao total se foi realmente criado
                total_pago += valor_total_mes
                meses_info.append({
                    "nome": mes_obj.nome,
                    "valor": emolumento.valor,
                    "multa": multa_valor,
                    "total": valor_total_mes,
                    "data_pagamento": data_pagamento,
                })
        
        # Número do recibo (sequência de pagamentos)
        recibo_numero = Pagamento.objects.filter(escola=escola_usuario).count()

        # Gerar código de barras
        barcode_value = str(recibo_numero)
        drawing = createBarcodeDrawing(
            'Code128',
            value=barcode_value,
            barHeight=40,
            barWidth=2.5,
            humanReadable=True
        )

        # Exportar para formato SVG em memória
        barcode_svg = drawing.asString('svg')

        barcode_base64 = base64.b64encode(barcode_svg.encode("utf-8")).decode("utf-8")

        context = {
            "aluno": aluno,
            "emolumento": emolumento,
            "meses_info": meses_info,
            "total_pago": total_pago,
            "tipo_pagamento": tipo_pagamento,
            "data_pagamento": data_pagamento,
            "atendente": request.user,
            "recibo": {"numero": recibo_numero},
            "barcode": barcode_base64,
            'escola': escola_usuario
        }
        return render(request, "financeiro/comprovativos/comprovativo_pagamento.html", context)

    # GET → redireciona para escolha do pagamento
    perfil = request.user.perfil
    usuario = request.user
    if perfil == 'diretor_geral':
        return render(request, "financeiro/diretor_geral/financas.html", {"usuario":usuario})
    elif perfil == "diretor_admin":
        return render(request, 'financeiro/diretor_admin/financas.html')
    elif perfil == "secretario_admin":
        return render(request, "financeiro/secretario_admin/financas.html")
    elif perfil == "secretario_geral":
        return render(request, "financeiro/secretario_geral/financas.html")
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
def processar_pagamento_servicos(request, aluno_id):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'}) 
    
    aluno = get_object_or_404(Aluno, id=aluno_id, escola=escola_usuario)
    tipos_pagamento = TipoPagamento.objects.filter(escola=escola_usuario)
    emolumentos = Emolumentos.objects.filter(escola=escola_usuario).exclude(nome__icontains="propina")

    if request.method == "POST":
        emolumento_id = request.POST.get("emolumento_id")
        tipo_pagamento_id = request.POST.get("tipo_pagamento")
        tipo_pagamento_selecionado = request.POST.get("tipo_pagamento_selecionado", "unico")
        
        emolumento = get_object_or_404(Emolumentos, id=emolumento_id, escola=escola_usuario)
        tipo_pagamento = get_object_or_404(TipoPagamento, id=tipo_pagamento_id, escola=escola_usuario)
        meses_selecionados = request.POST.getlist("meses")
        multas_selecionadas = request.POST.getlist("multas") 
        ano_lectivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
        data_pagamento = timezone.now()

        meses_info = []
        total_pago = 0

        # PAGAMENTO ÚNICO (sem meses selecionados)
        if tipo_pagamento_selecionado == "unico" or not meses_selecionados:
            # Verificar se há multa aplicável (para pagamento único)
            multa_valor = 0
            multa = emolumento.multas.filter(aplicar_multa=True).first()
            if multa:
                multa_valor = multa.valor_multa

            valor_total = emolumento.valor + multa_valor

            # Criar pagamento sem associar a um mês específico
            pagamento = Pagamento.objects.create(
                escola=escola_usuario,
                aluno=aluno,
                tipo=tipo_pagamento, 
                tipoServico=emolumento,
                ano_lectivo=ano_lectivo,
                valor=emolumento.valor,
                data_pagamento=data_pagamento,
                # mes=None (não associado a um mês específico)
            )
            
            if pagamento:
                total_pago += valor_total
                meses_info.append({
                    "nome": "Pagamento Único",
                    "valor": emolumento.valor,
                    "multa": multa_valor,
                    "total": valor_total,
                    "data_pagamento": data_pagamento,
                })

        # PAGAMENTO MENSAL (com meses selecionados)
        else:
            for mes_id in meses_selecionados:
                mes_obj = MesesPagar.objects.get(id=mes_id, escola=escola_usuario)

                multa_valor = 0
                if mes_id in multas_selecionadas:
                    multa = emolumento.multas.filter(aplicar_multa=True).first()
                    if multa:
                        multa_valor = multa.valor_multa

                valor_total_mes = emolumento.valor + multa_valor

                pagamento = Pagamento.objects.create(
                    escola=escola_usuario,
                    aluno=aluno,
                    tipo=tipo_pagamento, 
                    tipoServico=emolumento,
                    ano_lectivo=ano_lectivo,
                    valor=emolumento.valor,
                    data_pagamento=data_pagamento,
                    mes=mes_obj,
                )
                if pagamento:
                    total_pago += valor_total_mes
                    meses_info.append({
                        "nome": mes_obj.nome,
                        "valor": emolumento.valor,
                        "multa": multa_valor,
                        "total": valor_total_mes,
                        "data_pagamento": data_pagamento,
                    })
        # Número do recibo
        recibo_numero = Pagamento.objects.filter(escola=escola_usuario).count()

        # Gerar código de barras
        barcode_value = str(recibo_numero)
        drawing = createBarcodeDrawing(
            'Code128',
            value=barcode_value,
            barHeight=40,
            barWidth=2.5,
            humanReadable=True
        )
        barcode_svg = drawing.asString('svg')
        barcode_base64 = base64.b64encode(barcode_svg.encode("utf-8")).decode("utf-8")

        # Renderizar comprovativo
        context = {
            "aluno": aluno,
            "emolumento": emolumento,
            "meses_info": meses_info,
            "total_pago": total_pago,
            "tipo_pagamento": tipo_pagamento,
            "data_pagamento": data_pagamento,
            "atendente": request.user,
            "recibo": {"numero": recibo_numero},
            "barcode": barcode_base64,
            'escola': escola_usuario
        }
        return render(request, "financeiro/comprovativos/comprovativo_pagamento.html", context)
    usuario = request.user
    # GET: mostra o formulário
    context = {
        "aluno": aluno,
        "emolumentos": emolumentos,
        "tipos_pagamento": tipos_pagamento,
        "usuario":usuario,
        'escola': escola_usuario
    }
    perfil = request.user.perfil
    if perfil == 'diretor_geral':
        return render(request, "financeiro/diretor_geral/financas.html", context)
    elif perfil == "diretor_admin":
        return render(request, "financeiro/diretor_admin/financas.html", context)
    elif perfil == "secretario_admin":
        return render(request, "financeiro/secretario_admin/financas.html", context)
    elif perfil == "secretario_geral":
        return render(request, "financeiro/secretario_geral/financas.html", context)
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
def pagamento_manual(request, aluno_id):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})  
    
    aluno = get_object_or_404(Aluno, id=aluno_id, escola=escola_usuario)
    tipos_pagamento = TipoPagamento.objects.filter(escola=escola_usuario)
    emolumentos = Emolumentos.objects.filter(escola=escola_usuario)
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
    
    ano_lectivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()

    if request.method == "POST":
        emolumento_id = request.POST.get("emolumento_id")
        tipo_pagamento_id = request.POST.get("tipo_pagamento")
        tipo_pagamento = get_object_or_404(TipoPagamento, id=tipo_pagamento_id, escola=escola_usuario)
        
        # Obter o tipo de pagamento (único ou mensal)
        tipo_pagamento_radio = request.POST.get("tipo_pagamento_radio", "unico")
        
        if not emolumento_id:
            messages.error(request, "Por favor, selecione um serviço.")
            return redirect('financa:pagamento_manual', aluno_id=aluno_id)
            
        emolumento = get_object_or_404(Emolumentos, id=emolumento_id, escola=escola_usuario)
        
        # Obter valor manual inserido pelo usuário
        valor_manual_str = request.POST.get("valor_manual", "0")
        if not valor_manual_str or valor_manual_str == "":
            messages.error(request, "Por favor, insira um valor para o pagamento.")
            return redirect('financa:pagamento_manual', aluno_id=aluno_id)
        
        try:
            valor_manual = Decimal(valor_manual_str)
        except:
            messages.error(request, "Valor inválido. Use números com ponto decimal (ex: 1000.50).")
            return redirect('financa:pagamento_manual', aluno_id=aluno_id)
        
        data_pagamento = timezone.now()
        meses_info = []
        total_pago = 0

        # Se for pagamento único
        if tipo_pagamento_radio == "unico":
            # Obter multa para o emolumento
            multa_valor = Decimal('0')
            multa_obj = emolumento.multas.filter(aplicar_multa=True).first()
            if multa_obj:
                multa_valor = multa_obj.valor_multa
            
            valor_total = valor_manual + multa_valor

            # Criar pagamento único
            pagamento = Pagamento.objects.create(
                escola=escola_usuario,
                aluno=aluno, 
                tipo=tipo_pagamento,
                tipoServico=emolumento,
                valor=valor_total,
                data_pagamento=data_pagamento,
                ano_lectivo=ano_lectivo,
                #pago_por=request.user,
                mes=None  # Pagamento único não tem mês
            )

            total_pago += valor_total
            meses_info.append({
                "nome": "Pagamento Único",
                "valor": valor_manual,
                "multa": multa_valor,
                "total": valor_total,
                "data_pagamento": data_pagamento,
            })
        else:
            # Pagamento mensal
            meses_selecionados = request.POST.getlist("meses")
            multas_selecionadas = request.POST.getlist("multas") 
            
            if not meses_selecionados:
                messages.error(request, "Por favor, selecione pelo menos um mês para pagamento.")
                return redirect('financa:pagamento_manual', aluno_id=aluno_id)
            
            # Obter valor da multa do emolumento
            multa_valor = Decimal('0')
            multa_obj = emolumento.multas.filter(aplicar_multa=True).first()
            if multa_obj:
                multa_valor = multa_obj.valor_multa
            
            for mes_id in meses_selecionados:
                try:
                    mes_obj = MesesPagar.objects.get(id=mes_id, escola=escola_usuario)
                except MesesPagar.DoesNotExist:
                    continue
                
                # Verificar se este mês já foi pago
                ja_pago = Pagamento.objects.filter(
                    escola=escola_usuario,
                    aluno=aluno,
                    tipoServico=emolumento,
                    mes=mes_obj,
                    ano_lectivo=ano_lectivo
                ).exists()
                
                if ja_pago:
                    messages.warning(request, f"O mês {mes_obj.nome} já foi pago anteriormente.")
                    continue
                
                # Verificar se tem multa para este mês específico
                multa_mes_valor = multa_valor if mes_id in multas_selecionadas else Decimal('0')
                
                valor_total_mes = valor_manual + multa_mes_valor

                # Criar pagamento para o mês
                pagamento = Pagamento.objects.create(
                    escola=escola_usuario,
                    aluno=aluno,
                    tipo=tipo_pagamento,
                    tipoServico=emolumento,
                    mes=mes_obj,
                    valor=valor_total_mes,
                    data_pagamento=data_pagamento,
                    ano_lectivo=ano_lectivo,
                )

                total_pago += valor_total_mes
                meses_info.append({
                    "nome": mes_obj.nome,
                    "valor": valor_manual,
                    "multa": multa_mes_valor,
                    "total": valor_total_mes,
                    "data_pagamento": data_pagamento,
                })
        
        if not meses_info:
            messages.error(request, "Nenhum pagamento foi processado. Verifique os dados e tente novamente.")
            return redirect('financa:pagamento_manual', aluno_id=aluno_id)
        
        # Número do recibo
        recibo_numero = Pagamento.objects.filter(escola=escola_usuario).count()

        # Gerar código de barras
        barcode_value = str(recibo_numero)
        drawing = createBarcodeDrawing(
            'Code128',
            value=barcode_value,
            barHeight=40,
            barWidth=2.5,
            humanReadable=True
        )

        barcode_svg = drawing.asString('svg')
        barcode_base64 = base64.b64encode(barcode_svg.encode("utf-8")).decode("utf-8")

        contexto = {
            "aluno": aluno,
            "emolumento": emolumento,
            "meses_info": meses_info,
            "total_pago": total_pago,
            "tipo_pagamento": tipo_pagamento,
            "data_pagamento": data_pagamento,
            "atendente": request.user,
            "recibo": {"numero": recibo_numero},
            "barcode": barcode_base64,
            'escola': escola_usuario
        }
        return render(request, "financeiro/comprovativos/comprovativo_pagamento.html", contexto)

    # GET request - mostrar formulário
    contexto = {
        "aluno": aluno,
        "emolumentos": emolumentos,
        "tipos_pagamento": tipos_pagamento,
        "meses": MesesPagar.objects.filter(escola=escola_usuario),
        "usuario": request.user,
        "ano": ano_lectivo,
        'escola': escola_usuario
    }
    
    if perfil == 'diretor_geral':
        return render(request, "financeiro/diretor_geral/pagamentos.html", contexto)
    elif perfil == "diretor_admin":
        return render(request, "financeiro/diretor_admin/pagamentos.html", contexto)
    elif perfil == "secretario_geral":
        return render(request, "financeiro/secretario_geral/pagamentos.html", contexto)
    elif perfil == "secretario_admin":
        return render(request, "financeiro/secretario_admin/pagamentos.html", contexto)

@login_required
def obter_meses(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})  
    
    emolumento_id = request.GET.get("emolumento_id")
    aluno_id = request.GET.get("aluno_id")
    ano_lectivo_id = request.GET.get("ano_lectivo_id")
    
    try:
        emolumento = Emolumentos.objects.get(id=emolumento_id, escola=escola_usuario)
        aluno = Aluno.objects.get(id=aluno_id, escola=escola_usuario)
        ano_lectivo = AnoLectivo.objects.get(id=ano_lectivo_id, escola=escola_usuario)
        
        # Buscar valor da multa do emolumento
        multa_valor = 0
        multa_obj = emolumento.multas.filter(aplicar_multa=True).first()
        if multa_obj:
            multa_valor = float(multa_obj.valor_multa)
        
        # Buscar os IDs dos meses que JÁ foram pagos
        meses_pagos = Pagamento.objects.filter(
            escola=escola_usuario,
            aluno=aluno,
            tipoServico=emolumento,
            ano_lectivo=ano_lectivo
        ).exclude(mes__isnull=True).values_list('mes_id', flat=True)
        
        # Filtrar meses NÃO pagos ainda
        meses_disponiveis = MesesPagar.objects.filter(escola=escola_usuario).exclude(
            id__in=meses_pagos
        ).order_by('numero')
        
        meses_data = []
        for mes in meses_disponiveis:
            meses_data.append({
                "id": mes.id,
                "nome": mes.nome,
                "numero": mes.numero,
                "multa_valor": multa_valor
            })
        
        return JsonResponse({
            "meses": meses_data,
            "multa_valor": multa_valor
        })
        
    except Exception as e:
        print(f"Erro ao obter meses: {str(e)}")
        return JsonResponse({"meses": [], "error": str(e)})
            
@login_required
def emolumentos(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})  
    
    tipoPagamentos = TipoPagamento.objects.filter(escola=escola_usuario)
    emolumentos = Emolumentos.objects.filter(escola=escola_usuario)
    multas = Multa.objects.filter(escola=escola_usuario)
    mesesPagar = MesesPagar.objects.filter(escola=escola_usuario)
    desconto, created = DescontoFalta.objects.get_or_create(
        escola=escola_usuario,
        defaults={'valor_desconto': 0.00}
    )
    print(desconto)
    usuario = request.user
    context ={
        'tipoPagamentos': tipoPagamentos,
        'emolumentos': emolumentos,
        'multas': multas,
        'mesesPagar': mesesPagar,
        "usuario":usuario,
        "desconto":desconto,
        'escola': escola_usuario
    }
    perfil = request.user.perfil
    
    if perfil == 'diretor_geral':
        return render(request, "financeiro/diretor_geral/emolumentos.html", context)
    elif perfil == "diretor_admin":
        return render(request, 'financeiro/diretor_admin/emolumentos.html', context)
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
def add_emolumento(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Escola inválida.'})  
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        valor = request.POST.get('valor')
        
        if not nome or not valor:
            messages.error(request, 'Todos os campos são obrigatórios!')
            return redirect('financa:servicos')
        
        Emolumentos.objects.create(escola=escola_usuario, nome=nome, valor=valor)
        messages.success(request, 'Emolumento adicionado com sucesso!')
        return redirect('financa:servicos')
    
    return redirect('financa:servicos')

@login_required
def edit_emolumento(request):
    
    if request.method == 'POST':
        emolumento_id = request.POST.get('id')
        nome = request.POST.get('nome')
        valor = request.POST.get('valor')
        
        if not emolumento_id or not nome or not valor:
            messages.error(request, 'Todos os campos são obrigatórios!')
            return redirect('financa:servicos')
        
        emolumento = get_object_or_404(Emolumentos, id=emolumento_id)
        emolumento.nome = nome
        emolumento.valor = valor
        emolumento.save()
        
        messages.success(request, 'Emolumento atualizado com sucesso!')
        return redirect('financa:servicos')
    
    return redirect('financa:servicos')

from decimal import Decimal, InvalidOperation

@login_required
def editValorFalta(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola inválida.')
        return redirect('financa:servicos')
    
    if request.method == 'POST':
        valor_falta_id = request.POST.get('id')
        valor = request.POST.get('valor')
        
        print(f"Debug - ID: {valor_falta_id}")
        print(f"Debug - Valor original: '{valor}'")
        
        if not valor_falta_id or not valor:
            messages.error(request, 'Todos os campos são obrigatórios!')
            return redirect('financa:servicos')
        
        # Limpar e converter o valor
        try:
            # Remover espaços
            valor_limpo = valor.strip()
            
            # Substituir vírgula por ponto
            valor_limpo = valor_limpo.replace(',', '.')
            
            # Remover qualquer coisa que não seja número ou ponto
            import re
            valor_limpo = re.sub(r'[^\d.-]', '', valor_limpo)
            
            # Se tiver múltiplos pontos, manter apenas o último
            if valor_limpo.count('.') > 1:
                partes = valor_limpo.split('.')
                valor_limpo = ''.join(partes[:-1]) + '.' + partes[-1]
            
            print(f"Debug - Valor limpo: '{valor_limpo}'")
            
            # Converter para Decimal
            from decimal import Decimal, InvalidOperation
            valor_decimal = Decimal(valor_limpo)
            print(f"Debug - Decimal: {valor_decimal}")
            
        except (InvalidOperation, AttributeError, ValueError) as e:
            print(f"Debug - Erro na conversão: {e}")
            messages.error(request, f'Valor inválido: "{valor}". Use formato como 1000,50 ou 1000.50')
            return redirect('financa:servicos')
        
        # Buscar o objeto
        try:
            valor_falta = DescontoFalta.objects.get(
                id=valor_falta_id,
                escola=escola_usuario
            )
            print(f"Debug - Objeto encontrado: {valor_falta.id}")
            print(f"Debug - Valor antigo: {valor_falta.valor_desconto}")
            
            # Atualizar o valor
            valor_falta.valor_desconto = valor_decimal
            valor_falta.save()
            
            print(f"Debug - Novo valor salvo: {valor_falta.valor_desconto}")
            
            # VERIFICAÇÃO: Buscar novamente para confirmar
            valor_confirmado = DescontoFalta.objects.get(id=valor_falta_id)
            print(f"Debug - Valor confirmado no banco: {valor_confirmado.valor_desconto}")
            
            messages.success(request, f'✅ Valor de falta atualizado para Kz {valor_decimal:,.2f}')
            
        except DescontoFalta.DoesNotExist:
            messages.error(request, 'Configuração de desconto não encontrada!')
        except Exception as e:
            print(f"Debug - Erro ao salvar: {e}")
            messages.error(request, f'Erro ao atualizar: {str(e)}')
        
        return redirect('financa:servicos')
    
    return redirect('financa:servicos')

@login_required
def add_multa(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola inválida.')

    if request.method == 'POST':
        emolumento_id = request.POST.get('emolumento')
        aplicar_multa = request.POST.get('aplicar_multa') == 'Sim'
        data_aplicacao = request.POST.get('data_aplicacao')
        valor_multa = request.POST.get('valor_multa')
        
        if not all([emolumento_id, aplicar_multa, data_aplicacao, valor_multa]):
            messages.error(request, 'Todos os campos são obrigatórios!')
            return redirect('financa:servicos')
        
        emolumento = get_object_or_404(Emolumentos, id=emolumento_id)
        Multa.objects.create(
            escola=escola_usuario,
            emolumento=emolumento,
            aplicar_multa=aplicar_multa,
            data_aplicacao=data_aplicacao,
            valor_multa=valor_multa
        )
        messages.success(request, 'Multa adicionada com sucesso!')
        return redirect('financa:servicos')
    
    return redirect('financa:servicos')

@login_required
def edit_multa(request):
    if request.method == 'POST':
        multa_id = request.POST.get('multa_id') 
        emolumento_id = request.POST.get('emolumento')
        aplicar_multa = request.POST.get('aplicar_multa') == 'Sim'
        data_aplicacao = request.POST.get('data_aplicacao')
        valor_multa = request.POST.get('valor_multa')
        
        if not all([multa_id, emolumento_id, data_aplicacao, valor_multa]):
            messages.error(request, 'Todos os campos são obrigatórios!')
            return redirect('financa:servicos')
        
        multa = get_object_or_404(Multa, id=multa_id)
        emolumento = get_object_or_404(Emolumentos, id=emolumento_id)
        
        multa.emolumento = emolumento
        multa.aplicar_multa = aplicar_multa
        multa.data_aplicacao = data_aplicacao
        multa.valor_multa = valor_multa
        multa.save()
        
        messages.success(request, 'Multa atualizada com sucesso!')
        return redirect('financa:servicos')
    
    return redirect('financa:servicos') 

@login_required
def add_pagamento(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola inválida.')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        
        if not nome:
            messages.error(request, 'O campo nome é obrigatório!')
            return redirect('financa:servicos')
        
        TipoPagamento.objects.create(escola=escola_usuario, nome=nome)
        messages.success(request, 'Forma de pagamento adicionada com sucesso!')
        return redirect('financa:servicos')
    
    return redirect('financa:servicos')

@login_required
def edit_pagamento(request):
    if request.method == 'POST':
        pagamento_id = request.POST.get('id')
        nome = request.POST.get('nome')
        
        if not pagamento_id or not nome:
            messages.error(request, 'Todos os campos são obrigatórios!')
            return redirect('financa:servicos')
        
        pagamento = get_object_or_404(TipoPagamento, id=pagamento_id)
        pagamento.nome = nome
        pagamento.save()
        
        messages.success(request, 'Forma de pagamento atualizada com sucesso!')
        return redirect('financa:servicos')
    
    return redirect('financa:servicos')

@login_required
def add_mes(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola inválida.') 

    if request.method == 'POST':
        nome = request.POST.get('nome')
        numero = request.POST.get('numero')
        
        if not nome and not numero:
            messages.error(request, 'O campo nome é obrigatório!')
            return redirect('financa:servicos')
        
        MesesPagar.objects.create(escola=escola_usuario, nome=nome, numero=numero)
        messages.success(request, 'Mês adicionado com sucesso!')
        return redirect('financa:servicos')
    
    return redirect('financa:servicos')

@login_required
def edit_mes(request):
    if request.method == 'POST':
        mes_id = request.POST.get('id')
        nome = request.POST.get('nome')
        numero = request.POST.get('numero')
        
        if not mes_id or not nome or not numero:
            messages.error(request, 'Todos os campos são obrigatórios!')
            return redirect('financa:servicos')
        
        mes = get_object_or_404(MesesPagar, id=mes_id)
        mes.nome = nome
        mes.numero = numero
        mes.save()
        
        messages.success(request, 'Mês atualizado com sucesso!')
        return redirect('financa:servicos')
    
    return redirect('financa:servicos')

@login_required
def delete_item(request):
    if request.method == 'POST':
        item_type = request.POST.get('item_type')
        item_id = request.POST.get('item_id')
        
        if not item_type or not item_id:
            messages.error(request, 'Erro ao excluir item!')
            return redirect('financa:servicos')
        
        model_map = {
            'Emolumento': Emolumentos,
            'Multa': Multa,
            'FormaPagamento': TipoPagamento,
            'Mes': MesesPagar
        }
        
        model = model_map.get(item_type)
        if not model:
            messages.error(request, 'Tipo de item inválido!')
            return redirect('financa:servicos')
        
        item = get_object_or_404(model, id=item_id)
        item.delete()
         
        messages.success(request, f'{item_type} excluído com sucesso!')
        return redirect('financa:servicos')
     
    return redirect('financa:servicos')   

@login_required
def relatorio_view(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola inválida.') 

    # ano letivo atual ou escolhido no select
    ano_lectivo = request.GET.get("ano_lectivo")
    ano_lectivos_disponiveis = AnoLectivo.objects.filter(escola=escola_usuario)
    if not ano_lectivo:
        ano_lectivo = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()

    # Filtra os pagamentos (RECEITAS)
    pagamentos = Pagamento.objects.filter(escola=escola_usuario, ano_lectivo=ano_lectivo)
    
    # Filtra as despesas (GASTOS)
    # Se quiser filtrar despesas por ano também, adicione um campo ano na model Despesa
    despesas = Despesa.objects.filter(escola=escola_usuario, ano_lectivo=ano_lectivo)  # ou filtre por ano se tiver campo
    
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

    usuario = request.user
    context = {
        "ano_lectivo": ano_lectivo,
        "ano_lectivos_disponiveis": ano_lectivos_disponiveis,
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
        "usuario": usuario,
        "categoria_choices": Despesa.CATEGORIA_CHOICES,  # Para exibir nomes das categorias
        'escola': escola_usuario,
    }

    perfil = request.user.perfil
    if perfil == 'diretor_geral':
        return render(request, "financeiro/diretor_geral/relatorios.html", context)
    elif perfil == "diretor_admin":
        return render(request, "financeiro/diretor_admin/relatorios.html", context)
    else:
        return HttpResponse(
            """
            <html>
                <head>
                    <title>Erro 401 - Não Autorizado</title>
                </head>
                <body>
                    <h1>401</h1>
                    <p><strong>Perfil não autorizado</strong></p>
                </body>
            </html>
            """,
            status=401
        )
    
@login_required
def historico_financeiro(request, aluno_id):
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola inválida.') 

    aluno = get_object_or_404(Aluno, id=aluno_id, escola=escola_usuario)
    usuario = request.user

    # Buscar todos os pagamentos do aluno
    pagamentos = Pagamento.objects.filter(aluno=aluno, escola=escola_usuario).order_by("ano_lectivo", "data_pagamento")

    # Agrupar por ano lectivo
    historico = {}
    for p in pagamentos:
        if p.ano_lectivo not in historico:
            historico[p.ano_lectivo] = []
        historico[p.ano_lectivo].append(p)

    context = {
        "aluno": aluno,
        "historico": historico,
        "usuario":usuario,
        'escola': escola_usuario,
    }
    return render(request, "financeiro/comprovativos/historico-financeiro.html", context)

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
    despesas = Despesa.objects.filter(escola=escola_usuario)
    
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
        .filter(escola=escola_usuario)
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
    data_inicio = date(date.today().year, 1, 1)  # 1 de Janeiro do ano atual
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
        'escola': escola_usuario,
    }

    return render(request, "financeiro/relatorio_completo.html", context)

logger = logging.getLogger(__name__)
def calcular_saldo_disponivel(escola, ano_lectivo):
    """
    Calcula o saldo disponível = Total de Pagamentos - Total de Despesas Pagas
    """
    # Total de pagamentos dos alunos
    total_pagamentos = Pagamento.objects.filter(
        escola=escola,
        ano_lectivo=ano_lectivo
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    
    # Total de despesas já pagas (status='pago')
    total_despesas_pagas = Despesa.objects.filter(
        escola=escola,
        ano_lectivo=ano_lectivo,
        status='pago'
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    
    # Saldo disponível
    saldo_disponivel = total_pagamentos - total_despesas_pagas
    
    return {
        'total_pagamentos': total_pagamentos,
        'total_despesas_pagas': total_despesas_pagas,
        'saldo_disponivel': saldo_disponivel
    }

@login_required
def despesas(request): 
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola inválida.') 

    usuario = request.user
    
    # Buscar filtros
    categoria = request.GET.get('categoria')
    status = request.GET.get('status')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    
    despesas_lista = Despesa.objects.filter(escola=escola_usuario)
    
    # Aplicar filtros
    if categoria:
        despesas_lista = despesas_lista.filter(categoria=categoria)
    if status:
        despesas_lista = despesas_lista.filter(status=status)
    if mes:
        despesas_lista = despesas_lista.filter(data_despesa__month=mes)
    if ano:
        despesas_lista = despesas_lista.filter(data_despesa__year=ano)
    
    # Calcular totais
    total_despesas = despesas_lista.aggregate(total=Sum('valor'))['total'] or 0
    total_pagas = despesas_lista.filter(status='pago').aggregate(total=Sum('valor'))['total'] or 0
    total_pendentes = despesas_lista.filter(status='pendente').aggregate(total=Sum('valor'))['total'] or 0
    
    # Estatísticas por categoria
    categorias_stats = {}
    for categoria_code, categoria_nome in Despesa.CATEGORIA_CHOICES:
        total_cat = despesas_lista.filter(categoria=categoria_code).aggregate(total=Sum('valor'))['total'] or 0
        if total_cat > 0:
            categorias_stats[categoria_nome] = total_cat
    
    ano_lectivo = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()
    desconto_ativo = DescontoFalta.objects.filter(escola=escola_usuario).first()
    
    context = {
        "usuario": usuario,
        "despesas": despesas_lista,
        "total_despesas": total_despesas,
        "total_pagas": total_pagas,
        "total_pendentes": total_pendentes,
        "categorias_stats": categorias_stats,
        "categoria_choices": Despesa.CATEGORIA_CHOICES,
        "status_choices": Despesa.STATUS_CHOICES,
        'ano_lectivo': ano_lectivo,
        'desconto_ativo': desconto_ativo, 
        'escola': escola_usuario,
        "director_geral": Funcionario.objects.filter(escolas=escola_usuario, funcao__icontains='diretor_geral').first(),
        "director_admin": Funcionario.objects.filter(escolas=escola_usuario, funcao__icontains='diretor_admin').first(),
    }
    perfil = request.user.perfil   
    usuario = request.user 

    if perfil == 'diretor_admin':
        return render(request, 'financeiro/diretor_admin/despesas.html', context)
   
    elif perfil == 'diretor_geral':
        return render(request, 'financeiro/diretor_geral/despesas.html', context)
    elif perfil == 'secretario_admin':
        return render(request, 'financeiro/secretario_admin/despesas.html', context)
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
def adicionar_despesa(request):
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola inválida.')
        return redirect('financa:despesas')
    
    if request.method == 'POST':
        try:
            descricao = request.POST.get('descricao')
            valor_str = request.POST.get('valor')
            categoria = request.POST.get('categoria')
            data_despesa = request.POST.get('data_despesa')
            observacoes = request.POST.get('observacoes')
            status = request.POST.get('status', 'pendente')
            
            # Buscar ano letivo aberto
            ano_lectivo_obj = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()
            
            if not ano_lectivo_obj:
                messages.error(request, 'Nenhum ano letivo aberto encontrado!')
                return redirect('financa:despesas')
            
            # Usar o ID do ano letivo como string ou o ano
            ano_lectivo = str(ano_lectivo_obj.ano) if hasattr(ano_lectivo_obj, 'ano') else str(ano_lectivo_obj.id)
            
            # Converter valor para Decimal
            valor_str = valor_str.replace(',', '.')
            valor = Decimal(valor_str)
            
            # Determinar responsável
            perfil = request.user.perfil
            usuario = request.user
            
            if perfil == 'diretor_admin':
                responsavel = 'Director Administrativo'
            elif perfil == 'diretor_geral':
                responsavel = 'Director Geral'
            elif perfil == 'secretario_admin':
                responsavel = f'Secretário {usuario.username}'
            else:
                responsavel = 'Director Geral'
            
            # Se o status for 'pago', verificar saldo disponível
            if status == 'pago':
                saldo_info = calcular_saldo_disponivel(escola_usuario, ano_lectivo)
                saldo_disponivel = saldo_info['saldo_disponivel']
                
                if valor > saldo_disponivel:
                    messages.error(
                        request, 
                        f'⚠️ Saldo insuficiente!\n'
                        f'📊 Total de Pagamentos: Kz {saldo_info["total_pagamentos"]:,.2f}\n'
                        f'💸 Total de Despesas Pagas: Kz {saldo_info["total_despesas_pagas"]:,.2f}\n'
                        f'💰 Saldo Disponível: Kz {saldo_disponivel:,.2f}\n'
                        f'📝 Despesa atual: Kz {valor:,.2f}\n'
                        f'❌ Déficit de: Kz {valor - saldo_disponivel:,.2f}'
                    )
                    return redirect('financa:despesas')
            
            # Usar transação para garantir consistência
            with transaction.atomic():
                # Criar despesa
                despesa = Despesa(
                    escola=escola_usuario,
                    descricao=descricao,
                    valor=valor,
                    categoria=categoria,
                    data_despesa=data_despesa,
                    registro_por=responsavel,
                    observacoes=observacoes,
                    status=status,
                    ano_lectivo=ano_lectivo
                )
                
                # Processar arquivo se existir
                if 'comprovante' in request.FILES:
                    despesa.comprovante = request.FILES['comprovante']
                
                despesa.save()
            
            # Mostrar mensagem com novo saldo se for pago
            if status == 'pago':
                novo_saldo = calcular_saldo_disponivel(escola_usuario, ano_lectivo)['saldo_disponivel']
                messages.success(
                    request, 
                    f'✅ Despesa registrada como PAGA com sucesso!\n'
                    f'💵 Valor: Kz {valor:,.2f}\n'
                    f'💰 Novo saldo disponível: Kz {novo_saldo:,.2f}'
                )
            else:
                messages.success(request, '✅ Despesa registrada como PENDENTE com sucesso!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Despesa registrada!'})
            
            return redirect('financa:despesas')
            
        except Exception as e:
            print(f"Erro ao registrar despesa: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)})
            messages.error(request, f'Erro ao registrar despesa: {str(e)}')
            return redirect('financa:despesas')
    
    return redirect('financa:despesas')

@login_required
def gerar_folha_salario(request):
    """View para gerar folha de salário"""
    escola_id_sessao = request.session.get('escola_atual_id')
    
    try:
        escola_usuario = Escola.objects.get(id=escola_id_sessao)
    except Escola.DoesNotExist:
        messages.error(request, 'Escola inválida.') 

    if request.method == 'POST':
        try:
            # Recebe dados do formulário
            mes = int(request.POST.get('mes'))
            ano_lectivo_id = request.POST.get('ano_lectivo')
            
            # Validação
            if not mes:
                return JsonResponse({
                    'success': False,
                    'message': 'Mês e ano letivo são obrigatórios.'
                })
            
            # Busca ano letivo
            ano_lectivo = AnoLectivo.objects.filter(escola=escola_usuario, estado='Aberto').last()
            ano = datetime.now().year  # Ano atual
            
            # Busca valor de desconto ativo
            desconto_obj = DescontoFalta.objects.filter(escola=escola_usuario).first()
            if not desconto_obj:
                return JsonResponse({
                    'success': False,
                    'message': 'Nenhum valor de desconto por falta configurado.'
                })
            
            valor_desconto = desconto_obj.valor_desconto
            
            # Busca todos os funcionários
            funcionarios = Funcionario.objects.filter(escolas=escola_usuario)
            
            # Calcula para cada funcionário
            folha_detalhada = []
            total_salarios_bruto = Decimal('0')
            total_descontos = Decimal('0')
            total_liquido = Decimal('0')
            
            for funcionario in funcionarios:
                # Calcula faltas do mês
                faltas = FaltaFuncionario.objects.filter(
                    escola=escola_usuario,
                    funcionario=funcionario,
                    mes=mes,
                    ano_lectivo=ano_lectivo
                ).count()
                
                # Salário bruto
                salario_bruto = funcionario.salario or Decimal('0')
                
                # Desconto por faltas
                desconto_faltas = valor_desconto * faltas
                
                # Salário líquido
                salario_liquido = salario_bruto - desconto_faltas
                if salario_liquido < 0:
                    salario_liquido = Decimal('0')
                
                # Adiciona à folha
                folha_detalhada.append({
                    'funcionario': funcionario,
                    'funcao': funcionario.funcao,
                    'faltas': faltas,
                    'salario_bruto': salario_bruto,
                    'valor_desconto': valor_desconto,
                    'desconto_faltas': desconto_faltas,
                    'salario_liquido': salario_liquido,
                    "director_geral": Funcionario.objects.filter(escolas=escola_usuario, funcao__icontains='diretor_geral').first(),
                    "director_admin": Funcionario.objects.filter(escolas=escola_usuario, funcao__icontains='diretor_admin').first(),
                })
                
                # Acumula totais
                total_salarios_bruto += salario_bruto
                total_descontos += desconto_faltas
                total_liquido += salario_liquido
            
            # Ordena por nome do funcionário
            folha_detalhada.sort(key=lambda x: x['funcionario'].nome)
            
            # Renderiza o template HTML
            html_content = render_to_string('documentos/folha_salario_documento.html', {
                'mes': mes,
                'ano': ano,
                'ano_lectivo': ano_lectivo,
                'folha_detalhada': folha_detalhada,
                'total_salarios_bruto': total_salarios_bruto,
                'total_descontos': total_descontos,
                'total_liquido': total_liquido,
                'valor_desconto': valor_desconto,
                'data_geracao': datetime.now(),
                'usuario': request.user,
                'escola': escola_usuario
            })
            
            return JsonResponse({
                'success': True,
                'html': html_content
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao gerar folha: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método não permitido'
    })

@login_required
def editar_despesa(request, id):
    despesa = get_object_or_404(Despesa, id=id)
    escola_usuario = despesa.escola
    
    if request.method == 'POST':
        try:
            novo_valor = Decimal(str(request.POST.get('valor')).replace(',', '.'))
            novo_status = request.POST.get('status')
            valor_antigo = despesa.valor
            status_antigo = despesa.status
            
            # Verificar se está alterando para 'pago'
            if novo_status == 'pago' and status_antigo != 'pago':
                # Calcular saldo disponível
                saldo_info = calcular_saldo_disponivel(escola_usuario, despesa.ano_lectivo)
                saldo_disponivel = saldo_info['saldo_disponivel']
                
                # Verificar se tem saldo suficiente
                if novo_valor > saldo_disponivel:
                    messages.error(
                        request, 
                        f'⚠️ Saldo insuficiente para pagar esta despesa!\n'
                        f'💰 Saldo disponível: Kz {saldo_disponivel:,.2f}\n'
                        f'📝 Valor da despesa: Kz {novo_valor:,.2f}\n'
                        f'❌ Faltam: Kz {novo_valor - saldo_disponivel:,.2f}'
                    )
                    return redirect('financa:despesas')
            
            # Se estava pago e vai continuar pago, mas mudou o valor
            elif novo_status == 'pago' and status_antigo == 'pago' and novo_valor != valor_antigo:
                # Calcular a diferença
                diferenca = novo_valor - valor_antigo
                if diferenca > 0:
                    saldo_info = calcular_saldo_disponivel(escola_usuario, despesa.ano_lectivo)
                    saldo_disponivel = saldo_info['saldo_disponivel']
                    
                    if diferenca > saldo_disponivel:
                        messages.error(
                            request,
                            f'⚠️ Aumento de Kz {diferenca:,.2f} excede o saldo disponível!\n'
                            f'💰 Saldo disponível: Kz {saldo_disponivel:,.2f}'
                        )
                        return redirect('financa:despesas')
            
            with transaction.atomic():
                # Atualizar dados básicos
                despesa.descricao = request.POST.get('descricao')
                despesa.valor = novo_valor
                despesa.categoria = request.POST.get('categoria')
                despesa.data_despesa = request.POST.get('data_despesa')
                despesa.registro_por = request.POST.get('responsavel')
                despesa.status = novo_status
                despesa.observacoes = request.POST.get('observacoes', '')
                
                # Processar novo comprovante se enviado
                if 'comprovante' in request.FILES:
                    if despesa.comprovante:
                        despesa.comprovante.delete(save=False)
                    despesa.comprovante = request.FILES['comprovante']
                
                despesa.save()
            
            # Mensagem de sucesso com novo saldo
            novo_saldo = calcular_saldo_disponivel(escola_usuario, despesa.ano_lectivo)['saldo_disponivel']
            messages.success(
                request,
                f'✅ Despesa atualizada com sucesso!\n'
                f'💰 Saldo disponível atual: Kz {novo_saldo:,.2f}'
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Despesa atualizada!'})
            
            return redirect('financa:despesas')
            
        except Exception as e:
            print(f"Erro ao atualizar despesa: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)})
            messages.error(request, f'Erro ao atualizar despesa: {str(e)}')
            return redirect('financa:despesas')
    
    # Para GET, retornar dados em JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'id': despesa.id,
            'descricao': despesa.descricao,
            'valor': float(despesa.valor),
            'categoria': despesa.categoria,
            'data_despesa': despesa.data_despesa.strftime('%Y-%m-%d'),
            'registro_por': despesa.registro_por,
            'status': despesa.status,
            'observacoes': despesa.observacoes,
            'comprovante_url': despesa.comprovante.url if despesa.comprovante else '',
            'comprovante_nome': despesa.comprovante.name.split('/')[-1] if despesa.comprovante else '',
        }
        return JsonResponse(data)
    
    return redirect('financa:despesas')

@login_required
def excluir_despesa(request, id):
    if request.method == 'POST':
        try:
            despesa = get_object_or_404(Despesa, id=id)
            despesa.delete()
            messages.success(request, 'Despesa excluída com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao excluir despesa: {str(e)}')
    
    return redirect('financa:despesas')

def atualizar_estado_aluno(aluno: "Aluno", escola_usuario):
    """Atualiza o estado (Adimplente/Inadimplente) do aluno com base nos pagamentos de propina."""

    try:
        hoje = now().date()
        ano_lectivo = AnoLectivo.objects.filter(estado='Aberto', escola=escola_usuario).last()
        
        if not ano_lectivo:
            logger.warning(f"Não há ano letivo aberto para atualizar estado do aluno {aluno.id}")
            return

        # Buscar TODOS os tipos de propina
        tipos_propina = Emolumentos.objects.filter(nome__icontains="propina", escola=escola_usuario)
        
        if not tipos_propina.exists():
            logger.error("Nenhum serviço de propina encontrado no sistema")
            return

        # Obtém todos os meses cadastrados ordenados
        meses = MesesPagar.objects.filter(escola=escola_usuario)
        if hasattr(MesesPagar, "ordem"):
            meses = meses.order_by("ordem")
        else:
            meses = meses.order_by("id")

        if not meses.exists():
            logger.warning("Não há meses cadastrados no sistema")
            return

        # Mapeamento de meses em português para inglês
        meses_portugues_ingles = {
            'janeiro': 'january', 'fevereiro': 'february', 'março': 'march',
            'abril': 'april', 'maio': 'may', 'junho': 'june',
            'julho': 'july', 'agosto': 'august', 'setembro': 'september',
            'outubro': 'october', 'novembro': 'november', 'dezembro': 'december'
        }

        # Encontra o mês atual
        nome_mes_hoje_ingles = calendar.month_name[hoje.month].lower()
        mes_atual = None
        
        for mes in meses:
            # Converte o nome do mês cadastrado para inglês para comparação
            mes_nome_lower = mes.nome.lower()
            if mes_nome_lower in meses_portugues_ingles:
                mes_nome_ingles = meses_portugues_ingles[mes_nome_lower]
                # Compara os primeiros 3 caracteres
                if mes_nome_ingles[:3] == nome_mes_hoje_ingles[:3]:
                    mes_atual = mes
                    break

        # Se o mês atual não está cadastrado, não prosseguir
        if not mes_atual:
            logger.info(f"Mês atual ({calendar.month_name[hoje.month]}) não está cadastrado no sistema")
            return

        # Verificar se o aluno tem PELO MENOS UM tipo de propina pago
        tem_propina_paga = False
        tem_propina_em_atraso = False
        
        for propina in tipos_propina:
            # Verifica pagamento do mês atual para este tipo de propina
            pagou_mes_atual = Pagamento.objects.filter(
                escola=escola_usuario,
                aluno=aluno,
                tipoServico=propina,
                ano_lectivo=ano_lectivo,
                mes=mes_atual
            ).exists()

            # Verifica multa específica para este tipo de propina
            multa = Multa.objects.filter(emolumento=propina, aplicar_multa=True, escola=escola_usuario).first()
            
            if pagou_mes_atual:
                tem_propina_paga = True
            elif multa and hoje.day > multa.data_aplicacao:
                tem_propina_em_atraso = True

        # Determina o estado com base na NOVA lógica
        if tem_propina_paga:
            # Se tem pelo menos uma propina paga, é adimplente
            estado = "Adimplente"
        elif tem_propina_em_atraso:
            # Se não tem nenhuma paga mas tem pelo menos uma em atraso, é inadimplente
            estado = "Inadimplente"
        else:
            # Se não tem paga mas ainda está dentro do prazo, é adimplente
            estado = "Adimplente"

        # Atualiza ou cria reconfirmação
        reconf, created = Reconfirmacao.objects.get_or_create(
            escola=escola_usuario,
            aluno=aluno,
            ano_letivo=ano_lectivo,
            defaults={"estado": estado}
        )

        if not created and reconf.estado != estado:
            reconf.estado = estado
            reconf.save()
            logger.info(f"Estado do aluno {aluno.id} atualizado para {estado}")
            
    except Exception as e:
        logger.error(f"Erro ao atualizar estado do aluno {aluno.id}: {str(e)}")
