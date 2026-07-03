from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from escola.models import Escola


class TipoPagamento(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    def __str__(self):
        return self.nome

class Emolumentos(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)   
    valor = models.DecimalField(max_digits=10, decimal_places=2) 

    def __str__(self):
        return f'{self.nome} - {self.valor}' 

class Multa(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    emolumento = models.ForeignKey(Emolumentos, on_delete=models.CASCADE, related_name="multas")
    aplicar_multa = models.BooleanField(default=False)
    data_aplicacao = models.PositiveSmallIntegerField(help_text="Dia do mês em que a multa deve ser aplicada (1-31)")
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Multa - {self.emolumento.nome} ({'Ativa' if self.aplicar_multa else 'Inativa'})"

class MesesPagar(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    numero = models.PositiveSmallIntegerField(unique=False) 

    def __str__(self):
        return self.nome

class Pagamento(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    aluno = models.ForeignKey('administracao.Aluno', on_delete=models.CASCADE)
    tipo = models.ForeignKey(TipoPagamento, on_delete=models.SET_NULL, null=True) 
    tipoServico = models.ForeignKey(Emolumentos, on_delete=models.SET_NULL, null=True) 
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_pagamento = models.DateField(auto_now_add=True)
    ano_lectivo = models.CharField(max_length=9) 
    mes = models.ForeignKey(MesesPagar, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'{self.aluno.usuario.get_full_name()} - {self.tipo.nome} - {self.valor}'

class Recibo(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    pagamento = models.OneToOneField(Pagamento, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20, unique=True)
    data_emissao = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'Recibo {self.codigo}'
    
class Despesa(models.Model):
    CATEGORIA_CHOICES = [
        ('salarios', 'Salários'),
        ('material', 'Material Escolar'),
        ('manutencao', 'Manutenção'),
        ('energia', 'Energia/Água'),
        ('internet', 'Internet/Telefone'),
        ('alimentacao', 'Alimentação'),
        ('transportes', 'Transportes'),
        ('limpeza', 'Limpeza'),
        ('outros', 'Outros'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
    ]
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='outros')
    data_despesa = models.DateField(default=timezone.now, verbose_name="Data da Despesa")
    data_registro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Registro")
    registro_por = models.CharField(max_length=100, verbose_name="Responsável pela Despesa")
    comprovante = models.FileField(upload_to='comprovantes/despesas/', null=True, blank=True, verbose_name="Comprovante")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    ano_lectivo = models.CharField(max_length=9) 
    
    class Meta:
        ordering = ['-data_despesa']
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'
    
    def __str__(self):
        return f"{self.descricao} - Kz {self.valor}"
