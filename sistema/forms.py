from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, StringField, URLField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp, ValidationError

from . import db
from .models import Usuario


class CadastroForm(FlaskForm):
    nome = StringField("Seu nome", validators=[DataRequired("Informe seu nome."), Length(max=100)])
    empresa = StringField("Nome da empresa", validators=[DataRequired("Informe o nome da empresa."), Length(max=150)])
    email = EmailField("E-mail", validators=[
        DataRequired("Informe seu e-mail."),
        Email("Digite um e-mail válido, como nome@empresa.com.br."),
        Length(max=150),
    ])
    senha = PasswordField("Senha", validators=[
        DataRequired("Crie uma senha."),
        Length(min=8, max=128, message="A senha precisa ter pelo menos 8 caracteres."),
        Regexp(r"^(?=.*[A-Za-z])(?=.*\d).+$", message="Use pelo menos uma letra e um número."),
    ])
    confirmar = PasswordField("Confirme a senha", validators=[
        DataRequired("Repita a senha."),
        EqualTo("senha", message="As senhas não são iguais."),
    ])

    def validate_email(self, campo):
        email = campo.data.strip().lower()
        if db.session.execute(db.select(Usuario).filter_by(email=email)).scalar():
            raise ValidationError("Já existe uma conta com este e-mail. Tente entrar.")


class LoginForm(FlaskForm):
    email = EmailField("E-mail", validators=[DataRequired("Informe seu e-mail."), Email("E-mail inválido.")])
    senha = PasswordField("Senha", validators=[DataRequired("Informe sua senha.")])
    lembrar = BooleanField("Manter conectado neste computador")


class SiteForm(FlaskForm):
    url = URLField("Endereço do site", validators=[
        DataRequired("Informe o endereço do site."),
        Length(max=500),
    ])
