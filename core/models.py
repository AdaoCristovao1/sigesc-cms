from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    PERFIS = [ 
        ('admin_central', 'Admin Central'),
        ('diretor_geral', 'Diretor Geral'),
        ('diretor_pedagogico', 'Diretor Pedagógico'),
        ('diretor_admin', 'Diretor Administrativo'),
        ('coordenador_turno', 'Coordenador de Turno'),
        ('coordenador_turma', 'Coordenador de Turma'),
        ('coordenador_disc', 'Coordenador de Disciplina'),
        ('secretario_geral', 'Secretário Geral'), 
        ('secretario_admin', 'Secretário Administrativo'),
        ('secretario_ped', 'Secretário Pedagógico'),
        ('professor', 'Professor'), 
        ('encarregado', 'Encarregado de Educação'),
        ('aluno', 'Aluno'), 
    ]
    perfil = models.CharField(max_length=20, choices=PERFIS)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    foto = models.ImageField(upload_to='usuarios/fotos/', blank=True, null=True)

    def __str__(self):
        return f'{self.username}'
