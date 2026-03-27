# assistente_notas

Projeto Python para apoiar o preenchimento inteligente da coluna `Notas` em ficheiros Excel de producao de mobiliario exportados do IMOS.

Nesta fase o foco continua a ser qualidade de dados, sem IA, sem `.mpr` e sem `FINAL_VALIDADO`. O objetivo e melhorar a ligacao entre os estados `ORIGINAL_IMOS` e `TRANSFORMADO_AUTOMATION`.

## Objetivo atual

- importar ficheiros Excel para MySQL
- bloquear reimportacoes do mesmo ficheiro
- guardar linhas de `LISTA_ORDENADA` e `LISTAGEM_CUT_RITE`
- gerar `chave_ligacao` v2 para agrupar candidatos
- comparar estados com correspondencia forte e tolerante
- classificar diferencas de forma mais util para leitura humana
- gerar um resumo simples no terminal e um CSV opcional

## Estados atualmente usados

- `ORIGINAL_IMOS`
- `TRANSFORMADO_AUTOMATION`

O estado `FINAL_VALIDADO` ainda nao esta a ser usado, mas a estrutura continua preparada para essa fase.

## Estrutura do projeto

```text
assistente_notas/
|-- .env.example
|-- .gitignore
|-- README.md
|-- gerar_resumo_comparacao.py
|-- importar_obra_excel.py
|-- main.py
|-- requirements.txt
|-- testar_duplicados_e_comparacao.py
|-- config/
|-- data/
|-- database/
|-- importers/
|-- logs/
|-- models/
|-- parsers/
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
- guarda `estado_origem`, `nome_folha_origem`, `linha_excel` e `chave_ligacao`

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

Campos usados na tabela `obras` nesta fase:

- `nome_ficheiro`
- `ficheiro_origem`
- `hash_ficheiro`
- `tamanho_ficheiro`
- `data_ficheiro`

## Como funciona a chave_ligacao v2

A `chave_ligacao` v2 ja nao tenta resolver a ligacao sozinha. Nesta fase ela serve para agrupar candidatos provaveis.

Campos usados para a chave tolerante:

- `descricao`
- `material`
- `artigo`
- `veio`

Motivo:

- estes campos tendem a ser mais estaveis entre `ORIGINAL_IMOS` e `TRANSFORMADO_AUTOMATION`
- `comp`, `larg` e `qt` podem mudar, arredondar ou surgir trocados apos o Automation

Regras usadas:

- normalizacao de espacos
- normalizacao de maiusculas e minusculas
- remocao de acentos para comparacao
- conversao de nulos para vazio controlado
- geracao de um hash curto e estavel

## Como funciona a correspondencia v2

A comparacao trabalha por niveis:

1. `FORTE`
   quando a assinatura completa coincide em `descricao`, `material`, `comp`, `larg`, `qt`, `artigo` e `veio`
2. `TOLERANTE`
   quando a assinatura forte nao coincide, mas o score de semelhanca passa o limiar minimo
3. `SEM_PAR`
   quando nenhuma ligacao aceitavel e encontrada

Campos considerados no score:

- `descricao`
- `material`
- `artigo`
- `veio`
- `qt`
- `comp` e `larg`

Detalhes importantes da v2:

- `comp` e `larg` aceitam pequenas tolerancias numericas
- `comp` e `larg` tambem podem ser comparados de forma cruzada
- isto ajuda quando a peca aparece rodada entre os dois estados

Importante:
esta v2 ainda e uma heuristica simples. Foi feita para melhorar ligacoes corretas sem introduzir logica "magica". Pode evoluir mais tarde de forma controlada.

## Como funciona a classificacao das diferencas

As diferencas passam a ser classificadas com tipos mais uteis:

- `DESCRICAO_ALTERADA`
- `MATERIAL_ALTERADO`
- `ARTIGO_ALTERADO`
- `VEIO_ALTERADO`
- `MEDIDA_ALTERADA`
- `ORLA_ALTERADA`
- `CNC_ALTERADO`
- `NOTA_ADICIONADA`
- `NOTA_REMOVIDA`
- `NOTA_ALTERADA`
- `LINHA_SEM_PAR`
- `CAMPO_ALTERADO`

As diferencas continuam a ser guardadas em `diferencas_estados`, agora com:

- `nivel_correspondencia`
- `score_correspondencia`

## Como gerar um resumo da comparacao

Script novo desta fase:

```powershell
cd assistente_notas
python gerar_resumo_comparacao.py --ficheiro Lista_Material.xlsm
```

Este script mostra:

- `obra_id`
- total de linhas em `ORIGINAL_IMOS`
- total de linhas em `TRANSFORMADO_AUTOMATION`
- total de chaves ligadas
- total de pares ligados
- pares por nivel `FORTE` e `TOLERANTE`
- total de linhas sem correspondencia
- total de diferencas
- top tipos de diferenca

Para gerar tambem um CSV de apoio:

```powershell
cd assistente_notas
python gerar_resumo_comparacao.py --ficheiro Lista_Material.xlsm --gerar-csv
```

CSV por omissao:

- `logs/comparacao_obra_<id>.csv`

Tambem podes escolher o caminho:

```powershell
cd assistente_notas
python gerar_resumo_comparacao.py --obra-id 1 --csv logs\minha_comparacao.csv
```

## Como testar duplicado + comparacao

O script de teste desta ronda e:

```powershell
cd assistente_notas
python testar_duplicados_e_comparacao.py --ficheiro Lista_Material.xlsm
```

Este script:

- tenta importar novamente o ficheiro
- mostra se o duplicado foi bloqueado
- recalcula a comparacao entre estados
- mostra os totais principais, os pares por nivel e o top de diferencas

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
- ainda nao existe integracao `.mpr` nesta comparacao
- ainda nao existe sugestao inteligente de notas
- ainda nao existe analise estatistica avancada

Isto e intencional.
O objetivo desta ronda e melhorar a qualidade da correspondencia entre estados antes de avancar para as fases seguintes.
