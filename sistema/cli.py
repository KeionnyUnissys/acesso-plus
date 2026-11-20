"""Comandos de terminal: flask --app run init-db"""
import click

from . import db
from .models import Categoria, Plano

CATEGORIAS = [
    ("Acessibilidade", "Barreiras para pessoas que usam leitor de tela, teclado ou outras tecnologias assistivas."),
    ("Legibilidade", "Facilidade de ler o conteúdo: idioma, títulos e estrutura do texto."),
    ("Navegação", "Links, menus e a ordem lógica da página."),
    ("Experiência mobile", "Como a página se comporta no celular."),
    ("Formulários", "Campos com rótulos claros e fáceis de preencher."),
    ("Botões e links", "Elementos clicáveis com nomes que fazem sentido."),
]

PLANOS = [
    ("Descobrir", 0, "Análise gratuita da página inicial."),
    ("Corrigir", 49.90, "Explicações detalhadas e recomendações por problema."),
    ("Monitorar", 99.90, "Análises periódicas, histórico e alertas."),
]


def register_cli(app):
    @app.cli.command("init-db")
    @click.option("--recriar", is_flag=True, help="Apaga tudo e cria de novo.")
    def init_db(recriar):
        """Cria as tabelas e cadastra categorias e planos."""
        if recriar:
            db.drop_all()
        db.create_all()
        for nome, desc in CATEGORIAS:
            if not db.session.execute(db.select(Categoria).filter_by(nome=nome)).scalar():
                db.session.add(Categoria(nome=nome, descricao=desc))
        for nome, valor, desc in PLANOS:
            if not db.session.execute(db.select(Plano).filter_by(nome=nome)).scalar():
                db.session.add(Plano(nome=nome, valor=valor, descricao=desc))
        db.session.commit()
        from .catalogo import garantir_catalogo
        garantir_catalogo(db)
        click.echo("Banco pronto: tabelas, categorias, catálogo de problemas e planos cadastrados.")

    @app.cli.command("criar-demo")
    def criar_demo():
        """Cria a conta de demonstração usada na apresentação."""
        from .models import Empresa, Usuario

        email = "demo@exemplo.com.br"
        if db.session.execute(db.select(Usuario).filter_by(email=email)).scalar():
            click.echo(f"A conta {email} já existe.")
            return
        usuario = Usuario(nome="Conta de demonstração", email=email)
        usuario.definir_senha("demo12345")
        usuario.empresas.append(Empresa(nome="Empresa Demo"))
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Conta criada: {email} / senha demo12345")
