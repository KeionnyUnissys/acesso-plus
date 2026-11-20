"""Autenticação: cadastro, login e logout."""
from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from . import db
from .forms import CadastroForm, LoginForm
from .models import Empresa, Usuario

bp = Blueprint("auth", __name__)


def destino_seguro(proximo):
    """Só aceita redirecionar para páginas do próprio sistema (evita open redirect)."""
    if not proximo:
        return None
    partes = urlsplit(proximo)
    if partes.scheme or partes.netloc or not proximo.startswith("/") or proximo.startswith("//"):
        return None
    return proximo


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for("main.painel"))
    form = CadastroForm()
    if form.validate_on_submit():
        usuario = Usuario(nome=form.nome.data.strip(), email=form.email.data.strip().lower())
        usuario.definir_senha(form.senha.data)
        usuario.empresas.append(Empresa(nome=form.empresa.data.strip()))
        db.session.add(usuario)
        db.session.commit()
        login_user(usuario)
        flash("Conta criada. Boas-vindas ao Acesso+!", "sucesso")
        return redirect(url_for("main.painel"))
    return render_template("auth/cadastro.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.painel"))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        usuario = db.session.execute(db.select(Usuario).filter_by(email=email)).scalar()
        # Mesma mensagem para e-mail inexistente e senha errada: não revela quais e-mails têm conta
        if usuario is None or not usuario.conferir_senha(form.senha.data):
            flash("E-mail ou senha incorretos.", "erro")
        elif not usuario.is_active:
            flash("Esta conta está desativada.", "erro")
        else:
            login_user(usuario, remember=form.lembrar.data)
            return redirect(destino_seguro(request.args.get("next")) or url_for("main.painel"))
    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("main.index"))
