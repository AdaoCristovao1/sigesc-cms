from django.db import models

class Escola(models.Model):
    nome = models.CharField(max_length=255)
    decreto_executivo = models.CharField(max_length=100, blank=True, null=True)
    
    provincia = models.CharField(max_length=100)
    municipio = models.CharField(max_length=100)
    endereco = models.CharField(max_length=255)
    
    nif = models.CharField(max_length=50, unique=True, null=True)
    
    logotipo = models.ImageField(upload_to='logos/', blank=True, null=True)
    
    contacto = models.CharField(max_length=20)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome
    
class LogSistema(models.Model):
    TIPO_CHOICES = [
        ('info', 'Informação'),
        ('warning', 'Aviso'),
        ('error', 'Erro'),
        ('success', 'Sucesso'),
    ]
    
    usuario = models.ForeignKey('core.Usuario', on_delete=models.SET_NULL, null=True)
    acao = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='info')
    detalhes = models.TextField(blank=True)
    ip = models.GenericIPAddressField(blank=True, null=True)
    data = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data']
    
    @property
    def classe(self):
        classes = {
            'info': 'info',
            'warning': 'warning',
            'error': 'danger',
            'success': 'success',
        }
        return classes.get(self.tipo, 'secondary')
    
    @property
    def icone(self):
        icones = {
            'info': 'info-circle',
            'warning': 'exclamation-triangle',
            'error': 'times-circle',
            'success': 'check-circle',
        }
        return icones.get(self.tipo, 'circle')
    
class BackupSistema(models.Model):
    nome = models.CharField(max_length=255)
    caminho = models.CharField(max_length=500)
    tamanho = models.CharField(max_length=50, blank=True)
    descricao = models.TextField(blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey('core.Usuario', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return self.nome

class ConfiguracaoSistema(models.Model):
    nome_sistema = models.CharField(max_length=255, default='SIGESC - Sistema Integrado de Gestão Escolar')
    ano_lectivo_corrente = models.CharField(max_length=9, blank=True, null=True)
    timezone = models.CharField(max_length=50, default='Africa/Luanda')
    
    # Backup automático
    backup_auto = models.BooleanField(default=False)
    backup_frequencia = models.CharField(max_length=20, choices=[
        ('daily', 'Diário'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensal'),
    ], default='daily')
    manter_backups_dias = models.IntegerField(default=30)
    
    # Email
    smtp_server = models.CharField(max_length=255, blank=True)
    smtp_port = models.IntegerField(default=587)
    smtp_user = models.CharField(max_length=255, blank=True)
    smtp_password = models.CharField(max_length=255, blank=True)
    email_sistema = models.EmailField(blank=True)
    
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return "Configurações do Sistema"
 