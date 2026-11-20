import pytest

from app import create_app, db
from app.models import Usuario


@pytest.fixture
def client():
    app = create_app("config.TestConfig")
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def cadastrar(client, email="ana@loja.com.br", senha="segura123", confirmar=None):
    return client.post("/cadastro", data={
        "nome": "Ana", "empresa": "Loja da Ana", "email": email,
        "senha": senha, "confirmar": confirmar or senha,
    }, follow_redirects=True)


def entrar(client, email="ana@loja.com.br", senha="segura123"):
    return client.post("/login", data={"email": email, "senha": senha}, follow_redirects=True)


def test_painel_exige_login(client):
    r = client.get("/painel")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_cadastro_guarda_so_hash(client):
    r = cadastrar(client)
    assert "Meus sites" in r.get_data(as_text=True)
    u = db.session.execute(db.select(Usuario)).scalar_one()
    assert u.senha_hash != "segura123"
    assert u.conferir_senha("segura123")
    assert u.empresas[0].nome == "Loja da Ana"


def test_email_duplicado(client):
    cadastrar(client)
    client.post("/logout")
    r = cadastrar(client)
    assert "Já existe uma conta" in r.get_data(as_text=True)


def test_senha_fraca_e_confirmacao(client):
    assert "pelo menos 8" in cadastrar(client, senha="abc1").get_data(as_text=True)
    assert "letra e um número" in cadastrar(client, senha="somenteletras").get_data(as_text=True)
    assert "não são iguais" in cadastrar(client, confirmar="outra1234").get_data(as_text=True)


def test_login_logout(client):
    cadastrar(client)
    client.post("/logout")
    assert client.get("/painel").status_code == 302

    r = entrar(client, senha="errada123")
    assert "E-mail ou senha incorretos" in r.get_data(as_text=True)

    r = entrar(client)
    assert "Meus sites" in r.get_data(as_text=True)
    assert client.get("/painel").status_code == 200

    client.post("/logout")
    assert client.get("/painel").status_code == 302


def test_mesma_mensagem_para_email_inexistente(client):
    r = entrar(client, email="ninguem@x.com.br")
    assert "E-mail ou senha incorretos" in r.get_data(as_text=True)


def test_next_externo_ignorado(client):
    cadastrar(client)
    client.post("/logout")
    r = client.post("/login?next=https://site-malicioso.com", data={"email": "ana@loja.com.br", "senha": "segura123"})
    assert r.headers["Location"].endswith("/painel")


def test_usuario_nao_ve_nem_remove_site_de_outro(client):
    cadastrar(client)
    client.post("/painel", data={"url": "https://www.lojadaana.com.br"})
    client.post("/logout")
    cadastrar(client, email="bia@outra.com.br")
    r = client.get("/painel")
    assert "lojadaana" not in r.get_data(as_text=True)
    assert client.post("/sites/1/remover").status_code == 404


def test_url_local_bloqueada(client):
    cadastrar(client)
    r = client.post("/painel", data={"url": "http://localhost:5000"}, follow_redirects=True)
    assert "endereço público" in r.get_data(as_text=True)
    r = client.post("/painel", data={"url": "minhaloja.com.br"}, follow_redirects=True)
    assert "https://minhaloja.com.br/" in r.get_data(as_text=True)
