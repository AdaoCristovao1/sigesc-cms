from django.db import models
from administracao.models import *
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
import os
from django.utils import timezone

class Disciplina(models.Model):
    nome = models.CharField(max_length=100)
    classe = models.IntegerField()
    codigo = models.CharField(max_length=10)
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            # Geração de código: 3 letras do nome + número aleatório
            prefix = self.nome[:3].upper() if self.nome else 'DSC'
            random_part = get_random_string(5, allowed_chars='0123456789')
            self.codigo = f'{prefix}{random_part}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nome}'

class DisciplinasClasse(models.Model):
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.disciplina.nome} - {self.classe.numero}ª Classe'

class Nota(models.Model):
    ano_lectivo = models.ForeignKey('administracao.AnoLectivo', on_delete=models.CASCADE)
    aluno = models.ForeignKey('administracao.Aluno', on_delete=models.CASCADE)
    classe = models.ForeignKey('administracao.Classe', on_delete=models.CASCADE)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    trimestre = models.IntegerField(choices=[(1, '1º'), (2, '2º'), (3, '3º'), (4, 'exame')])
    valor = models.DecimalField(max_digits=5, decimal_places=2) 

    def __str__(self):
        return f'{self.aluno.usuario.username} - {self.disciplina.nome} - T{self.trimestre}' 
 
class ProfessorVinculo(models.Model):
    professor = models.ForeignKey(Funcionario, on_delete=models.CASCADE, limit_choices_to={'funcao': 'professor'})
    turma = models.ForeignKey('administracao.Turma', on_delete=models.CASCADE)
    disciplina = models.ForeignKey('Disciplina', on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Vínculo de Professor"
        verbose_name_plural = "Vínculos de Professores"

    def __str__(self):
        return f'{self.professor.nome} | {self.disciplina.nome} - {self.turma.nome}'

class HorarioAula(models.Model):
    DIA_SEMANA_CHOICES = [
        ('2', 'Segunda-feira'),
        ('3', 'Terça-feira'),
        ('4', 'Quarta-feira'),
        ('5', 'Quinta-feira'),
        ('6', 'Sexta-feira'),
        ('7', 'Sábado'),
    ]

    vinculo = models.ForeignKey(ProfessorVinculo, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.CharField(max_length=1, choices=DIA_SEMANA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    
    # Opcional: Para identificar se é o 1º tempo, 2º tempo, etc.
    tempo_aula = models.PositiveIntegerField(help_text="Ex: 1 para primeiro tempo")

    class Meta:
        ordering = ['dia_semana', 'hora_inicio']
        verbose_name = "Horário de Aula"
        
    def __str__(self):
        return f'{self.get_dia_semana_display()}: {self.hora_inicio} - {self.hora_fim}'
    
class Coordenacao(models.Model):
    TIPOS = [
        ('turno', 'Coordenador de Turno'),
        ('turma', 'Coordenador de Turma'),
        ('disciplina', 'Coordenador de Disciplina'),
    ]

    TURNOS = [
        ('Manhã', 'Manhã'),
        ('Tarde', 'Tarde'),
        ('Noite', 'Noite'),
    ]

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=15, choices=TIPOS)

    turno = models.CharField(max_length=10, choices=TURNOS, null=True, blank=True)
    turma = models.ForeignKey(Turma, on_delete=models.SET_NULL, null=True, blank=True)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.funcionario.nome} - {self.get_tipo_display()}"

    def clean(self): 
        if self.tipo == 'turno':
            if not self.turno:
                raise ValidationError("O campo 'turno' deve ser preenchido para Coordenador de Turno.")
            if self.turma or self.disciplina:
                raise ValidationError("Apenas o campo 'turno' deve estar preenchido para este tipo.")
        
        elif self.tipo == 'turma':
            if not self.turma:
                raise ValidationError("O campo 'turma' deve ser preenchido para Coordenador de Turma.")
            if self.turno or self.disciplina:
                raise ValidationError("Apenas o campo 'turma' deve estar preenchido para este tipo.")
        
        elif self.tipo == 'disciplina':
            if not self.disciplina:
                raise ValidationError("O campo 'disciplina' deve ser preenchido para Coordenador de Disciplina.")
            if self.turno or self.turma:
                raise ValidationError("Apenas o campo 'disciplina' deve estar preenchido para este tipo.")
    
    class Meta:
        verbose_name = "Coordenação"
        verbose_name_plural = "Coordenações"
        unique_together = ('funcionario', 'tipo', 'turno', 'turma', 'disciplina')

class Monografia(models.Model):
    # Campos principais
    titulo = models.CharField(max_length=200, verbose_name="Título")
    resumo = models.TextField(verbose_name="Resumo", blank=True, null=True)
    
    # Autor
    autor = models.CharField(max_length=100, verbose_name="Autor")
    autor_curso = models.CharField(max_length=100, verbose_name="Curso")
    autor_telefone = models.CharField(max_length=20, verbose_name="Telefone")
    autor_email = models.EmailField(max_length=100, verbose_name="Email")
    
    # Orientador
    orientador = models.CharField(max_length=100, verbose_name="Orientador")
    orientador_telefone = models.CharField(max_length=20, verbose_name="Telefone do Orientador")
    
    # Arquivo
    arquivo = models.FileField(
        upload_to='monografias/%Y/%m/%d/',
        verbose_name="Arquivo",
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx']
            )
        ]
    )
    
    # Controle
    ano_academico = models.CharField(max_length=9, verbose_name="Ano Académico")
    data_submissao = models.DateTimeField(default=timezone.now)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('rascunho', 'Rascunho'),
            ('submetido', 'Submetido'),
            ('avaliacao', 'Em Avaliação'),
            ('aprovado', 'Aprovado'),
            ('reprovado', 'Reprovado'),
        ],
        default='avaliacao'
    )
    
    nota_final = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Campos automáticos
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.autor} - {self.titulo}"
    
    def get_nome_arquivo(self):
        """Retorna apenas o nome do arquivo sem o caminho"""
        return os.path.basename(self.arquivo.name)
    
    @property
    def esta_aprovada(self):
        return self.estado == 'aprovado'

class Avaliacao(models.Model):
    ESTADO_AVALIACAO = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]
    
    monografia = models.ForeignKey('Monografia', on_delete=models.CASCADE, related_name='avaliacoes')
    avaliador = models.CharField(max_length=100, verbose_name="Avaliador")
    data_atribuicao = models.DateTimeField(default=timezone.now)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_AVALIACAO, default='pendente')
    nota = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    parecer = models.TextField(verbose_name="Parecer", blank=True)
    recomendacao = models.CharField(
        max_length=20,
        choices=[
            ('aprovado', 'Aprovar'),
            ('reprovado', 'Reprovar'),
            ('correcoes', 'Necessita Correções'),
        ],
        blank=True
    )
    
    class Meta:
        ordering = ['-data_atribuicao']
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"
    
    def __str__(self):
        return f"Avaliação de {self.monografia.titulo[:30]} por {self.avaliador}"
    
    @property
    def esta_atrasada(self):
        if self.estado == 'pendente' and self.data_atribuicao:
            dias_espera = (timezone.now() - self.data_atribuicao).days
            return dias_espera > 7  # Considera atrasada após 7 dias
        return False
    