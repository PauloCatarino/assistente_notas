# assistente_notas

Projeto Python para apoiar o preenchimento inteligente da coluna **"Notas"** em ficheiros Excel de produção de mobiliário exportados do IMOS.

Nesta fase, o objetivo é criar uma base técnica simples, organizada e fácil de evoluir, sem entrar ainda em lógica avançada de IA.

## Objetivo desta primeira fase

- Organizar a estrutura do projeto.
- Preparar a leitura de ficheiros Excel e programas CNC `.mpr`.
- Preparar a extração de tokens úteis dos ficheiros `.mpr`.
- Preparar a ligação a MySQL.
- Criar um ponto de arranque simples para testar o projeto.
- Deixar a arquitetura pronta para crescer de forma faseada.

## Contexto de negócio

Fluxo atual de trabalho:

1. O ficheiro Excel chega do IMOS.
2. Existe uma folha original chamada `lista_ordenada`.
3. Depois da macro/botão `Automation`, os dados passam para `LISTAGEM_CUT_RITE`.
4. São feitas alterações manuais, sobretudo na coluna `Notas`.
5. O objetivo futuro é aprender padrões históricos e sugerir notas automaticamente ou de forma semi-automática.

Além disso, os ficheiros CNC HOMAG em formato `.mpr` também serão usados como fonte de contexto, porque podem conter tokens relevantes para a sugestão de notas.

## Decisões de arquitetura

Esta estrutura foi escolhida para manter o projeto simples:

- `config/`: centraliza a configuração do projeto e variáveis de ambiente.
- `database/`: concentra a ligação à base de dados para evitar código espalhado.
- `importers/`: recebe módulos de importação de ficheiros Excel.
- `parsers/`: recebe módulos de leitura e análise de ficheiros `.mpr`.
- `services/`: concentra regras de negócio, incluindo futuras sugestões de notas.
- `models/`: define estruturas de dados simples com `dataclasses`.
- `utils/`: funções auxiliares reutilizáveis.
- `sql/`: guarda o esquema inicial da base de dados.
- `data/`: pastas sugeridas para colocar ficheiros de teste locais.
- `logs/`: registos locais úteis durante a fase de desenvolvimento.
- `tests/`: testes simples para validar a base do projeto.

Motivo principal desta abordagem:
manter os componentes separados desde o início, mas sem criar complexidade excessiva.

## Estrutura do projeto

```text
assistente_notas/
├── .env.example
├── .gitignore
├── README.md
├── main.py
├── requirements.txt
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

## Instalação inicial

No terminal, dentro da pasta do projeto:

```powershell
cd assistente_notas
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuração do ambiente

1. Copiar o ficheiro `.env.example` para `.env`.
2. Ajustar os dados do MySQL.

Exemplo:

```powershell
Copy-Item .env.example .env
```

## Como arrancar o projeto

```powershell
cd assistente_notas
python main.py
```

O `main.py` faz um arranque simples:

- carrega a configuração;
- garante que as pastas principais existem;
- mostra quantos ficheiros Excel e `.mpr` estão nas pastas de dados;
- testa a ligação à base de dados apenas se essa opção estiver ativa no `.env`.

## Como testar a importação Excel -> MySQL

Este projeto já inclui um script simples para importar uma obra Excel real:

```powershell
cd assistente_notas
python importar_obra_excel.py --ficheiro Lista_Material.xlsm
```

Antes de correr este comando, é necessário criar o ficheiro `.env`
com credenciais MySQL válidas.

Exemplo:

```powershell
Copy-Item .env.example .env
```

## Base de dados MySQL

Foi incluído um ficheiro SQL inicial em:

- `sql/schema_inicial.sql`

Tabelas preparadas nesta fase:

- `obras`
- `linhas_obra`
- `cnc_programas`
- `linhas_obra_cnc`
- `cnc_tokens`
- `sugestoes_notas_log`

Para aplicar o esquema:

```sql
SOURCE caminho/para/schema_inicial.sql;
```

Ou, no terminal:

```powershell
mysql -u root -p < sql\schema_inicial.sql
```

## Como usar os dados locais de teste

Pasta sugerida para ficheiros Excel:

- `data/excel/`

Pasta sugerida para ficheiros CNC:

- `data/mpr/`

Isto permite testar o projeto sem misturar ficheiros de produção com o código.

## Módulos já preparados

- `importers/importar_obras.py`
  - identifica ficheiros Excel e lê metadados básicos das obras.
- `importers/importar_excel_cutrite.py`
  - lê linhas da folha `LISTAGEM_CUT_RITE`.
- `parsers/ler_mpr.py`
  - lê o conteúdo base de ficheiros `.mpr`.
- `parsers/extrair_tokens_mpr.py`
  - extrai tokens em maiúsculas e com underscore, úteis para análise futura.
- `services/servico_sugestoes.py`
  - regista eventos de sugestão e prepara a evolução da lógica de sugestões.

## Testes simples

```powershell
cd assistente_notas
python -m unittest
```

## Limitações desta fase

- Ainda não existe importação histórica completa para a base de dados.
- Ainda não existe análise de padrões.
- Ainda não existe integração com Excel/VBA.
- Ainda não existe motor real de sugestão para a coluna `Notas`.

Estas limitações são intencionais.
O foco desta fase é criar uma base estável e clara.

## Próxima evolução recomendada

Depois desta base, o passo mais seguro é:

1. definir exatamente que colunas do `LISTAGEM_CUT_RITE` interessam;
2. importar essas colunas para MySQL;
3. associar linhas da obra a programas `.mpr`;
4. guardar tokens extraídos na base de dados;
5. só depois começar regras simples para sugerir `Notas`.
