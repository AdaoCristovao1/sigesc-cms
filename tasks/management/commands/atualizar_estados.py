from django.core.management.base import BaseCommand
from administracao.models import Aluno
from financeiro.views import atualizar_estado_aluno

class Command(BaseCommand):
    help = "Atualiza estado de todos os alunos (para multas, inadimplência, etc.)"

    def handle(self, *args, **options):
        for aluno in Aluno.objects.all():
            atualizar_estado_aluno(aluno)
        self.stdout.write(self.style.SUCCESS("Estados atualizados com sucesso!"))
