from django.db import models
from core.models import Usuario
from django.conf import settings

TURNOS = [
    ('Manhã', 'Manhã'),
    ('Tarde', 'Tarde'),
    ('Noite', 'Noite'),
]

GENERO_CHOICES = [
    ('M', 'Masculino'),
    ('F', 'Feminino'),
]

ESTADOS = [
    ('Adimplente', 'Adimplente'),
    ('Inadimplente', 'Inadimplente'),
]

ESTADOSCLASSES = [
    ('Pendente', 'Pendente'),
    ('Aprovado', 'Aprovado'),
    ('Reprovado', 'Reprovado'),
]

class AnoLectivo(models.Model):
    ano = models.CharField(max_length=50)
    estado = models.CharField(max_length=50, default='Aberto')

    def __str__(self):
        return self.ano
    
class Curso(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

class Classe(models.Model):
    numero = models.IntegerField()
    designacao = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.numero}ª Classe'

class Sala(models.Model):
    nome = models.CharField(max_length=50)

    def __str__(self):
        return f'Sala {self.nome}'

class Turma(models.Model):
    ano_letivo = models.CharField(max_length=9)
    nome = models.CharField(max_length=50)
    turno = models.CharField(max_length=10, choices=TURNOS)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'Turma {self.nome} - {self.classe} - {self.curso} - {self.turno}'

class Aluno(models.Model): 
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, limit_choices_to={'perfil': 'aluno'})
    nome_completo = models.CharField(max_length=255)
    numero_mecanografico = models.CharField(max_length=20, unique=True)
    bi = models.CharField(max_length=14, unique=True, null=True)
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES) 
    nome_pai = models.CharField(max_length=255, null=True)
    nome_mae = models.CharField(max_length=255, null=True)
    dia_nasc = models.CharField(max_length=255, null=True)
    mes_nasc = models.CharField(max_length=255, null=True)
    ano_nasc = models.CharField(max_length=255, null=True)
    naturalidade = models.CharField(max_length=255, null=True)
    foto = models.ImageField(upload_to='alunos/fotos/', blank=True, null=True)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True, blank=True)
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True, blank=True)
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True)
    turno = models.CharField(max_length=10, choices=TURNOS) 
 
    def __str__(self): 
        return self.nome_completo
 
class Reconfirmacao(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    ano_letivo = models.CharField(max_length=9)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Adimplente')  
    estadoClasse = models.CharField(max_length=20, choices=ESTADOSCLASSES, default='Pendente')
    data = models.DateField(auto_now_add=True)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True)
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True)
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True)
    turno = models.CharField(max_length=10, choices=TURNOS) 

    def __str__(self):
        return f'{self.aluno.nome_completo} - {self.ano_letivo}'
    
class Funcionario(models.Model):
    GENEROS = [
        ('M', 'Masculino'),
        ('F', 'Feminino'), 
        ('O', 'Outro'),
    ]
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=255)
    bi = models.CharField("Bilhete de Identidade", max_length=20, unique=True)
    genero = models.CharField(max_length=1, choices=GENEROS)
    nivel_academico = models.CharField(max_length=100)
    area_formacao = models.CharField(max_length=100)
    funcao = models.CharField(max_length=100)
    telefone = models.CharField(max_length=15)
    salario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Salário"
    )

    def __str__(self): 
        return f'{self.nome}'

class DescontoFalta(models.Model):
    valor_desconto = models.DecimalField( 
        max_digits=10,
        decimal_places=2,
        default=0, 
        verbose_name="Valor de Desconto por Falta"  
    )
        
    def __str__(self):
        return f"{self.valor_desconto}"

class FaltaFuncionario(models.Model):
    funcionario = models.ForeignKey(
        'Funcionario',
        on_delete=models.CASCADE,
        related_name='faltas'
    )
    ano_lectivo = models.ForeignKey(
        'AnoLectivo',
        on_delete=models.CASCADE,
        related_name='faltas_funcionarios'
    )
    mes = models.PositiveSmallIntegerField(
        verbose_name="Mês",
        help_text="Informe o mês da falta (1 a 12)"
    )
    dia = models.PositiveSmallIntegerField(
        verbose_name="Dia da Falta"
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Registrado por"
    )
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Falta de Funcionário"
        verbose_name_plural = "Faltas de Funcionários"
        ordering = ['-data_registro']

    def __str__(self):
        return f"{self.funcionario} - {self.dia}/{self.mes} ({self.ano_lectivo})"
    