# assistente_notas

Projeto Python para apoiar o preenchimento inteligente da coluna `Notas` em ficheiros Excel de producao de mobiliario exportados do IMOS.

Nesta fase o foco deixou de ser apenas gerar sugestoes. O objetivo passou a ser validar, no Excel, se o assistente e realmente util.
Agora o projeto tambem ja consegue recalibrar o motor com base no feedback real para reduzir sugestoes fracas.

## O que esta fase faz

- importa obras Excel para MySQL
- bloqueia duplicados
- importa em lote varias obras de 2026
- interpreta partes do nome do ficheiro da obra
- compara `ORIGINAL_IMOS` e `TRANSFORMADO_AUTOMATION`
- gera sugestoes simples de `Notas` com historico MySQL
- cria ficheiros de validacao em Excel e/ou CSV
- importa feedback manual do utilizador de forma idempotente
- recalibra o score das sugestoes com base no feedback real
- gera relatorio de qualidade com comparacao antes vs depois

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
|-- recalibrar_e_testar_sugestoes.py
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

Nesta fase o motor usa historico MySQL e feedback real, sem `.mpr` e sem IA pesada.

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

## Como funciona a deduplicacao do feedback

O feedback manual guardado em `feedback_sugestoes_notas` usa duas regras simples:

- `obra_id + linha_excel` identifica a linha validada e impede duplicar a mesma linha da mesma obra
- `feedback_hash` identifica o conteudo exato da validacao e permite ignorar reimportacoes iguais

Resultado:

- se importares o mesmo ficheiro de feedback duas vezes, os registos iguais sao ignorados
- se alterares o feedback da mesma linha e voltares a importar, o registo e atualizado
- se a linha ainda nao tiver `validacao_utilizador` nem `nota_final_utilizador`, ela e ignorada na importacao

## Como funciona a recalibracao

O motor continua explicavel. Nao ha machine learning pesado.

A recalibracao usa apenas feedback real ja guardado e aplica:

- reforco para notas frequentemente aceites
- penalizacao para notas frequentemente rejeitadas
- ajuste extra quando a combinacao `descricao + nota` tem historico forte
- um limiar mais exigente para a versao recalibrada

Objetivo:

- reduzir cobertura quando necessario
- aumentar a precisao das sugestoes que sobrevivem

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

Para testar o motor base sem recalibracao:

```powershell
cd assistente_notas
python analisar_excel_sugestoes.py --ficheiro Lista_Material_0556_01_26_JF_VIVA.xlsm --sem-recalibracao
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

Se voltares a importar exatamente o mesmo ficheiro, o sistema deve mostrar duplicados ignorados e nao voltar a criar registos.
Linhas ainda sem resposta manual sao ignoradas na importacao e nao entram no relatorio de qualidade.

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
- taxa de cobertura antes
- taxa de aceitacao antes
- taxa de rejeicao antes
- taxa de cobertura depois
- taxa de aceitacao depois
- taxa de rejeicao depois
- top sugestoes penalizadas
- top sugestoes reforcadas
- descricoes com mais acertos
- descricoes com mais falhas
- notas mais aceites
- notas mais rejeitadas

## Como testar antes vs depois

Fluxo completo com uma obra real:

```powershell
cd assistente_notas
python recalibrar_e_testar_sugestoes.py --ficheiro-feedback logs\validacao_sugestoes_Lista_Material_0556_01_26_JF_VIVA.xlsx --ficheiro-excel Lista_Material_0556_01_26_JF_VIVA.xlsm --gerar-csv
```

O resumo mostra:

- n de feedbacks validos usados
- n de registos ignorados por duplicacao
- n de padroes recalibrados
- cobertura antes
- cobertura depois
- sugestoes geradas antes
- sugestoes geradas depois
- aceitacao antes
- aceitacao depois

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

6. Comparar antes vs depois:

```powershell
cd assistente_notas
python recalibrar_e_testar_sugestoes.py --ficheiro-feedback logs\validacao_sugestoes_Lista_Material_0556_01_26_JF_VIVA.xlsx --ficheiro-excel Lista_Material_0556_01_26_JF_VIVA.xlsm --gerar-csv
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
