# assistente_notas

Projeto Python para apoiar o preenchimento inteligente da coluna `Notas` em ficheiros Excel de producao de mobiliario exportados do IMOS.

Nesta fase o foco deixou de ser apenas gerar sugestoes. O objetivo passou a ser validar, no Excel, se o assistente e realmente util.

## O que esta fase faz

- importa obras Excel para MySQL
- bloqueia duplicados
- importa em lote varias obras de 2026
- interpreta partes do nome do ficheiro da obra
- compara `ORIGINAL_IMOS` e `TRANSFORMADO_AUTOMATION`
- gera sugestoes simples de `Notas` com historico MySQL
- cria ficheiros de validacao em Excel e/ou CSV
- importa feedback manual do utilizador
- gera relatorio de qualidade com base no feedback

## O que esta fase ainda nao faz

- nao usa `.mpr`
- nao usa `FINAL_VALIDADO`
- nao escreve automaticamente na coluna `Notas`
- nao usa IA avancada

Isto e intencional. Antes de automatizar mais, o projeto precisa de provar utilidade pratica no Excel.

## Estrutura principal

```text
assistente_notas/
|-- README.md
|-- importar_obra_excel.py
|-- importar_obras_lote.py
|-- analisar_excel_sugestoes.py
|-- importar_feedback_sugestoes.py
|-- relatorio_qualidade_sugestoes.py
|-- testar_validacao_obra.py
|-- testar_lote_e_sugestoes.py
|-- config/
|-- database/
|-- importers/
|-- logs/
|-- models/
|-- services/
|-- sql/
|-- tests/
`-- utils/
```

## Requisitos

- Python 3.11+ recomendado
- MySQL 8+ recomendado
- VS Code

## Instalacao inicial

```powershell
cd assistente_notas
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuracao do ambiente

1. Copiar `.env.example` para `.env`
2. preencher os dados reais do MySQL

Exemplo:

```powershell
Copy-Item .env.example .env
```

## Importacao individual

```powershell
cd assistente_notas
python importar_obra_excel.py --ficheiro Lista_Material_0556_01_26_JF_VIVA.xlsm
```

## Importacao em lote

```powershell
cd assistente_notas
python importar_obras_lote.py
```

Se quiseres outra pasta:

```powershell
cd assistente_notas
python importar_obras_lote.py --pasta C:\caminho\para\obras
```

O resumo mostra:

- n de ficheiros encontrados
- n de ficheiros importados
- n de duplicados ignorados
- n de erros
- linhas importadas por estado

## Interpretacao do nome da obra

Quando o ficheiro segue o padrao:

```text
Lista_Material_0560_01_26_JF_VIVA.xlsm
```

o projeto tenta extrair:

- `nome_base = Lista_Material`
- `referencia_obra = 0560_01_26_JF_VIVA`
- `num_encomenda_phc = 0560`
- `versao_obra = 01`
- `ano_obra = 26`
- `cliente_codigo = JF_VIVA`

Esses campos sao guardados na tabela `obras`.

## Como funciona o motor simples de sugestoes

Nesta fase o motor usa apenas historico MySQL, sem `.mpr` e sem IA.

Campos considerados:

- `descricao`
- `material`
- `artigo`
- `veio`
- `esp`
- `esp_mat`
- `esp_final`
- `orla_esq`
- `orla_dir`
- `orla_cima`
- `orla_baixo`

Saida por linha:

- `sugestao_1`
- `score_1`
- `sugestao_2`
- `score_2`
- `justificacao`

Regra de seguranca:

- se o score ficar abaixo do limiar minimo, a sugestao fica vazia

## Como gerar o ficheiro de validacao

Forma simples para uma obra real:

```powershell
cd assistente_notas
python testar_validacao_obra.py --ficheiro Lista_Material_0556_01_26_JF_VIVA.xlsm --gerar-csv
```

Isto gera:

- um ficheiro Excel de validacao `.xlsx`
- opcionalmente um CSV de apoio

Se quiseres usar diretamente o script principal de analise:

```powershell
cd assistente_notas
python analisar_excel_sugestoes.py --ficheiro Lista_Material_0556_01_26_JF_VIVA.xlsm --gerar-csv
```

Colunas de validacao:

- `obra_id`
- `linha_excel`
- `descricao`
- `material`
- `artigo`
- `notas_atual`
- `sugestao_1`
- `score_1`
- `sugestao_2`
- `score_2`
- `justificacao`
- `validacao_utilizador`
- `nota_final_utilizador`

## Como preencher o feedback no Excel

1. Abrir o ficheiro `.xlsx` gerado na pasta `logs`
2. Rever cada linha
3. Preencher `validacao_utilizador`
4. Se necessario, preencher `nota_final_utilizador`

Sugestao pratica para `validacao_utilizador`:

- `aceite`
- `rejeitada`
- `editada`

Nao e obrigatorio usar apenas estes termos, mas sao os mais consistentes para o relatorio.

## Como importar o feedback para MySQL

Depois de preencher o ficheiro:

```powershell
cd assistente_notas
python importar_feedback_sugestoes.py --ficheiro logs\validacao_sugestoes_Lista_Material_0556_01_26_JF_VIVA.xlsx
```

Tambem funciona com CSV:

```powershell
cd assistente_notas
python importar_feedback_sugestoes.py --ficheiro logs\validacao_sugestoes_Lista_Material_0556_01_26_JF_VIVA.csv
```

O feedback fica guardado em:

- `feedback_sugestoes_notas`

## Como gerar o relatorio de qualidade

Relatorio global:

```powershell
cd assistente_notas
python relatorio_qualidade_sugestoes.py
```

Relatorio por obra:

```powershell
cd assistente_notas
python relatorio_qualidade_sugestoes.py --obra-id 50
```

O relatorio mostra:

- total de linhas analisadas
- total de linhas com sugestao
- total de linhas sem sugestao
- total de sugestoes aceites
- total de sugestoes rejeitadas
- total de sugestoes editadas
- taxa de cobertura
- taxa de aceitacao
- taxa de rejeicao
- descricoes com mais acertos
- descricoes com mais falhas
- notas mais aceites
- notas mais rejeitadas

## Fluxo recomendado desta fase

1. Importar o historico:

```powershell
cd assistente_notas
python importar_obras_lote.py
```

2. Gerar ficheiro de validacao para uma obra:

```powershell
cd assistente_notas
python testar_validacao_obra.py --ficheiro Lista_Material_0556_01_26_JF_VIVA.xlsm --gerar-csv
```

3. Preencher `validacao_utilizador` e `nota_final_utilizador` no Excel

4. Importar o feedback:

```powershell
cd assistente_notas
python importar_feedback_sugestoes.py --ficheiro logs\validacao_sugestoes_Lista_Material_0556_01_26_JF_VIVA.xlsx
```

5. Gerar o relatorio:

```powershell
cd assistente_notas
python relatorio_qualidade_sugestoes.py --obra-id 50
```

## Base de dados

Tabelas principais nesta fase:

- `obras`
- `linhas_obra`
- `diferencas_estados`
- `feedback_sugestoes_notas`

## Testes

```powershell
cd assistente_notas
python -m unittest
```

## Motivo desta fase

Antes de introduzir `.mpr`, `FINAL_VALIDADO` ou escrita automatica em `Notas`, o projeto precisa de responder a uma pergunta simples:

o assistente acerta o suficiente para valer a pena?

Esta fase existe exatamente para medir isso de forma pratica e controlada.
