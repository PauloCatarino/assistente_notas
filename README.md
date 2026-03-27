# assistente_notas

Projeto Python para apoiar o preenchimento inteligente da coluna `Notas` em ficheiros Excel de producao de mobiliario exportados do IMOS.

Nesta fase, o foco esta em consolidar a base de dados e criar a primeira comparacao entre estados do Excel, sem IA e sem logica CNC avancada.

## Objetivo atual

- importar ficheiros Excel para MySQL
- bloquear reimportacoes do mesmo ficheiro
- guardar linhas de `LISTA_ORDENADA` e `LISTAGEM_CUT_RITE`
- criar uma `chave_ligacao` simples entre estados
- gerar a primeira comparacao entre `ORIGINAL_IMOS` e `TRANSFORMADO_AUTOMATION`
- deixar a estrutura pronta para um futuro `FINAL_VALIDADO`

## Estados atualmente usados

- `ORIGINAL_IMOS`
- `TRANSFORMADO_AUTOMATION`

O estado `FINAL_VALIDADO` ainda nao esta a ser usado, mas a estrutura ja foi preparada para o futuro.

## Estrutura do projeto

```text
assistente_notas/
├── .env.example
├── .gitignore
├── README.md
├── importar_obra_excel.py
├── main.py
├── requirements.txt
├── testar_duplicados_e_comparacao.py
├── config/
├── data/
├── database/
├── importers/
├── logs/
├── models/
├── parsers/
├── services/
├── sql/
├── tests/
└── utils/
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

## Como arrancar o projeto

```powershell
cd assistente_notas
python main.py
```

## Como funciona a importacao Excel -> MySQL

O script principal de importacao e:

```powershell
cd assistente_notas
python importar_obra_excel.py --ficheiro Lista_Material.xlsm
```

Este script:

- le os metadados do ficheiro Excel
- identifica as folhas `LISTA_ORDENADA` e `LISTAGEM_CUT_RITE`
- mapeia as colunas configuradas
- insere a obra na tabela `obras`
- insere as linhas na tabela `linhas_obra`
- guarda o `estado_origem`
- guarda `nome_folha_origem`
- guarda `linha_excel`
- guarda `chave_ligacao`

## Como funciona o bloqueio de duplicados

Antes de importar, o sistema procura se o ficheiro ja foi carregado.

Estrategia usada, por esta ordem:

1. `hash_ficheiro`
2. `ficheiro_origem` apenas para registos antigos sem hash
3. `nome_ficheiro + nome_obra + tamanho_ficheiro` apenas para registos antigos sem hash

Se encontrar uma obra existente:

- a importacao e bloqueada
- a obra nao volta a ser inserida
- as linhas nao voltam a ser inseridas
- o terminal mostra um aviso claro

Campos usados na tabela `obras` para esta fase:

- `nome_ficheiro`
- `ficheiro_origem`
- `hash_ficheiro`
- `tamanho_ficheiro`
- `data_ficheiro`

## Como funciona a chave_ligacao

A `chave_ligacao` e a primeira versao da regra que tenta ligar linhas equivalentes entre estados.

Campos usados nesta versao:

- `descricao`
- `material`
- `comp`
- `larg`
- `qt`
- `artigo`
- `veio`

Regras usadas:

- normalizacao de texto
- arredondamento simples de numeros
- geracao de um hash curto e estavel

Importante:
esta e apenas uma primeira versao.
Foi feita para ser simples, previsivel e facil de evoluir.
No futuro pode ser melhorada sem partir a arquitetura.

## Como funciona a comparacao entre estados

O sistema compara:

- linhas `ORIGINAL_IMOS`
- linhas `TRANSFORMADO_AUTOMATION`

Processo usado nesta fase:

1. agrupar por `obra_id` e `chave_ligacao`
2. ordenar as linhas pela `linha_excel`
3. ligar pares por posicao dentro de cada chave
4. comparar os campos principais
5. guardar as diferencas na tabela `diferencas_estados`

Campos comparados nesta fase:

- `descricao`
- `material`
- `comp`
- `larg`
- `qt`
- `artigo`
- `notas`
- `esp`
- `orla_esq`
- `orla_dir`
- `orla_cima`
- `orla_baixo`
- `cnc_1_raw`
- `cnc_2_raw`

Tipos de diferenca usados:

- `VALOR_ALTERADO`
- `AUSENTE_NO_ORIGINAL`
- `AUSENTE_NO_TRANSFORMADO`

## Como testar esta fase

O script de teste desta ronda e:

```powershell
cd assistente_notas
python testar_duplicados_e_comparacao.py --ficheiro Lista_Material.xlsm
```

Este script:

- tenta importar novamente o ficheiro
- mostra se o duplicado foi bloqueado
- gera a comparacao entre os dois estados
- mostra no terminal:
  - `obra_id`
  - numero de linhas por estado
  - numero de chaves ligadas
  - numero de pares ligados
  - numero de diferencas encontradas

## Base de dados MySQL

Foi incluido um esquema inicial em:

- `sql/schema_inicial.sql`

Tabelas principais desta fase:

- `obras`
- `linhas_obra`
- `diferencas_estados`

Tabelas preparadas para fases seguintes:

- `cnc_programas`
- `linhas_obra_cnc`
- `cnc_tokens`
- `sugestoes_notas_log`

## Testes

```powershell
cd assistente_notas
python -m unittest
```

## Limites intencionais desta fase

- ainda nao existe `FINAL_VALIDADO`
- ainda nao existe leitura funcional de `.mpr` dentro desta comparacao
- ainda nao existe sugestao inteligente de notas
- ainda nao existe analise estatistica avancada

Isto e intencional.
O objetivo desta ronda e consolidar consistencia de dados e comparacao entre estados.
