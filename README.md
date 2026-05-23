
 "Componente Sócio-Cultural": [],
    "Componente Científica": [],
    "Componente Técnica, Tecnológica e Prática": []

{% load static %}
<!DOCTYPE html>
<html lang="pt">
<head>
<link href="{% static 'bootstrap/css/bootstrap.min.css' %}" rel="stylesheet">
<style>
@media print {
  .no-print { display: none; }
  body {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    margin: 0.5cm;
  }
  @page {
    margin: 0.5cm;
    size: A4;
  }
}

body {
  font-family: "Times New Roman", serif;
  margin: 0.8cm;
  font-size: 13px;
  line-height: 1.4;
  color: #000;
}

.header {
  text-align: center;
  margin-bottom: 20px;
}

.header h1 {
  font-size: 13pt;
  font-weight: bold;
  margin: 0;
  text-transform: uppercase;
}

.header h2 {
  font-size: 12pt;
  font-weight: bold;
  margin: 2px 0;
  text-transform: uppercase;
}

.header h3 {
  font-size: 11pt;
  font-weight: bold;
  margin: 15px 0 5px 0;
  text-transform: uppercase;
}

.titulo-certificado {
  margin: 15px 0;
  text-align: center;
  font-size: 15pt;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.texto-certificado {
  text-align: justify;
  line-height: 1.5;
  margin-bottom: 12px;
  font-size: 12.5px;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 11px;
}

table, th, td {
  border: 1px solid #000;
}

th {
  text-align: center;
  padding: 5px 2px;
  font-weight: bold;
  font-size: 11px;
  text-transform: uppercase;
}

td {
  padding: 4px 4px;
  text-align: center;
  vertical-align: middle;
}

.text-left {
  text-align: left;
}

.categoria-row {
  font-weight: bold;
  text-transform: uppercase;
  background-color: #fff;
}

.categoria-row td {
  text-align: left;
  padding-left: 5px;
}

.media-geral-row {
  font-weight: bold;
  text-transform: uppercase;
}

.local-data {
  text-align: center;
  margin-top: 25px;
  font-weight: bold;
  font-size: 13px;
}

.assinaturas-container {
  margin-top: 30px;
  display: flex;
  justify-content: space-between;
  padding: 0 50px;
}

.assinatura-box {
  text-align: center;
  width: 40%;
  font-size: 12px;
}

.assinatura-linha {
  margin-top: 40px;
  border-top: 1px solid #000;
  display: inline-block;
  width: 100%;
}
</style>
</head>

<body>

<div class="no-print mb-3">
  <button class="btn btn-primary" onclick="window.print()">Imprimir Certificado</button>
</div>

<div class="header">
  <img src="{% static 'imagens/insignia_angola.png' %}" alt="Insígnia" style="height: 75px; margin-bottom: 10px;">
  <h1>República de Angola</h1>
  <h2>Ministério da Educação</h2>
  <h3>Ensino Secundário Geral</h3>
</div>

<div class="titulo-certificado">Certificado</div>

<p class="texto-certificado">
  <strong>{{ diretor.nome }}</strong>, Directora do <strong>{{ escola.nome }}</strong>, criado sob Decreto Executivo nº 449/15 de 18 de Junho, certifica que <strong>{{ aluno.nome_completo }}</strong>, filho (a) de <strong>{{ aluno.nome_pai }}</strong> e de <strong>{{ aluno.nome_mae }}</strong>, natural de <strong>{{ aluno.naturalidade }}</strong>, Município de <strong>{{ aluno.municipio }}</strong>, Província de <strong>{{ aluno.provincia }}</strong>, nascido (a) aos <strong>{{ aluno.data_nascimento|date:"d/m/Y" }}</strong>, portador (a) do B.I nº <strong>{{ aluno.bi }}</strong>, passado pelo arquivo de identificação de <strong>{{ aluno.bi_emissao }}</strong> aos <strong>{{ aluno.bi_data|date:"d/m/Y" }}</strong>, concluiu no ano lectivo <strong>{{ ano_conclusao }}</strong>, o curso do <strong>II CICLO DO ENSINO SECUNDÁRIO GERAL</strong>, na área de <strong>{{ aluno.reconfirmacao.curso.nome }}</strong>, conforme o disposto da alínea e) do artigo 109º da LBSEE17/16, de 7 de Outubro, com a Média Final de <strong>{{ media_geral_valores }}</strong> valores, obtida nas seguintes classificações por disciplinas:
</p>

<table>
  <thead>
    <tr>
      <th style="width: 30%;">Disciplinas</th>
      <th style="width: 13%;">10ª A/{{ ano_10 }}</th>
      <th style="width: 13%;">11ª A/{{ ano_11 }}</th>
      <th style="width: 13%;">12ª A/{{ ano_12 }}</th>
      <th style="width: 13%;">Média Final</th>
      <th style="width: 18%;">Média por Extenso</th>
    </tr>
  </thead>
  <tbody>
    
    <tr class="categoria-row">
      <td colspan="6">Formação Geral</td>
    </tr>
    {% for disc in disciplinas_geral %}
    <tr>
      <td class="text-left">{{ disc.nome }}</td>
      <td>{{ disc.nota_10|default:"-" }}</td>
      <td>{{ disc.nota_11|default:"-" }}</td>
      <td>{{ disc.nota_12|default:"-" }}</td>
      <td><strong>{{ disc.media_final }}</strong></td>
      <td>{{ disc.media_extenso }}</td>
    </tr>
    {% endfor %}

    <tr class="categoria-row">
      <td colspan="6">Formação Específica</td>
    </tr>
    {% for disc in disciplinas_especifica %}
    <tr>
      <td class="text-left">{{ disc.nome }}</td>
      <td>{{ disc.nota_10|default:"-" }}</td>
      <td>{{ disc.nota_11|default:"-" }}</td>
      <td>{{ disc.nota_12|default:"-" }}</td>
      <td><strong>{{ disc.media_final }}</strong></td>
      <td>{{ disc.media_extenso }}</td>
    </tr>
    {% endfor %}

    <tr class="categoria-row">
      <td colspan="6">Opção</td>
    </tr>
    {% for disc in disciplinas_opcao %}
    <tr>
      <td class="text-left">{{ disc.nome }}</td>
      <td>{{ disc.nota_10|default:"-" }}</td>
      <td>{{ disc.nota_11|default:"-" }}</td>
      <td>{{ disc.nota_12|default:"-" }}</td>
      <td><strong>{{ disc.media_final }}</strong></td>
      <td>{{ disc.media_extenso }}</td>
    </tr>
    {% endfor %}

    <tr class="media-geral-row">
      <td colspan="4" style="text-align: right; padding-right: 15px;">Média Geral do Curso</td>
      <td><strong>{{ media_geral_valores }}</strong></td>
      <td><strong>{{ media_geral_extenso }}</strong></td>
    </tr>
  </tbody>
</table>

<p class="texto-certificado">
  Para efeitos legais lhe é passado o presente CERTIFICADO, que consta no livro de registo nº <strong>{{ livro_registo }}</strong>, folha <strong>{{ folha_registo }}</strong>, assinado por mim e autenticado com carimbo a óleo/selo branco em uso neste estabelecimento de ensino.
</p>

<div class="local-data">
  {{ escola.localizacao_doc }}, aos {{ data_extenso }}.
</div>

<div class="assinaturas-container">
  <div class="assinatura-box">
    <p>Conferido por</p>
    <div class="assinatura-linha"></div>
    <p><strong>{{ funcionario_conferiu }}</strong></p>
  </div>
  
  <div class="assinatura-box">
    <p>A Directora</p>
    <div class="assinatura-linha"></div>
    <p><strong>{{ diretor.nome }}</strong></p>
  </div>
</div>

</body>
</html>