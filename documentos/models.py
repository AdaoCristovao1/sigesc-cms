from django.db import models

class CartaoEstudante(models.Model):
    aluno = models.OneToOneField('core.Usuario', on_delete=models.CASCADE, limit_choices_to={'perfil': 'aluno'})
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    emitido_em = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'Cartão - {self.aluno.username}'

class Declaracao(models.Model):
    aluno = models.ForeignKey('core.Usuario', on_delete=models.CASCADE, limit_choices_to={'perfil': 'aluno'})
    tipo = models.CharField(max_length=100) 
    numero = models.CharField(max_length=20, unique=True)
    emitida_em = models.DateField(auto_now_add=True)
    conteudo = models.TextField()

    def __str__(self):
        return f'{self.tipo} - {self.numero}'

class Certificado(models.Model):
    aluno = models.ForeignKey('core.Usuario', on_delete=models.CASCADE, limit_choices_to={'perfil': 'aluno'})
    curso = models.CharField(max_length=100)
    ano_conclusao = models.CharField(max_length=4)
    numero = models.CharField(max_length=20, unique=True)
    emitido_em = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'Certificado {self.numero}'
