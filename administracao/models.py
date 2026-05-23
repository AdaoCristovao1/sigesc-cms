from django.db import models
from core.models import Usuario
from django.conf import settings
from escola.models import Escola

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
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    ano = models.CharField(max_length=50)
    estado = models.CharField(max_length=50, default='Aberto')

    def __str__(self):
        return self.ano
    
class Curso(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.nome

class Classe(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    numero = models.IntegerField()
    designacao = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.numero}ª Classe'

class Sala(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    nome = models.CharField(max_length=50)

    def __str__(self):
        return f'Sala {self.nome}'

class Turma(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    ano_letivo = models.CharField(max_length=9)
    nome = models.CharField(max_length=50)
    turno = models.CharField(max_length=10, choices=TURNOS)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'Turma {self.nome} - {self.classe} - {self.curso} - {self.turno}'

class Aluno(models.Model): 
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
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
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
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

    class Meta:
        indexes = [
            models.Index(fields=['escola']),
            models.Index(fields=['aluno']),
            models.Index(fields=['ano_letivo']),
            models.Index(fields=['estado']),
            models.Index(fields=['escola', 'ano_letivo']),
            models.Index(fields=['aluno', 'ano_letivo']),
        ]

    def __str__(self):
        return f'{self.aluno.nome_completo} - {self.ano_letivo}'
    

from django.contrib.auth import get_user_model

Usuario = get_user_model()

class Funcionario(models.Model):
    GENEROS = [
        ('M', 'Masculino'),
        ('F', 'Feminino'), 
        ('O', 'Outro'),
    ]
    
    FUNCOES = [
        ('Diretor Geral', 'Diretor Geral'),
        ('Diretor Pedagógico', 'Diretor Pedagógico'),
        ('Diretor Administrativo', 'Diretor Administrativo'),
        ('Coordenador de Turno', 'Coordenador de Turno'),
        ('Coordenador de Turma', 'Coordenador de Turma'),
        ('Coordenador de Disciplina', 'Coordenador de Disciplina'),
        ('Secretário Geral', 'Secretário Geral'),
        ('Secretário Administrativo', 'Secretário Administrativo'),
        ('Secretário Pedagógico', 'Secretário Pedagógico'),
        ('Professor', 'Professor'),
        ('Auxiliar Administrativo', 'Auxiliar Administrativo'),
        ('Auxiliar de Limpeza', 'Auxiliar de Limpeza'),
        ('Segurança', 'Segurança'),
        ('Motorista', 'Motorista'),
        ('Outro', 'Outro'),
    ]
    
    # Relacionamento ManyToMany para múltiplas escolas
    escolas = models.ManyToManyField(Escola, related_name='funcionarios', verbose_name="Escolas")
    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='funcionario'
    )
    nome = models.CharField("Nome Completo", max_length=255)
    bi = models.CharField("Bilhete de Identidade", max_length=20, unique=True) 
    genero = models.CharField("Gênero", max_length=1, choices=GENEROS)
    nivel_academico = models.CharField("Nível Acadêmico", max_length=100)
    area_formacao = models.CharField("Área de Formação", max_length=100)
    funcao = models.CharField("Função", max_length=100, choices=FUNCOES)
    telefone = models.CharField("Telefone", max_length=15)
    email = models.EmailField("E-mail", max_length=255, blank=True, null=True)
    salario = models.DecimalField(
        "Salário",
        max_digits=10, 
        decimal_places=2, 
        default=0,
    )

    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ['-criado_em']

    def __str__(self): 
        return f'{self.nome} - {self.funcao}'
    
    def escolas_nomes(self):
        return ", ".join([escola.nome for escola in self.escolas.all()])
    
    def total_escolas(self):
        return self.escolas.count()

class DescontoFalta(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
    valor_desconto = models.DecimalField( 
        max_digits=10,
        decimal_places=2,
        default=0, 
        verbose_name="Valor de Desconto por Falta"  
    )
        
    def __str__(self):
        return f"{self.valor_desconto}"

class FaltaFuncionario(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE)
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
    