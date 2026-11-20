"""Modelos do banco, seguindo o Projeto Físico do Acesso+ (Atividade 05)."""
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager

PRIORIDADES = ("CRITICO", "IMPORTANTE", "MELHORIA", "APROVADO")


def agora():
    return datetime.now()


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuario"
    id_usuario = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=agora)
    status = db.Column(db.String(20), nullable=False, default="ATIVO")

    empresas = db.relationship("Empresa", back_populates="usuario", cascade="all, delete-orphan")

    __table_args__ = (db.CheckConstraint("status IN ('ATIVO','INATIVO','BLOQUEADO')", name="ck_usuario_status"),)

    # Flask-Login usa get_id(); nossa PK não se chama "id"
    def get_id(self):
        return str(self.id_usuario)

    @property
    def is_active(self):
        return self.status == "ATIVO"

    def definir_senha(self, senha: str):
        # A senha nunca é guardada: só o hash (scrypt, com sal aleatório)
        self.senha_hash = generate_password_hash(senha)

    def conferir_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)


@login_manager.user_loader
def carregar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))


class Empresa(db.Model):
    __tablename__ = "empresa"
    id_empresa = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    id_usuario = db.Column(db.BigInteger, db.ForeignKey("usuario.id_usuario"), nullable=False)
    nome = db.Column(db.String(150), nullable=False)

    usuario = db.relationship("Usuario", back_populates="empresas")
    sites = db.relationship("Site", back_populates="empresa", cascade="all, delete-orphan")


class Site(db.Model):
    __tablename__ = "site"
    id_site = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    id_empresa = db.Column(db.BigInteger, db.ForeignKey("empresa.id_empresa"), nullable=False, index=True)
    url = db.Column(db.String(500), nullable=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=agora)
    status = db.Column(db.String(20), nullable=False, default="ATIVO")

    empresa = db.relationship("Empresa", back_populates="sites")
    analises = db.relationship("Analise", back_populates="site", cascade="all, delete-orphan",
                               order_by="Analise.data_analise.desc()")

    __table_args__ = (db.CheckConstraint("status IN ('ATIVO','INATIVO')", name="ck_site_status"),)


class Analise(db.Model):
    __tablename__ = "analise"
    id_analise = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    id_site = db.Column(db.BigInteger, db.ForeignKey("site.id_site"), nullable=False)
    data_analise = db.Column(db.DateTime, nullable=False, default=agora)
    pontuacao_geral = db.Column(db.Numeric(5, 2))
    status = db.Column(db.String(30), nullable=False, default="PENDENTE")

    site = db.relationship("Site", back_populates="analises")
    pontuacoes = db.relationship("PontuacaoCategoria", back_populates="analise", cascade="all, delete-orphan")
    problemas = db.relationship("ProblemaEncontrado", back_populates="analise", cascade="all, delete-orphan")

    __table_args__ = (
        db.CheckConstraint("pontuacao_geral IS NULL OR pontuacao_geral BETWEEN 0 AND 100", name="ck_analise_pontuacao"),
        db.CheckConstraint("status IN ('PENDENTE','PROCESSANDO','CONCLUIDA','ERRO')", name="ck_analise_status"),
        db.Index("idx_analise_site_data", "id_site", "data_analise"),
    )


class Categoria(db.Model):
    __tablename__ = "categoria"
    id_categoria = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False, unique=True)
    descricao = db.Column(db.Text)


class PontuacaoCategoria(db.Model):
    __tablename__ = "pontuacao_categoria"
    id_pontuacao = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    id_analise = db.Column(db.BigInteger, db.ForeignKey("analise.id_analise", ondelete="CASCADE"), nullable=False, index=True)
    id_categoria = db.Column(db.Integer, db.ForeignKey("categoria.id_categoria"), nullable=False)
    pontuacao = db.Column(db.Numeric(5, 2), nullable=False)

    analise = db.relationship("Analise", back_populates="pontuacoes")
    categoria = db.relationship("Categoria")

    __table_args__ = (
        db.CheckConstraint("pontuacao BETWEEN 0 AND 100", name="ck_pontuacao_faixa"),
        db.UniqueConstraint("id_analise", "id_categoria", name="uq_pontuacao_analise_categoria"),
    )


class Problema(db.Model):
    """Catálogo de problemas (conteúdo escrito pela Maria Eduarda)."""
    __tablename__ = "problema"
    id_problema = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    id_categoria = db.Column(db.Integer, db.ForeignKey("categoria.id_categoria"), nullable=False)
    codigo = db.Column(db.String(50), unique=True)  # identificador usado pelo scanner, ex.: "img-sem-alt"
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    impacto = db.Column(db.Text)
    recomendacao = db.Column(db.Text)
    prioridade_padrao = db.Column(db.String(20), nullable=False)

    categoria = db.relationship("Categoria")

    __table_args__ = (
        db.CheckConstraint("prioridade_padrao IN ('CRITICO','IMPORTANTE','MELHORIA','APROVADO')", name="ck_problema_prioridade"),
    )


class ProblemaEncontrado(db.Model):
    __tablename__ = "problema_encontrado"
    id_ocorrencia = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    id_analise = db.Column(db.BigInteger, db.ForeignKey("analise.id_analise", ondelete="CASCADE"), nullable=False, index=True)
    id_problema = db.Column(db.BigInteger, db.ForeignKey("problema.id_problema"), nullable=False)
    prioridade = db.Column(db.String(20), nullable=False)
    elemento_afetado = db.Column(db.String(255))
    localizacao = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="PENDENTE")

    analise = db.relationship("Analise", back_populates="problemas")
    problema = db.relationship("Problema")

    __table_args__ = (
        db.CheckConstraint("prioridade IN ('CRITICO','IMPORTANTE','MELHORIA','APROVADO')", name="ck_ocorrencia_prioridade"),
        db.CheckConstraint("status IN ('PENDENTE','CORRIGIDO','IGNORADO')", name="ck_ocorrencia_status"),
    )


class Plano(db.Model):
    __tablename__ = "plano"
    id_plano = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    descricao = db.Column(db.Text)

    __table_args__ = (db.CheckConstraint("valor >= 0", name="ck_plano_valor"),)


class Assinatura(db.Model):
    __tablename__ = "assinatura"
    id_assinatura = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True)
    id_empresa = db.Column(db.BigInteger, db.ForeignKey("empresa.id_empresa"), nullable=False, index=True)
    id_plano = db.Column(db.Integer, db.ForeignKey("plano.id_plano"), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False)

    __table_args__ = (
        db.CheckConstraint("data_fim IS NULL OR data_fim >= data_inicio", name="ck_assinatura_datas"),
        db.CheckConstraint("status IN ('ATIVA','CANCELADA','EXPIRADA')", name="ck_assinatura_status"),
    )
