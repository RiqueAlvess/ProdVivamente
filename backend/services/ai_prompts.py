"""
Versioned AI prompts for VIVAMENTE 360º.
All prompts are in Brazilian Portuguese.
"""

PROMPT_VERSION = '1.0.0'


PROMPT_ANALISE_SETOR = """
Você é um especialista em saúde ocupacional e riscos psicossociais, com profundo conhecimento
na metodologia HSE-IT (Health and Safety Executive - Indicator Tool) e na NR-1 brasileira.

Analise os dados do setor abaixo e forneça insights detalhados sobre os riscos psicossociais identificados.

SETOR: {setor_nome}
EMPRESA: {empresa_nome}
TOTAL DE RESPONDENTES: {total_respondentes}

SCORES HSE-IT POR DIMENSÃO (escala 0-4):
{scores}

DIMENSÕES CRÍTICAS (nível alto ou crítico):
{dimensoes_criticas}

COMENTÁRIOS DOS COLABORADORES (resumo):
{comentarios}

IMPORTANTE:
- Scores de dimensões POSITIVAS (controle, apoio_chefia, apoio_colegas, cargo, comunicacao_mudancas):
  4 = excelente, 0 = péssimo
- Scores de dimensões NEGATIVAS (demandas, relacionamentos):
  0 = excelente (baixas demandas/conflitos), 4 = crítico (altas demandas/conflitos)

Responda SOMENTE com JSON válido no seguinte formato:
{{
  "pontos_criticos": [
    {{
      "dimensao": "nome_dimensao",
      "nivel": "critico|alto|moderado|baixo",
      "descricao": "Descrição do problema identificado",
      "impacto": "Impacto na saúde e produtividade dos colaboradores"
    }}
  ],
  "recomendacoes": [
    {{
      "prioridade": 1,
      "acao": "Descrição da ação recomendada",
      "prazo": "imediato|30_dias|60_dias|90_dias|6_meses",
      "responsavel_sugerido": "RH|Liderança|Gestão|Todos",
      "impacto_esperado": "Impacto esperado com a implementação"
    }}
  ],
  "analise_completa": "Análise narrativa completa do setor em 2-3 parágrafos",
  "alertas_legais": ["Alerta sobre conformidade NR-1 se aplicável"],
  "pontos_positivos": ["Pontos de destaque positivo do setor"]
}}
"""


PROMPT_ANALISE_SENTIMENTO = """
Analise o sentimento do seguinte comentário de um colaborador em pesquisa de clima/riscos psicossociais.

COMENTÁRIO: "{comentario}"

Responda SOMENTE com JSON válido:
{{
  "score": <float entre -1.0 (muito negativo) e 1.0 (muito positivo)>,
  "categorias": [
    "<categoria: burnout|sobrecarga|relacionamento|liderança|reconhecimento|comunicacao|ambiente|outro>"
  ],
  "emocoes_detectadas": ["<emoção detectada>"],
  "urgencia": "<alta|media|baixa>",
  "requer_atencao_imediata": <true|false>
}}
"""


PROMPT_PLANO_ACAO = """
Você é um especialista em gestão de riscos psicossociais e saúde ocupacional, especializado em NR-1.

Com base nos dados abaixo, gere um plano de ação detalhado para reduzir o risco identificado.

DIMENSÃO: {dimensao}
NÍVEL DE RISCO: {nivel_risco}
SCORE HSE-IT: {score}
EMPRESA: {empresa}
SETOR: {setor}
FATORES DE RISCO IDENTIFICADOS: {fatores}

Gere um plano de ação PRÁTICO e MENSURÁVEL.

Responda SOMENTE com JSON válido:
{{
  "acao_proposta": "Descrição detalhada das ações a serem implementadas",
  "objetivo": "Objetivo SMART do plano de ação",
  "etapas": [
    {{
      "numero": 1,
      "descricao": "Descrição da etapa",
      "prazo_dias": 30,
      "responsavel": "RH|Liderança|Gestão"
    }}
  ],
  "recursos_necessarios": "Descrição dos recursos humanos, financeiros e materiais necessários",
  "indicadores": "KPIs para medir o sucesso (ex: redução do score de demandas de 3.2 para 2.5 em 90 dias)",
  "prazo_sugerido": "30|60|90|180 dias",
  "custo_estimado": "baixo|medio|alto",
  "referencia_nr1": "Artigos ou itens da NR-1 relacionados"
}}
"""


PROMPT_RECOMENDACOES = """
Você é um especialista em saúde psicossocial no trabalho e NR-1.

Com base no panorama geral da pesquisa abaixo, gere recomendações estratégicas para a empresa.

EMPRESA: {empresa}
TOTAL DE RESPONDENTES: {total_respondentes}
NÍVEL DE RISCO GERAL: {nivel_geral}

SCORES POR DIMENSÃO:
{scores}

Gere uma lista de RECOMENDAÇÕES PRIORITÁRIAS.

Responda SOMENTE com JSON válido - uma lista de objetos:
[
  {{
    "prioridade": 1,
    "titulo": "Título conciso da recomendação",
    "descricao": "Descrição detalhada",
    "dimensoes_relacionadas": ["dimensao1", "dimensao2"],
    "prazo": "imediato|30_dias|60_dias|90_dias|6_meses|1_ano",
    "impacto": "alto|medio|baixo",
    "tipo": "preventivo|corretivo|desenvolvimento"
  }}
]
"""


PROMPT_COMPARACAO_CAMPANHAS = """
Você é um especialista em análise longitudinal de riscos psicossociais.

Compare as campanhas de pesquisa abaixo e identifique tendências e mudanças significativas.

DADOS DAS CAMPANHAS:
{dados}

Analise a evolução dos scores entre campanhas e identifique:
1. Dimensões que melhoraram
2. Dimensões que pioraram
3. Tendências gerais
4. Recomendações baseadas na evolução

Responda SOMENTE com JSON válido:
{{
  "tendencia_geral": "melhora|piora|estavel",
  "dimensoes_melhoradas": [
    {{"dimensao": "nome", "variacao": 0.5, "interpretacao": "texto"}}
  ],
  "dimensoes_pioradas": [
    {{"dimensao": "nome", "variacao": -0.3, "interpretacao": "texto"}}
  ],
  "analise": "Análise narrativa da evolução entre campanhas",
  "recomendacoes": ["Recomendação 1", "Recomendação 2"]
}}
"""
