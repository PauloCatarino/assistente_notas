-- Esquema inicial simples para o projeto assistente_notas.
-- Objetivo: criar uma base estável e legível para evolução faseada.

CREATE DATABASE IF NOT EXISTS assistente_notas
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE assistente_notas;

-- Tabela principal de obras importadas de Excel.
CREATE TABLE IF NOT EXISTS obras (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    codigo_obra VARCHAR(100) NULL,
    nome_obra VARCHAR(255) NOT NULL,
    ficheiro_origem VARCHAR(500) NOT NULL,
    folha_origem VARCHAR(100) NOT NULL DEFAULT 'IMPORTACAO_EXCEL',
    observacoes TEXT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Linhas importadas do Excel.
CREATE TABLE IF NOT EXISTS linhas_obra (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    obra_id BIGINT NOT NULL,
    numero_linha INT NOT NULL,
    linha_excel INT NOT NULL,
    estado_origem VARCHAR(50) NOT NULL,
    nome_folha_origem VARCHAR(100) NOT NULL,
    referencia VARCHAR(150) NULL,
    designacao VARCHAR(255) NULL,
    descricao VARCHAR(255) NULL,
    material VARCHAR(255) NULL,
    comp DECIMAL(12,3) NULL,
    larg DECIMAL(12,3) NULL,
    esp DECIMAL(12,3) NULL,
    qt DECIMAL(12,3) NULL,
    veio VARCHAR(50) NULL,
    orla_esq VARCHAR(255) NULL,
    orla_dir VARCHAR(255) NULL,
    orla_cima VARCHAR(255) NULL,
    orla_baixo VARCHAR(255) NULL,
    cnc_1_raw VARCHAR(255) NULL,
    cnc_2_raw VARCHAR(255) NULL,
    enc VARCHAR(100) NULL,
    cliente VARCHAR(255) NULL,
    ref_cliente VARCHAR(255) NULL,
    processo VARCHAR(255) NULL,
    artigo VARCHAR(255) NULL,
    notas VARCHAR(500) NULL,
    id_linha_excel VARCHAR(100) NULL,
    esp_mat DECIMAL(12,3) NULL,
    esp_final DECIMAL(12,3) NULL,
    dados_json JSON NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_linhas_obra_obras
        FOREIGN KEY (obra_id) REFERENCES obras (id)
);

-- Programas CNC lidos de ficheiros .mpr.
CREATE TABLE IF NOT EXISTS cnc_programas (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    nome_programa VARCHAR(255) NOT NULL,
    caminho_ficheiro VARCHAR(500) NOT NULL,
    conteudo_texto LONGTEXT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de relação entre linhas da obra e programas CNC.
CREATE TABLE IF NOT EXISTS linhas_obra_cnc (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    linha_obra_id BIGINT NOT NULL,
    cnc_programa_id BIGINT NOT NULL,
    tipo_relacao VARCHAR(50) NOT NULL DEFAULT 'manual',
    confianca DECIMAL(5,2) NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_linhas_obra_cnc_linha
        FOREIGN KEY (linha_obra_id) REFERENCES linhas_obra (id),
    CONSTRAINT fk_linhas_obra_cnc_programa
        FOREIGN KEY (cnc_programa_id) REFERENCES cnc_programas (id),
    CONSTRAINT uk_linha_programa UNIQUE (linha_obra_id, cnc_programa_id)
);

-- Tokens extraídos dos programas CNC.
CREATE TABLE IF NOT EXISTS cnc_tokens (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cnc_programa_id BIGINT NOT NULL,
    token VARCHAR(255) NOT NULL,
    ocorrencias INT NOT NULL DEFAULT 1,
    origem VARCHAR(255) NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cnc_tokens_programa
        FOREIGN KEY (cnc_programa_id) REFERENCES cnc_programas (id),
    INDEX idx_cnc_tokens_token (token)
);

-- Registo de sugestões feitas ou analisadas pelo sistema.
CREATE TABLE IF NOT EXISTS sugestoes_notas_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    linha_obra_id BIGINT NULL,
    sugestao_texto VARCHAR(500) NULL,
    nota_original VARCHAR(500) NULL,
    origem_sugestao VARCHAR(100) NOT NULL,
    confianca DECIMAL(5,2) NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'pendente',
    detalhes_json JSON NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sugestoes_notas_linha
        FOREIGN KEY (linha_obra_id) REFERENCES linhas_obra (id)
);
