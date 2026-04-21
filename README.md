✅ PASSO 3: Configure para iniciar com o Windows
➤ Opção 1: Via Pasta de Inicialização (mais simples)
Pressione Win + R, digite shell:startup e pressione Enter.
Uma pasta vai abrir: C:\Users\SEU_USUARIO\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
Copie o arquivo start_sigesc.bat para dentro dessa pasta.
➡️ Pronto! Toda vez que o Windows iniciar, seu sistema será iniciado automaticamente.

➤ Opção 2: Via Agendador de Tarefas (recomendado para maior controle)
Pressione Win + R, digite taskschd.msc e pressione Enter.
Clique em “Criar Tarefa” no painel direito.
Na aba Geral:
Nome: Iniciar SIGEsc (Nginx + Waitress)
Marque: “Executar com privilégios mais altos”
Na aba Disparadores:
Clique em Novo...
“Iniciar a tarefa:” → Na inicialização
OK
Na aba Ações:
Clique em Novo...
“Ação:” → Iniciar um programa
“Programa/script:” → navegue e selecione seu start_sigesc.bat
“Iniciar em:” → coloque o caminho da pasta do projeto (ex: C:\projectos\sigesc)
OK
Na aba Condições, desmarque:
“Iniciar somente se o computador estiver na rede elétrica”
“Despertar o computador para executar esta tarefa”
Clique em OK.
➡️ Pronto! O sistema iniciará automaticamente com o Windows, mesmo sem login.

✅ PASSO 4 (OPCIONAL): Crie um script para parar o servidor
Crie stop_sigesc.bat:

bat


1
2
3
4
5
@echo off
taskkill /f /im nginx.exe
taskkill /f /im python.exe
echo Servidores Nginx e Django encerrados.
pause
⚠️ Cuidado: Isso mata todos os processos python.exe. Se estiver rodando outros scripts Python, use: 

bat


1
2
wmic process where "commandline like '%server.py%'" delete
taskkill /f /im nginx.exe


PASSO 2: Libere a porta 80 no firewall
No CMD (já como Administrador), execute:

cmd


1
netsh advfirewall firewall add rule name="Nginx Port 80" dir=in action=allow protocol=TCP localport=80
➡️ Deve aparecer: Ok.


{% load static %}
<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <title>Cadastro | Funcionários</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="{% static 'bootstrap/css/bootstrap.min.css' %}" rel="stylesheet">
  <link rel="stylesheet" href="{% static 'css/style.css' %}">
  <link rel="apple-touch-icon" sizes="300x300" href="{% static 'imgs/apple-touch-icon.png' %}">
  <link rel="icon" type="image/png" sizes="32x32" href="{% static 'imgs/favicon-32x32.png' %}">
  <link rel="icon" type="image/png" sizes="16x16" href="{% static 'imgs/favicon-16x16.png' %}">
  <link rel="manifest" href="{% static 'imgs/site.webmanifest' %}">
  
  <!-- Bootstrap Icons -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">

  <style>
    .sidebar{
      overflow-y: auto;
    }
    .badge-falta {
      background-color: #dc3545;
      color: white;
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 12px;
    }
    .mes-selector {
      background: #f8f9fa;
      border-radius: 8px;
      padding: 15px;
      margin-bottom: 20px;
    }
    .calendar-day {
      border: 1px solid #dee2e6;
      padding: 10px;
      height: 100px;
      overflow-y: auto;
    }
    .calendar-day.falta {
      background-color: #ffe6e6;
    }
    .calendar-day-header {
      background: #e9ecef;
      padding: 5px;
      text-align: center;
      font-weight: bold;
    }
    .funcionario-card {
      border: 1px solid #dee2e6;
      border-radius: 8px;
      padding: 15px;
      margin-bottom: 15px;
      transition: all 0.3s;
    }
    .funcionario-card:hover {
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      transform: translateY(-2px);
    }
    .stats-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 10px;
      padding: 20px;
      margin-bottom: 20px;
    }
  </style>
</head>
<body>

  <div class="sidebar" id="sidebar">
    <div class="logo">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-mortarboard-fill" viewBox="0 0 16 16">
        <path d="M8.211 2.047a.5.5 0 0 0-.422 0l-7.5 3.5a.5.5 0 0 0 .025.917l7.5 3a.5.5 0 0 0 .372 0L14 7.14V13a1 1 0 0 0-1 1v2h3v-2a1 1 0 0 0-1-1V6.739l.686-.275a.5.5 0 0 0 .025-.917l-7.5-3.5Z"/>
        <path d="M4.176 9.032a.5.5 0 0 0-.656.327l-.5 1.7a.5.5 0 0 0 .294.605l4.5 1.8a.5.5 0 0 0 .372 0l4.5-1.8a.5.5 0 0 0 .294-.605l-.5-1.7a.5.5 0 0 0-.656-.327L8 10.466 4.176 9.032Z"/>
      </svg>
      SIGEsc
    </div>
    <div class="user-info">
      <svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" fill="currentColor" class="bi bi-person-circle" viewBox="0 0 16 16">
        <path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0"/>
        <path fill-rule="evenodd" d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8m8-7a7 7 0 0 0-5.468 11.37C3.242 11.226 4.805 10 8 10s4.757 1.225 5.468 2.37A7 7 0 0 0 8 1"/>
      </svg>
      <div><strong>Director Geral</strong></div>
      <small>{{usuario.username}}</small>
    </div>
    <a href="{% url 'core:dashboard' %}">Dashboard</a>
    <a href="{% url 'core:usuarios' %}">Usuários</a>
    <a href="{% url 'core:docentes' %}">Docentes</a>
    <a href="{% url 'core:cadastrar_funcionario' %}" class="active">Funcionários</a>
    <a href="{% url 'core:alunos_lista' %}">Alunos</a>
    <a href="{% url 'core:turmas_e_salas' %}">Turmas</a>
    <a href="{% url 'core:classes' %}">Classes</a>
    <a href="{% url 'core:cursos' %}">Cursos</a>
    <a href="{% url 'core:disciplinas' %}">Disciplinas</a>
    <a href="{% url 'core:matriculas' %}">Matrículas</a>
    <a href="{% url 'core:pautas' %}">Pautas</a>
    <a href="{% url 'core:coordenacoes' %}">Coordenações</a>
    <a href="{% url 'financa:financas' %}">Finanças</a>
    <a href="{% url 'financa:relatorios' %}">Relatórios</a>
  </div>

  <div class="main-content">
    <div class="topbar">
      <h5>Sistema Integrado de Gestão Escolar</h5>
      <div class="d-flex align-items-center gap-3">
        <button class="burger" onclick="toggleSidebar()">☰</button>
        <a class="logout btn btn-danger" href="{% url 'core:logout' %}">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-power" viewBox="0 0 16 16">
            <path d="M7.5 1v7h1V1z"/>
            <path d="M3 8.812a5 5 0 0 1 2.578-4.375l-.485-.874A6 6 0 1 0 11 3.616l-.501.865A5 5 0 1 1 3 8.812"/>
          </svg>
          Sair
        </a>
      </div>
    </div>
    <div class="container mt-4">
        <form method="GET" class="row g-3 mt-3 mb-4">
      <div class="col-md-8">
        <input type="text" name="q" class="form-control" placeholder="Pesquise aqui!..." value="{{ request.GET.q }}">
      </div>
      <div class="col-md-4">
        <button type="submit" class="btn btn-primary">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-search" viewBox="0 0 16 16">
            <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001q.044.06.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1 1 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0"/>
            </svg>
            Pesquisar
        </button>
      </div>
    </form>
    <div class="d-flex justify-content-between align-items-center mt-4 mb-2">
      <div>
        <button class="btn btn-outline-primary" onclick="mostrarLista('outros')">Lista de Funcionários</button>
        <button class="btn btn-outline-success" onclick="mostrarLista('alunos')">Novo Funcionário</button>
        <button class="btn btn-outline-warning" onclick="mostrarLista('faltas')">
          <i class="bi bi-calendar-x"></i> Gestão de Faltas
        </button>
      </div>
    </div>

    <!-- Modal para gerar folha de salário -->
    <div class="modal fade" id="gerarFolhaModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-warning text-dark">
                    <h5 class="modal-title">
                        <i class="bi bi-cash-stack"></i> Gerar Folha de Salário
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form id="formFolhaSalario">
                    {% csrf_token %}
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle"></i> Selecione o mês para gerar a folha de salário com cálculo de descontos por faltas.
                        </div>
                        
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label">Mês</label>
                                <select name="mes" class="form-select" required>
                                    <option value="">Selecione o mês</option>
                                    <option value="1">Janeiro</option>
                                    <option value="2">Fevereiro</option>
                                    <option value="3">Março</option>
                                    <option value="4">Abril</option>
                                    <option value="5">Maio</option>
                                    <option value="6">Junho</option>
                                    <option value="7">Julho</option>
                                    <option value="8">Agosto</option>
                                    <option value="9">Setembro</option>
                                    <option value="10">Outubro</option>
                                    <option value="11">Novembro</option>
                                    <option value="12">Dezembro</option>
                                </select>
                            </div>
                        </div>
                        
                        <!-- Resumo do desconto ativo -->
                        <div class="card mt-3">
                            <div class="card-body">
                                <h6 class="card-title">Configuração Atual de Descontos</h6>
                                {% if desconto_ativo %}
                                    <p class="mb-1"><strong>Valor por falta:</strong> Kz {{ desconto_ativo.valor_desconto }}</p>
                                    <small class="text-muted">Este valor será aplicado a cada falta registrada.</small>
                                {% else %}
                                    <div class="alert alert-warning">
                                        <i class="bi bi-exclamation-triangle"></i>
                                        Nenhum valor de desconto configurado. Configure um valor antes de gerar a folha.
                                    </div>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="submit" class="btn btn-warning" id="btnGerarFolha">
                            <i class="bi bi-file-earmark-pdf"></i> Gerar Folha
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- LISTA DE FUNCIONÁRIOS -->
    <div id="lista-outros" class="table-responsive">
      <h2 class="page-title">Lista de Funcionários</h2>
      {% if messages %}
            <div class="mt-3">
            {% for message in messages %}
                <div class="alert alert-success">{{ message }}</div>
            {% endfor %}
            </div>
        {% endif %}
      <table class="table table-bordered table-striped table-hover" style="font-size: 13px;">
        <thead class="table-primary">
          <tr>
            <th>Ordem</th>
            <th>Nome Completo</th>
            <th>Nome de Usuário</th>
            <th>Identidade</th>
            <th>Gênero</th>
            <th>Função</th>
            <th>Telefone</th>
            <th>Salário</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {% for funcionario in funcionarios %}
          <tr>
            <td>{{ forloop.counter }}</td>
            <td>{{ funcionario.nome }}</td>
            <td>{{ funcionario.usuario.username }}</td>
            <td>{{ funcionario.bi }}</td>
            <td>{{ funcionario.get_genero_display }}</td>
            <td>{{ funcionario.funcao }}</td>
            <td>{{ funcionario.telefone }}</td>
            <td>{{ funcionario.salario }}</td>
            <td>
              <div class="d-flex justify-content-center gap-2">
                  <button class="btn btn-light border d-flex align-items-center gap-2 px-3 py-1"
                          onclick="openModalEditar(this)"
                          data-id="{{ funcionario.id }}"
                          data-nome="{{ funcionario.nome }}"
                          data-bi="{{ funcionario.bi }}"
                          data-genero="{{ funcionario.genero }}"
                          data-funcao="{{ funcionario.funcao }}"
                          data-telefone="{{ funcionario.telefone }}"
                          data-salario="{{ funcionario.salario }}"
                          title="Editar funcionário">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#0d6efd" viewBox="0 0 16 16">
                          <path d="M12.854.146a.5.5 0 0 0-.707 0L10.5 1.793 14.207 5.5l1.647-1.646a.5.5 0 0 0 0-.708l-3-3zm.646 6.061L9.793 2.5 3.293 9H3.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.207l6.5-6.5zm-7.468 7.468A.5.5 0 0 1 6 13.5V13h-.5a.5.5 0 0 1-.5-.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.5-.5V10h-.5a.499.499 0 0 1-.175-.032l-.179.178a.5.5 0 0 0-.11.168l-2 5a.5.5 0 0 0 .65.65l5-2a.5.5 0 0 0 .168-.11l.178-.178z"/>
                      </svg>
                      <span class="text-primary fw-medium">Editar</span>
                  </button>
                  
                  <button class="btn btn-light border d-flex align-items-center gap-2 px-3 py-1"
                          onclick="openDeleteModal('{{ funcionario.id }}', '{{ funcionario.nome }}')"
                          title="Eliminar funcionário">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#dc3545" viewBox="0 0 16 16">
                          <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                          <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                      </svg>
                      <span class="text-danger fw-medium">Eliminar</span>
                  </button>
              </div>
          </td>
          </tr>
          {% empty %}
          <tr><td colspan="7" class="text-center">Nenhum Funcionário encontrado.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    
    <!-- FORMULÁRIO DE CADASTRO -->
    <div id="lista-alunos" class="table-responsive d-none">
      <div class="container mt-4">
        <h2>Formulário para Cadastro de Funcionários</h2>

        <form method="POST" action="">
            {% csrf_token %}
            <div class="mb-3">
            <label for="nome" class="form-label">Nome Completo:</label>
            <input type="text" class="form-control" id="nome" name="nome" required>
            </div>

            <div class="mb-3">
            <label for="bilhete" class="form-label">Bilhete de Identidade:</label>
            <input type="text" class="form-control" id="bilhete" name="bilhete" required>
            </div>

            <div class="mb-3">
            <label class="form-label">Gênero:</label><br>
            <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="genero" id="genero_m" value="M" required>
                <label class="form-check-label" for="genero_m">Masculino</label>
            </div>
            <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="genero" id="genero_f" value="F">
                <label class="form-check-label" for="genero_f">Feminino</label>
            </div>
            </div>

            <div class="mb-3">
                <label for="funcao" class="form-label">Função:</label>
                <select class="form-select" id="funcao" name="funcao" required>
                    <option value="">Selecione uma função</option>
                    <option value="diretor_geral">Diretor Geral</option>
                    <option value="diretor_pedagogico">Diretor Pedagógico</option>
                    <option value="diretor_admin">Diretor Administrativo</option>
                    <option value="coordenador_turno">Coordenador de Turno</option>
                    <option value="coordenador_turma">Coordenador de Turma</option>
                    <option value="coordenador_disc">Coordenador de Disciplina</option>
                    <option value="secretario_geral">Secretário Geral</option>
                    <option value="secretario_admin">Secretário Administrativo</option>
                    <option value="secretario_ped">Secretário Pedagógico</option>
                    <option value="professor">Professor</option>
                </select>
            </div>

            <div class="mb-3">
              <label for="telefone" class="form-label">Telefone:</label>
              <input type="text" class="form-control" id="telefone" name="telefone" required>
            </div>

            <div class="mb-3">
              <label for="salario" class="form-label">Salário a receber:</label>
              <input type="text" class="form-control" id="salario" name="salario" required>
            </div>

            <button type="submit" class="btn btn-primary"
              onclick="if (this.form.checkValidity()) {
                this.disabled = true; this.form.submit();
              } else { 
                this.form.reportValidity(); return false; 
              }">Cadastrar Funcionário</button>
        </form>
        <br><br>
    </div>
    </div>
    
    <!-- GESTÃO DE FALTAS -->
    <div id="lista-faltas" class="d-none">
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="page-title">
          <i class="bi bi-calendar-x me-2"></i>Gestão de Faltas
        </h2>
        <button class="btn btn-primary" onclick="carregarFaltas()">
          <i class="bi bi-arrow-clockwise"></i> Atualizar
        </button>
      </div>
      
      <!-- Filtros e Controles -->
      <div class="card mb-4">
        <div class="card-body">
          <div class="row g-3">
            <div class="col-md-4">
              <label class="form-label">Ano Lectivo</label>
              <select class="form-select" id="anoLectivoSelect">
                {% for ano in anos_lectivos %}
                <option value="{{ ano.id }}" {% if ano.ativo %}selected{% endif %}>{{ ano.nome }}</option>
                {% endfor %}
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label">Mês</label>
              <select class="form-select" id="mesSelect" onchange="carregarFaltas()">
                <option value="1">Janeiro</option>
                <option value="2">Fevereiro</option>
                <option value="3">Março</option>
                <option value="4">Abril</option>
                <option value="5">Maio</option>
                <option value="6">Junho</option>
                <option value="7">Julho</option>
                <option value="8">Agosto</option>
                <option value="9">Setembro</option>
                <option value="10">Outubro</option>
                <option value="11">Novembro</option>
                <option value="12">Dezembro</option>
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label">Funcionário</label>
              <select class="form-select" id="funcionarioSelect" onchange="filtrarFuncionarios()">
                <option value="">Todos os Funcionários</option>
                {% for funcionario in funcionarios %}
                <option value="{{ funcionario.id }}">{{ funcionario.nome }} - {{ funcionario.funcao }}</option>
                {% endfor %}
              </select>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Estatísticas -->
      <div class="row mb-4">
        <div class="col-md-4">
          <div class="stats-card">
            <h6><i class="bi bi-people"></i> Total de Funcionários</h6>
            <h3 id="totalFuncionarios">{{ funcionarios.count }}</h3>
          </div>
        </div>
        <div class="col-md-4">
          <div class="stats-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h6><i class="bi bi-calendar-x"></i> Faltas no Mês</h6>
            <h3 id="totalFaltasMes">0</h3>
          </div>
        </div>
        <div class="col-md-4">
          <div class="stats-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h6><i class="bi bi-cash"></i> Desconto Estimado</h6>
            <h3 id="descontoTotal">Kz 0</h3>
          </div>
        </div>
      </div>
      
      <!-- Lista de Funcionários com Faltas -->
      <div class="row">
        <div class="col-md-8">
          <h5>Funcionários com Faltas</h5>
          <div id="listaFuncionariosFaltas">
            <!-- Aqui serão carregados os funcionários via AJAX -->
            {% for funcionario in funcionarios %}
            <div class="funcionario-card" data-id="{{ funcionario.id }}">
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <h6 class="mb-1">{{ funcionario.nome }}</h6>
                  <small class="text-muted">{{ funcionario.funcao }} | {{ funcionario.get_genero_display }}</small>
                </div>
                <div class="d-flex gap-2">
                  <button class="btn btn-sm btn-outline-warning" onclick="abrirModalRegistrarFalta({{ funcionario.id }}, '{{ funcionario.nome }}')">
                    <i class="bi bi-plus-circle"></i> Registrar Falta
                  </button>
                  <button class="btn btn-sm btn-outline-info" onclick="visualizarFaltasFuncionario({{ funcionario.id }})">
                    <i class="bi bi-eye"></i> Ver Faltas
                  </button>
                </div>
              </div>
              <div class="mt-2">
                <small>Faltas no mês: <span class="badge-falta" id="faltas-{{ funcionario.id }}">0</span></small>
              </div>
            </div>
            {% endfor %}
          </div>
        </div>
        
        <!-- Calendário do Mês -->
        <div class="col-md-4">
          <h5>Calendário do Mês</h5>
          <div class="mes-selector">
            <h6 id="mesAtual">Janeiro 2024</h6>
            <div class="row" id="calendarioMes">
              <!-- Calendário será gerado dinamicamente -->
            </div>
          </div>
          
          <!-- Resumo de Faltas -->
          <div class="card">
            <div class="card-body">
              <h6 class="card-title">Resumo de Faltas</h6>
              <div id="resumoFaltas">
                <p class="text-muted">Selecione um funcionário para ver o resumo de faltas.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
  </div>

  <!-- Modal de Edição de Funcionário -->
  <div class="modal fade" id="confirmacaoModal" tabindex="-1" aria-labelledby="confirmacaoModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <form method="POST" action="{% url 'core:confirmar_acao_funcionario' %}">
        {% csrf_token %}

        <!-- Campos ocultos para o ID do funcionário e tipo de ação -->
        <input type="hidden" name="funcionario_id" id="funcionarioIdInput">
        <input type="hidden" name="acao" id="acaoInput">

        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="confirmacaoModalLabel">Editar Funcionário</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
          </div>

          <div class="modal-body">
            <!-- Nome -->
            <div class="mb-3">
              <label for="nome" class="form-label">Nome Completo:</label>
              <input type="text" class="form-control" id="modal_nome" name="nome" required>
            </div>

            <!-- BI -->
            <div class="mb-3">
              <label for="bilhete" class="form-label">Bilhete de Identidade:</label>
              <input type="text" class="form-control" id="modal_bilhete" name="bilhete" required>
            </div>

            <!-- Gênero -->
            <div class="mb-3">
              <label class="form-label">Gênero:</label><br>
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="genero" id="modal_genero_m" value="M" required>
                <label class="form-check-label" for="genero_m">Masculino</label>
              </div>
              <div class="form-check form-check-inline">
                <input class="form-check-input" type="radio" name="genero" id="modal_genero_f" value="F">
                <label class="form-check-label" for="genero_f">Feminino</label>
              </div>
            </div>

            <!-- Função -->
            <div class="mb-3">
              <label for="funcao" class="form-label">Função:</label>
              <select class="form-select" id="modal_funcao" name="funcao" required>
                <option value="">Selecione uma função</option>
                <option value="diretor_geral">Diretor Geral</option>
                <option value="diretor_pedagogico">Diretor Pedagógico</option>
                <option value="diretor_admin">Diretor Administrativo</option>
                <option value="coordenador_turno">Coordenador de Turno</option>
                <option value="coordenador_turma">Coordenador de Turma</option>
                <option value="coordenador_disc">Coordenador de Disciplina</option>
                <option value="secretario_geral">Secretário Geral</option>
                <option value="secretario_admin">Secretário Administrativo</option>
                <option value="secretario_ped">Secretário Pedagógico</option>
                <option value="professor">Professor</option>
              </select>
            </div>

            <!-- Telefone -->
            <div class="mb-3">
              <label for="telefone" class="form-label">Telefone:</label>
              <input type="text" class="form-control" id="modal_telefone" name="telefone" required>
            </div>

            <!-- Salário -->
            <div class="mb-3">
              <label for="salario" class="form-label">Salário a Receber:</label>
              <input type="text" class="form-control" id="modal_salario" name="salario" required>
            </div>

            <!-- Confirmação de Senha -->
            <div class="mb-3">
              <label for="senha" class="form-label">Digite a chave Master:</label>
              <input type="password" class="form-control" name="senha" required>
            </div>
            <p class="text-muted">Digite sua senha para confirmar a edição deste funcionário e do usuário correspondente.</p>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            <button type="submit" class="btn btn-primary">Confirmar Edição</button>
          </div>
        </div>
      </form>
    </div>
  </div>

  <!-- Modal Exclusão -->
  <div class="modal fade" id="deleteModal" tabindex="-1" aria-labelledby="deleteModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <form method="POST" action="{% url 'core:excluir_funcionario' %}">
        {% csrf_token %}
        <input type="hidden" name="funcionario_id" id="deleteFuncionarioId">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="deleteModalLabel">Confirmar Exclusão</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fechar"></button>
          </div>
          <div class="modal-body">
            <p>Tem certeza de que deseja apagar o funcionário <strong id="funcionarioNome"></strong>?</p>
            <p>O usuário correspondente será: <strong id="emailReconstruido" class="text-primary"></strong></p>
            <p class="text-danger">Essa ação é irreversível.</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            <button type="submit" class="btn btn-danger">Apagar</button>
          </div>
        </div>
      </form>
    </div>
  </div>

  <!-- Modal Registrar Falta -->
  <div class="modal fade" id="registrarFaltaModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header bg-warning text-dark">
          <h5 class="modal-title">
            <i class="bi bi-calendar-plus"></i> Registrar Falta
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <form method="POST" action="{% url 'documentos:registrar_falta_funcionario' %}">
          {% csrf_token %}
          <div class="modal-body">
            <input type="hidden" name="funcionario_id" id="modalFuncionarioId">
            
            <div class="mb-3">
              <label class="form-label">Funcionário</label>
              <input type="text" class="form-control" id="modalFuncionarioNome" readonly>
            </div>
            
            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label">Mês</label>
                <select name="mes" class="form-select" id="modalMes" required>
                  <option value="">Selecione o mês</option>
                  <option value="1">Janeiro</option>
                  <option value="2">Fevereiro</option>
                  <option value="3">Março</option>
                  <option value="4">Abril</option>
                  <option value="5">Maio</option>
                  <option value="6">Junho</option>
                  <option value="7">Julho</option>
                  <option value="8">Agosto</option>
                  <option value="9">Setembro</option>
                  <option value="10">Outubro</option>
                  <option value="11">Novembro</option>
                  <option value="12">Dezembro</option>
                </select>
              </div>
              <div class="col-md-6">
                <label class="form-label">Dia</label>
                <select name="dia" class="form-select" id="modalDia" required>
                  <option value="">Selecione o dia</option>
                  {% for i in "x"|rjust:"31" %}
                  <option value="{{ forloop.counter }}">{{ forloop.counter }}</option>
                  {% endfor %}
                </select>
              </div>
            </div>
            
            <div class="alert alert-info mt-3">
              <i class="bi bi-info-circle"></i> A falta será registrada para o ano lectivo atual.
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            <button type="submit" class="btn btn-warning">Registrar Falta</button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- Modal Visualizar Faltas -->
  <div class="modal fade" id="visualizarFaltasModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header bg-info text-dark">
          <h5 class="modal-title">
            <i class="bi bi-calendar-check"></i> Histórico de Faltas
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <h6 id="modalFuncionarioTitulo"></h6>
          <div id="historicoFaltas">
            <!-- Histórico será carregado via AJAX -->
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal Simples de Confirmação -->
  <div class="modal fade" id="removerFaltaModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header bg-danger text-white">
          <h5 class="modal-title">
            <i class="bi bi-exclamation-triangle"></i> Confirmar Remoção
          </h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <p id="faltaInfoText"></p>
          <p class="text-danger"><small>Esta ação não pode ser desfeita.</small></p>
          
          <!-- Formulário POST simples -->
          <form id="formRemoverFalta" method="POST" action="">
            {% csrf_token %}
            <input type="hidden" name="falta_id" id="inputFaltaId">
            <div class="d-grid gap-2">
              <button type="submit" class="btn btn-danger">
                <i class="bi bi-trash"></i> Confirmar Remoção
              </button>
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                Cancelar
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>

  <script>
    function mostrarLista(tipo) {
      const listaAlunos = document.getElementById('lista-alunos');
      const listaOutros = document.getElementById('lista-outros');
      const listaFaltas = document.getElementById('lista-faltas');

      // Esconder todas as seções
      listaAlunos.classList.add('d-none');
      listaOutros.classList.add('d-none');
      listaFaltas.classList.add('d-none');

      // Mostrar apenas a seção selecionada
      if (tipo === 'alunos') {
        listaAlunos.classList.remove('d-none');
      } else if (tipo === 'faltas') {
        listaFaltas.classList.remove('d-none');
        carregarFaltas();
      } else {
        listaOutros.classList.remove('d-none');
      }
    }

    function abrirModalConfirmacao(acao, funcionarioId) {
      document.getElementById('funcionarioIdInput').value = funcionarioId;
      document.getElementById('acaoInput').value = acao;
      const modal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
      modal.show();
    }

    function removerAcentos(texto) {
      return texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    }

    function openDeleteModal(funcionarioId, nomeCompleto) {
      const nomes = removerAcentos(nomeCompleto.toLowerCase()).split(" ");
      const primeiro = nomes[0];
      const ultimo = nomes.length > 1 ? nomes[nomes.length - 1] : primeiro;
      const email = `${primeiro}${ultimo}@sigesc.co.ao`;

      document.getElementById('deleteFuncionarioId').value = funcionarioId;
      document.getElementById('funcionarioNome').textContent = nomeCompleto;
      document.getElementById('emailReconstruido').textContent = email;

      const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
      modal.show();
    }

    function openModalEditar(button) {
      const id = button.getAttribute('data-id');
      const nome = button.getAttribute('data-nome');
      const bi = button.getAttribute('data-bi');
      const genero = button.getAttribute('data-genero');
      const funcao = button.getAttribute('data-funcao');
      const telefone = button.getAttribute('data-telefone');
      const salario = button.getAttribute('data-salario');

      document.getElementById('funcionarioIdInput').value = id;
      document.getElementById('modal_nome').value = nome;
      document.getElementById('modal_bilhete').value = bi;
      document.getElementById('modal_telefone').value = telefone;
      document.getElementById('modal_funcao').value = funcao;
      document.getElementById('modal_salario').value = salario;

      // Selecionar o rádio do gênero
      document.getElementById('modal_genero_m').checked = genero === 'M';
      document.getElementById('modal_genero_f').checked = genero === 'F';

      // Modo de edição
      document.getElementById('acaoInput').value = 'editar';

      // Exibe a modal
      const modal = new bootstrap.Modal(document.getElementById('confirmacaoModal'));
      modal.show();
    }

    // FUNÇÕES PARA GESTÃO DE FALTAS
    function carregarFaltas() {
      const anoLectivoId = document.getElementById('anoLectivoSelect').value;
      const mes = document.getElementById('mesSelect').value;
      
      // Atualizar título do mês
      const meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'];
      const anoAtual = new Date().getFullYear();
      document.getElementById('mesAtual').textContent = `${meses[mes-1]} ${anoAtual}`;
      
      // Gerar calendário
      gerarCalendario(mes, anoAtual);
      
      // Carregar estatísticas
      fetch(`/documentos/api/faltas/estatisticas/?ano_lectivo=${anoLectivoId}&mes=${mes}`)
        .then(response => response.json())
        .then(data => {
          document.getElementById('totalFaltasMes').textContent = data.total_faltas;
          document.getElementById('descontoTotal').textContent = `Kz ${data.desconto_total}`;
          
          // Atualizar contadores por funcionário
          data.faltas_por_funcionario.forEach(item => {
            const badge = document.getElementById(`faltas-${item.funcionario_id}`);
            if (badge) {
              badge.textContent = item.total_faltas;
            }
          });
        });
    }

    function gerarCalendario(mes, ano) {
      const calendarioDiv = document.getElementById('calendarioMes');
      calendarioDiv.innerHTML = '';
      
      const data = new Date(ano, mes - 1, 1);
      const diasNoMes = new Date(ano, mes, 0).getDate();
      const primeiroDia = data.getDay();
      
      // Dias da semana
      const diasSemana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
      
      // Cabeçalho dos dias
      const headerRow = document.createElement('div');
      headerRow.className = 'row';
      diasSemana.forEach(dia => {
        const col = document.createElement('div');
        col.className = 'col calendar-day-header';
        col.textContent = dia;
        headerRow.appendChild(col);
      });
      calendarioDiv.appendChild(headerRow);
      
      // Dias do mês
      let row = document.createElement('div');
      row.className = 'row';
      
      // Espaços vazios no início
      for (let i = 0; i < primeiroDia; i++) {
        const col = document.createElement('div');
        col.className = 'col calendar-day';
        row.appendChild(col);
      }
      
      // Dias do mês
      for (let dia = 1; dia <= diasNoMes; dia++) {
        if ((primeiroDia + dia - 1) % 7 === 0 && dia > 1) {
          calendarioDiv.appendChild(row);
          row = document.createElement('div');
          row.className = 'row';
        }
        
        const col = document.createElement('div');
        col.className = 'col calendar-day';
        col.innerHTML = `<strong>${dia}</strong>`;
        col.setAttribute('data-dia', dia);
        col.onclick = function() { selecionarDia(this, dia); };
        row.appendChild(col);
      }
      
      calendarioDiv.appendChild(row);
    }

    function selecionarDia(elemento, dia) {
      // Remove seleção anterior
      document.querySelectorAll('.calendar-day').forEach(el => {
        el.classList.remove('bg-primary', 'text-white');
      });
      
      // Adiciona seleção ao dia clicado
      elemento.classList.add('bg-primary', 'text-white');
      
      // Aqui você pode carregar as faltas do dia selecionado
      const mes = document.getElementById('mesSelect').value;
      const ano = new Date().getFullYear();
      console.log(`Dia selecionado: ${dia}/${mes}/${ano}`);
    }

    function abrirModalRegistrarFalta(funcionarioId, nomeFuncionario) {
      document.getElementById('modalFuncionarioId').value = funcionarioId;
      document.getElementById('modalFuncionarioNome').value = nomeFuncionario;
      
      // Definir o mês atual no modal
      const mesAtual = document.getElementById('mesSelect').value;
      document.getElementById('modalMes').value = mesAtual;
      
      const modal = new bootstrap.Modal(document.getElementById('registrarFaltaModal'));
      modal.show();
    }

    function visualizarFaltasFuncionario(funcionarioId) {
        const anoLectivoId = document.getElementById('anoLectivoSelect').value;
        
        fetch(`/documentos/api/faltas/funcionario/${funcionarioId}/?ano_lectivo=${anoLectivoId}`)
          .then(response => response.json())
          .then(data => {
            const funcionario = data.funcionario;
            const faltas = data.faltas;
            
            document.getElementById('modalFuncionarioTitulo').textContent = 
              `Faltas de ${funcionario.nome} - ${funcionario.funcao}`;
            
            const historicoDiv = document.getElementById('historicoFaltas');
            historicoDiv.innerHTML = '';
            
            if (faltas.length === 0) {
              historicoDiv.innerHTML = '<p class="text-muted">Nenhuma falta registrada.</p>';
            } else {
              const table = document.createElement('table');
              table.className = 'table table-striped';
              table.innerHTML = `
                <thead>
                  <tr>
                    <th>Data</th>
                    <th>Mês</th>
                    <th>Ano Lectivo</th>
                    <th>Registrado por</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  ${faltas.map(falta => `
                    <tr id="falta-row-${falta.id}">
                      <td>${falta.dia}/${falta.mes}</td>
                      <td>${falta.mes_nome}</td>
                      <td>${falta.ano_lectivo_nome}</td>
                      <td>${falta.registrado_por_nome || falta.registrado_por}</td>
                      <td>
                        <a href="/documentos/faltas/remover/${falta.id}/" 
                          class="btn btn-sm btn-outline-danger"
                          onclick="return confirm('Tem certeza que deseja remover esta falta?');">
                          <i class="bi bi-trash"></i> Remover
                        </a>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              `;
              historicoDiv.appendChild(table);
            }
            
            const modal = new bootstrap.Modal(document.getElementById('visualizarFaltasModal'));
            modal.show();
          })
          .catch(error => {
            console.error('Erro ao carregar faltas:', error);
            alert('Erro ao carregar o histórico de faltas.');
          });
    }
    // Variáveis globais para controle
    let faltaAtualParaRemover = null;
    let funcionarioIdAtual = null;

    function abrirModalRemoverFalta(faltaId, dia, mes, anoLectivoNome, funcionarioId) {
        faltaAtualParaRemover = faltaId;
        funcionarioIdAtual = funcionarioId;
        
        // Atualizar informações no modal
        document.getElementById('faltaDataInfo').textContent = `${dia}/${mes} (${anoLectivoNome})`;
        document.getElementById('removerFaltaMessage').innerHTML = '';
        
        // Resetar o botão de confirmação
        const btn = document.getElementById('btnConfirmarRemoverFalta');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm d-none" id="removerSpinner"></span> Remover Falta';
        }
        
        const spinner = document.getElementById('removerSpinner');
        if (spinner) {
            spinner.classList.add('d-none');
        }
        
        // Mostrar o modal
        const modal = new bootstrap.Modal(document.getElementById('removerFaltaModal'));
        modal.show();
    }

    function removerFalta() {
        if (!faltaAtualParaRemover) {
            console.error('Nenhuma falta selecionada para remover');
            return;
        }
        
        const btn = document.getElementById('btnConfirmarRemoverFalta');
        const messageDiv = document.getElementById('removerFaltaMessage');
        
        if (!btn) {
            console.error('Botão de confirmação não encontrado');
            return;
        }
        
        // Mostrar spinner e desabilitar botão
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" id="removerSpinner"></span> Removendo...';
        
        messageDiv.innerHTML = '';
        
        // Enviar requisição para remover
        fetch(`/documentos/api/faltas/remover/${faltaAtualParaRemover}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Sucesso - mostrar mensagem
                messageDiv.innerHTML = `
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        <i class="bi bi-check-circle"></i> ${data.message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                `;
                
                // Remover a linha da tabela se existir
                const row = document.getElementById(`falta-row-${faltaAtualParaRemover}`);
                if (row) {
                    row.style.opacity = '0.5';
                    setTimeout(() => {
                        row.remove();
                        // Verificar se ainda há linhas na tabela
                        const tbody = row.parentElement;
                        if (tbody && tbody.children.length === 0) {
                            const table = tbody.parentElement;
                            if (table) {
                                table.innerHTML = '<p class="text-muted p-3">Nenhuma falta registrada.</p>';
                            }
                        }
                    }, 500);
                }
                
                // Atualizar estatísticas globais
                carregarFaltas();
                
                // Atualizar contador do funcionário específico
                if (funcionarioIdAtual) {
                    const badge = document.getElementById(`faltas-${funcionarioIdAtual}`);
                    if (badge) {
                        const currentFaltas = parseInt(badge.textContent) || 0;
                        badge.textContent = Math.max(0, currentFaltas - 1);
                    }
                }
                
                // Fechar modal após 3 segundos
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('removerFaltaModal'));
                    if (modal) {
                        modal.hide();
                    }
                    
                    // Recarregar as faltas do funcionário se o modal de histórico ainda estiver aberto
                    if (funcionarioIdAtual) {
                        const historicoModal = document.getElementById('visualizarFaltasModal');
                        const bsModal = bootstrap.Modal.getInstance(historicoModal);
                        if (bsModal && bsModal._isShown) {
                            visualizarFaltasFuncionario(funcionarioIdAtual);
                        }
                    }
                }, 3000);
                
            } else {
                // Erro do servidor
                messageDiv.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        <i class="bi bi-exclamation-triangle"></i> ${data.message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                `;
                
                // Reabilitar botão
                btn.disabled = false;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm d-none" id="removerSpinner"></span> Remover Falta';
            }
        })
        .catch(error => {
            console.error('Erro ao remover falta:', error);
            messageDiv.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <i class="bi bi-exclamation-triangle"></i> Erro de conexão. Verifique sua internet e tente novamente.
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            
            // Reabilitar botão
            btn.disabled = false;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm d-none" id="removerSpinner"></span> Remover Falta';
        });
    }

    // Função auxiliar para obter token CSRF
    function getCsrfToken() {
        const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfTokenElement ? csrfTokenElement.value : '';
    }

    document.addEventListener('DOMContentLoaded', function() {
        // Configurar evento do botão de confirmação usando event delegation
        document.addEventListener('click', function(e) {
            if (e.target && e.target.id === 'btnConfirmarRemoverFalta') {
                removerFalta();
            }
        });
        
        // Limpar dados ao fechar modal
        const removerFaltaModal = document.getElementById('removerFaltaModal');
        if (removerFaltaModal) {
            removerFaltaModal.addEventListener('hidden.bs.modal', function() {
                faltaAtualParaRemover = null;
                funcionarioIdAtual = null;
                document.getElementById('removerFaltaMessage').innerHTML = '';
                const btn = document.getElementById('btnConfirmarRemoverFalta');
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<span class="spinner-border spinner-border-sm d-none" id="removerSpinner"></span> Remover Falta';
                }
                const spinner = document.getElementById('removerSpinner');
                if (spinner) {
                    spinner.classList.add('d-none');
                }
            });
        }
        
        // Também adicionar evento para quando o modal é mostrado
        if (removerFaltaModal) {
            removerFaltaModal.addEventListener('show.bs.modal', function() {
                // Resetar estado do botão
                const btn = document.getElementById('btnConfirmarRemoverFalta');
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<span class="spinner-border spinner-border-sm d-none" id="removerSpinner"></span> Remover Falta';
                }
                document.getElementById('removerFaltaMessage').innerHTML = '';
            });
        }
    });

    function filtrarFuncionarios() {
      const funcionarioId = document.getElementById('funcionarioSelect').value;
      const cards = document.querySelectorAll('.funcionario-card');
      
      cards.forEach(card => {
        if (funcionarioId === '' || card.getAttribute('data-id') === funcionarioId) {
          card.style.display = 'block';
        } else {
          card.style.display = 'none';
        }
      });
    }

    // Inicializar quando a página carregar
    document.addEventListener('DOMContentLoaded', function() {
      // Definir mês atual no select
      const mesAtual = new Date().getMonth() + 1;
      document.getElementById('mesSelect').value = mesAtual;
      
      // Inicializar tooltips
      const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
      tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
      });
    });

    function toggleSidebar() {
      document.getElementById("sidebar").classList.toggle("active");
    }
  </script>
  <script src="{% static 'bootstrap/js/bootstrap.bundle.min.js' %}"></script>
</body>
</html>


def faltas_funcionario(request, funcionario_id):
    ano_lectivo_id = request.GET.get('ano_lectivo')

    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    faltas = FaltaFuncionario.objects.filter(funcionario=funcionario)

    if ano_lectivo_id:
        faltas = faltas.filter(ano_lectivo_id=ano_lectivo_id)

    faltas_data = faltas.order_by(
        '-ano_lectivo__ano',
        '-mes',
        '-dia'
    ).values(
        'id',
        'dia',
        'mes',
        ano_lectivo_nome=F('ano_lectivo__ano'),
        registrado_por_nome=F('registrado_por__username')
    )
    meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    faltas_list = []
    for falta in faltas_data:
        falta['mes_nome'] = meses[falta['mes'] - 1] if 1 <= falta['mes'] <= 12 else ''
        faltas_list.append(falta)

    return JsonResponse({
        'funcionario': {
            'id': funcionario.id,
            'nome': funcionario.nome,
            'funcao': funcionario.funcao,
        },
        'faltas': faltas_list
    })
    @login_required
def remover_falta_funcionario(request, falta_id):
    """View SUPER SIMPLES para remover falta"""
    
    try:
        # Buscar a falta
        falta = get_object_or_404(FaltaFuncionario, id=falta_id)
        
        # Armazenar info do funcionário para redirecionar
        funcionario_id = falta.funcionario.id
        
        # Remover
        falta.delete()
        
    except Exception as e:
        # Mensagem de erro
        messages.error(request, f'❌ Erro ao remover falta: {str(e)}')
    
    # Sempre redireciona de volta
    return redirect('core:cadastrar_funcionario')
