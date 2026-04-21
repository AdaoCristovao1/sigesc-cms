from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('administracao/', include('administracao.urls', namespace='administracao')),
    path('pedagogico/', include('pedagogico.urls', namespace='pedagogico')),
    path('documentos/', include('documentos.urls', namespace='documentos')),
    path('estudante/', include('estudante.urls', namespace='estudante')),
    path('financeiro/', include('financeiro.urls', namespace='financa')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
