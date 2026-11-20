from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_object="config.Config"):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    from pathlib import Path
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Entre na sua conta para acessar esta página."
    login_manager.login_message_category = "aviso"
    login_manager.session_protection = "strong"

    from . import models  # noqa: F401  (registra as tabelas)
    from .auth import bp as auth_bp
    from .main import bp as main_bp
    from .cli import register_cli

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    register_cli(app)

    @app.errorhandler(404)
    def nao_encontrado(e):
        return render_template("erro.html", codigo=404, mensagem="Página não encontrada."), 404

    @app.errorhandler(403)
    def proibido(e):
        return render_template("erro.html", codigo=403, mensagem="Você não tem acesso a esta página."), 403

    @app.after_request
    def cabecalhos_seguranca(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        return resp

    return app
