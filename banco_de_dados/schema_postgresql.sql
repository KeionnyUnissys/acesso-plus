-- Acesso+ · Script de criação para PostgreSQL
-- Baseado no Projeto Físico (Atividade 05, 16/09/2026).
-- Diferença: a tabela "problema" ganhou a coluna "codigo", que o scanner usa para achar o problema no catálogo.
-- Na prática, o comando "flask --app run init-db" cria estas mesmas tabelas automaticamente.

CREATE TABLE usuario (
  id_usuario BIGSERIAL PRIMARY KEY,
  nome VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  senha_hash VARCHAR(255) NOT NULL,
  data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(20) NOT NULL DEFAULT 'ATIVO',
  CHECK (status IN ('ATIVO','INATIVO','BLOQUEADO'))
);

CREATE TABLE empresa (
  id_empresa BIGSERIAL PRIMARY KEY,
  id_usuario BIGINT NOT NULL REFERENCES usuario(id_usuario),
  nome VARCHAR(150) NOT NULL
);

CREATE TABLE site (
  id_site BIGSERIAL PRIMARY KEY,
  id_empresa BIGINT NOT NULL REFERENCES empresa(id_empresa),
  url VARCHAR(500) NOT NULL,
  data_cadastro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(20) NOT NULL DEFAULT 'ATIVO',
  CHECK (status IN ('ATIVO','INATIVO'))
);

CREATE TABLE analise (
  id_analise BIGSERIAL PRIMARY KEY,
  id_site BIGINT NOT NULL REFERENCES site(id_site),
  data_analise TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  pontuacao_geral NUMERIC(5,2),
  status VARCHAR(30) NOT NULL DEFAULT 'PENDENTE',
  CHECK (pontuacao_geral IS NULL OR pontuacao_geral BETWEEN 0 AND 100),
  CHECK (status IN ('PENDENTE','PROCESSANDO','CONCLUIDA','ERRO'))
);

CREATE TABLE categoria (
  id_categoria SERIAL PRIMARY KEY,
  nome VARCHAR(80) NOT NULL UNIQUE,
  descricao TEXT
);

CREATE TABLE pontuacao_categoria (
  id_pontuacao BIGSERIAL PRIMARY KEY,
  id_analise BIGINT NOT NULL REFERENCES analise(id_analise) ON DELETE CASCADE,
  id_categoria INT NOT NULL REFERENCES categoria(id_categoria),
  pontuacao NUMERIC(5,2) NOT NULL CHECK (pontuacao BETWEEN 0 AND 100),
  UNIQUE (id_analise, id_categoria)
);

CREATE TABLE problema (
  id_problema BIGSERIAL PRIMARY KEY,
  id_categoria INT NOT NULL REFERENCES categoria(id_categoria),
  codigo VARCHAR(50) UNIQUE,
  titulo VARCHAR(150) NOT NULL,
  descricao TEXT NOT NULL,
  impacto TEXT,
  recomendacao TEXT,
  prioridade_padrao VARCHAR(20) NOT NULL,
  CHECK (prioridade_padrao IN ('CRITICO','IMPORTANTE','MELHORIA','APROVADO'))
);

CREATE TABLE problema_encontrado (
  id_ocorrencia BIGSERIAL PRIMARY KEY,
  id_analise BIGINT NOT NULL REFERENCES analise(id_analise) ON DELETE CASCADE,
  id_problema BIGINT NOT NULL REFERENCES problema(id_problema),
  prioridade VARCHAR(20) NOT NULL,
  elemento_afetado VARCHAR(255),
  localizacao TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'PENDENTE',
  CHECK (prioridade IN ('CRITICO','IMPORTANTE','MELHORIA','APROVADO')),
  CHECK (status IN ('PENDENTE','CORRIGIDO','IGNORADO'))
);

CREATE TABLE plano (
  id_plano SERIAL PRIMARY KEY,
  nome VARCHAR(50) NOT NULL UNIQUE,
  valor NUMERIC(10,2) NOT NULL CHECK (valor >= 0),
  descricao TEXT
);

CREATE TABLE assinatura (
  id_assinatura BIGSERIAL PRIMARY KEY,
  id_empresa BIGINT NOT NULL REFERENCES empresa(id_empresa),
  id_plano INT NOT NULL REFERENCES plano(id_plano),
  data_inicio DATE NOT NULL,
  data_fim DATE,
  status VARCHAR(20) NOT NULL,
  CHECK (data_fim IS NULL OR data_fim >= data_inicio),
  CHECK (status IN ('ATIVA','CANCELADA','EXPIRADA'))
);

CREATE UNIQUE INDEX idx_usuario_email ON usuario(email);
CREATE INDEX idx_site_empresa ON site(id_empresa);
CREATE INDEX idx_analise_site_data ON analise(id_site, data_analise DESC);
CREATE INDEX idx_pontuacao_analise ON pontuacao_categoria(id_analise);
CREATE INDEX idx_problema_encontrado_analise ON problema_encontrado(id_analise);
CREATE INDEX idx_assinatura_empresa ON assinatura(id_empresa);
