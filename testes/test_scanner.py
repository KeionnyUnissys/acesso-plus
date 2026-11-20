"""Testes do scanner, da pontuação e das rotas de análise. Nenhum teste acessa a internet."""
import socket

import pytest

from sistema import create_app, db, scanner
from sistema.models import Analise, ProblemaEncontrado

PAGINA_BOA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Início | Padaria Pão Quente</title></head>
<body>
<h1>Padaria Pão Quente</h1>
<h2>Cardápio</h2><h3>Pães</h3>
<img src="pao.jpg" alt="Pão francês"> <img src="enfeite.png" alt="">
<a href="/cardapio">Ver o cardápio completo</a>
<a href="https://wa.me/5561"><img src="zap.svg" alt="Falar no WhatsApp"></a>
<form><label for="email">E-mail</label><input id="email" type="email">
<label>Nome <input type="text" name="nome"></label>
<input type="hidden" name="t"><button type="submit">Enviar</button></form>
<iframe src="https://maps.example" title="Mapa da padaria"></iframe>
</body></html>"""

PAGINA_RUIM = """<html><head><meta name="viewport" content="width=device-width, user-scalable=no"></head>
<body>
<h2>Promoções</h2><h4>Hoje</h4>
<img src="a.jpg"><img src="b.jpg"><img src="c.jpg">
<a href="/x"></a>
<a href="/promo">Clique aqui</a>
<a href="https://instagram.com/loja"><i class="icone-insta"></i></a>
<input type="text" placeholder="Seu e-mail">
<button><i class="lupa"></i></button>
<iframe src="https://maps.example"></iframe>
</body></html>"""


def codigos(html):
    return sorted({o.codigo for o in scanner.analisar_html(html)})


# ---------------------------------------------------------------- verificações

def test_pagina_boa_nao_tem_problemas():
    assert scanner.analisar_html(PAGINA_BOA) == []


def test_pagina_ruim_encontra_todos_os_problemas():
    assert codigos(PAGINA_RUIM) == sorted([
        "img-sem-alt", "iframe-sem-titulo", "pagina-sem-idioma", "pagina-sem-titulo", "sem-h1",
        "titulos-fora-de-ordem", "zoom-bloqueado", "campo-sem-rotulo", "link-sem-nome",
        "botao-sem-nome", "link-generico",
    ])


def test_conta_cada_ocorrencia_e_guarda_linha():
    achados = scanner.analisar_html(PAGINA_RUIM)
    imgs = [o for o in achados if o.codigo == "img-sem-alt"]
    assert len(imgs) == 3
    assert imgs[0].localizacao == "linha 4"
    assert "a.jpg" in imgs[0].elemento
    assert len([o for o in achados if o.codigo == "link-sem-nome"]) == 2


def test_sem_viewport_e_aria_label_vale_como_nome():
    html = '<html lang="pt"><title>x</title><h1>x</h1><a href="/" aria-label="Início"><i></i></a></html>'
    assert codigos(html) == ["sem-viewport"]


def test_elementos_ocultos_nao_contam():
    html = """<html lang="pt"><title>x</title><h1>x</h1><meta name="viewport" content="width=device-width">
    <noscript><iframe src="https://www.googletagmanager.com/ns.html"></iframe></noscript>
    <iframe src="https://x.example" style="display: none"></iframe>
    <div hidden><img src="a.png"></div>
    <a href="/" aria-hidden="true"><i></i></a></html>"""
    assert codigos(html) == []


def test_placeholder_nao_substitui_rotulo():
    assert "campo-sem-rotulo" in codigos('<input type="email" placeholder="E-mail">')


# ---------------------------------------------------------------- pontuação

def test_pontuacao_sem_problemas_e_100():
    geral, notas = scanner.calcular_pontuacao([])
    assert geral == 100
    assert set(notas) == set(scanner.CATEGORIAS_AVALIADAS)


def test_pontuacao_desconta_por_prioridade_e_repeticao():
    O = scanner.Ocorrencia
    geral, notas = scanner.calcular_pontuacao([O("img-sem-alt")] * 3 + [O("pagina-sem-idioma")])
    assert notas["Acessibilidade"] == 100 - (30 + 30 * 0.2 * 2)   # 3 imagens: 30 + 2 repetições de 6
    assert notas["Legibilidade"] == 85
    assert notas["Formulários"] == 100
    assert geral == round(sum(notas.values()) / len(notas), 2)


def test_desconto_tem_limite_e_nota_nunca_negativa():
    O = scanner.Ocorrencia
    _, notas = scanner.calcular_pontuacao([O("link-sem-nome")] * 50 + [O("botao-sem-nome")] * 50)
    assert notas["Botões e links"] == 0


# ---------------------------------------------------------------- segurança do download

def test_bloqueia_endereco_interno(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(None, None, None, None, ("192.168.0.10", 80))])
    with pytest.raises(scanner.ErroScanner, match="sites públicos"):
        scanner.baixar_pagina("http://intranet.empresa.com.br/")


def test_dominio_inexistente(monkeypatch):
    def falha(*a, **k):
        raise socket.gaierror()
    monkeypatch.setattr(socket, "getaddrinfo", falha)
    with pytest.raises(scanner.ErroScanner, match="Não encontramos"):
        scanner.baixar_pagina("https://nao-existe.com.br/")


# ---------------------------------------------------------------- rotas

@pytest.fixture
def client():
    app = create_app("config.TestConfig")
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def preparar(client, email="ana@loja.com.br"):
    client.post("/cadastro", data={"nome": "Ana", "empresa": "Loja", "email": email,
                                   "senha": "segura123", "confirmar": "segura123"})
    client.post("/painel", data={"url": "https://www.lojadaana.com.br"})


def test_analisar_grava_e_mostra_resultado(client, monkeypatch):
    monkeypatch.setattr(scanner, "baixar_pagina", lambda url: (url, PAGINA_RUIM))
    preparar(client)
    r = client.post("/sites/1/analisar", follow_redirects=True)
    texto = r.get_data(as_text=True)
    assert "Resultado da análise" in texto
    assert "Imagem sem texto alternativo" in texto
    assert "Como corrigir" in texto
    assert "Nota por categoria" in texto
    assert "Todos os botões têm nome" not in texto           # botão sem nome foi encontrado
    assert "A página tem título principal" not in texto      # página ruim não tem h1

    analise = db.session.execute(db.select(Analise)).scalar_one()
    assert analise.status == "CONCLUIDA"
    assert 0 <= analise.pontuacao_geral < 100
    assert len(analise.pontuacoes) == len(scanner.CATEGORIAS_AVALIADAS)
    assert db.session.execute(db.select(db.func.count(ProblemaEncontrado.id_ocorrencia))).scalar() == len(
        scanner.analisar_html(PAGINA_RUIM))

    painel = client.get("/painel").get_data(as_text=True)
    assert f"{int(round(analise.pontuacao_geral))}/100" in painel


def test_erro_no_site_volta_ao_painel_com_aviso(client, monkeypatch):
    def fora_do_ar(url):
        raise scanner.ErroScanner("Não foi possível acessar o site. Ele pode estar fora do ar.")
    monkeypatch.setattr(scanner, "baixar_pagina", fora_do_ar)
    preparar(client)
    r = client.post("/sites/1/analisar", follow_redirects=True)
    assert "fora do ar" in r.get_data(as_text=True)
    assert db.session.execute(db.select(Analise)).scalar_one().status == "ERRO"
    assert client.get("/analises/1").status_code == 404


def test_outro_usuario_nao_ve_nem_analisa(client, monkeypatch):
    monkeypatch.setattr(scanner, "baixar_pagina", lambda url: (url, PAGINA_BOA))
    preparar(client)
    r = client.post("/sites/1/analisar", follow_redirects=True)
    assert "Todas as imagens têm texto alternativo" in r.get_data(as_text=True)
    client.post("/logout")
    preparar(client, email="bia@outra.com.br")
    assert client.get("/analises/1").status_code == 404
    assert client.post("/sites/1/analisar").status_code == 404


def test_analisar_exige_login(client):
    assert client.post("/sites/1/analisar").status_code == 302


def test_historico_mostra_analises_anteriores(client, monkeypatch):
    preparar(client)
    monkeypatch.setattr(scanner, "baixar_pagina", lambda url: (url, PAGINA_RUIM))
    client.post("/sites/1/analisar")
    monkeypatch.setattr(scanner, "baixar_pagina", lambda url: (url, PAGINA_BOA))
    texto = client.post("/sites/1/analisar", follow_redirects=True).get_data(as_text=True)
    assert "Histórico deste site" in texto
    assert "100/100</strong> (esta análise)" in texto
    assert 'href="/analises/1"' in texto


def test_o_proprio_acesso_mais_passa_nas_proprias_verificacoes(client, monkeypatch):
    """Um scanner de acessibilidade não pode ser inacessível: todas as telas devem passar."""
    paginas = {"/": client.get("/"), "/login": client.get("/login"), "/cadastro": client.get("/cadastro")}
    preparar(client)
    monkeypatch.setattr(scanner, "baixar_pagina", lambda url: (url, PAGINA_RUIM))
    paginas["/analises/1"] = client.post("/sites/1/analisar", follow_redirects=True)
    paginas["/painel"] = client.get("/painel")
    for rota, resp in paginas.items():
        assert resp.status_code == 200, rota
        achados = scanner.analisar_html(resp.get_data(as_text=True))
        assert achados == [], f"{rota}: {[(o.codigo, o.elemento) for o in achados]}"
