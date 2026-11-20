"""Scanner do Acesso+: baixa a página inicial de um site e procura barreiras de acessibilidade.

Dividido em três partes, para poder testar cada uma separadamente:
1. baixar_pagina()  -> busca o HTML com segurança (só endereços públicos, tempo e tamanho limitados);
2. analisar_html()  -> roda as verificações e devolve as ocorrências encontradas;
3. calcular_pontuacao() -> transforma as ocorrências em nota de 0 a 100, geral e por categoria.
"""
import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from .catalogo import CATALOGO, POR_CODIGO

TEMPO_LIMITE = (5, 10)          # segundos para conectar e para receber a resposta
TAMANHO_MAXIMO = 2 * 1024 * 1024  # 2 MB de HTML
MAX_REDIRECIONAMENTOS = 5
AGENTE = "AcessoMais/0.1 (scanner de acessibilidade; projeto academico Senac-DF)"

# Quanto cada tipo de problema tira da nota da categoria
PESO = {"CRITICO": 30, "IMPORTANTE": 15, "MELHORIA": 5}
CATEGORIAS_AVALIADAS = sorted({item["categoria"] for item in CATALOGO})

TEXTOS_GENERICOS = {
    "clique aqui", "clique", "aqui", "saiba mais", "leia mais", "veja mais", "mais",
    "ver mais", "acesse", "acesse aqui", "link", "click here", "read more", "more",
}


class ErroScanner(Exception):
    """Erro com mensagem que pode ser mostrada para o usuário."""


@dataclass
class Ocorrencia:
    codigo: str
    elemento: str = ""
    localizacao: str = ""

    @property
    def prioridade(self):
        return POR_CODIGO[self.codigo]["prioridade"]

    @property
    def categoria(self):
        return POR_CODIGO[self.codigo]["categoria"]


# --------------------------------------------------------------------------- 1. baixar a página

def endereco_publico(host: str) -> bool:
    """True se TODOS os IPs do domínio forem públicos. Impede o scanner de acessar a rede interna."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise ErroScanner("Não encontramos esse endereço. Confira se o site está digitado certo.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not ip.is_global:
            return False
    return True


def baixar_pagina(url: str) -> tuple[str, str]:
    """Devolve (url_final, html). Segue redirecionamentos conferindo cada endereço."""
    sessao = requests.Session()
    sessao.headers.update({"User-Agent": AGENTE, "Accept": "text/html,application/xhtml+xml"})
    atual = url
    for _ in range(MAX_REDIRECIONAMENTOS + 1):
        partes = urlsplit(atual)
        if partes.scheme not in ("http", "https") or not partes.hostname:
            raise ErroScanner("O site redirecionou para um endereço inválido.")
        if not endereco_publico(partes.hostname):
            raise ErroScanner("Por segurança, o Acesso+ só analisa sites públicos da internet.")
        try:
            resp = sessao.get(atual, timeout=TEMPO_LIMITE, allow_redirects=False, stream=True)
        except requests.exceptions.SSLError:
            raise ErroScanner("O certificado de segurança (HTTPS) do site tem problema e não foi possível abrir a página.")
        except requests.exceptions.Timeout:
            raise ErroScanner("O site demorou demais para responder. Tente de novo em alguns minutos.")
        except requests.exceptions.RequestException:
            raise ErroScanner("Não foi possível acessar o site. Ele pode estar fora do ar.")

        if resp.is_redirect or resp.is_permanent_redirect:
            destino = resp.headers.get("Location")
            resp.close()
            if not destino:
                raise ErroScanner("O site redirecionou sem informar o destino.")
            atual = urljoin(atual, destino)
            continue

        if resp.status_code >= 400:
            resp.close()
            raise ErroScanner(f"O site respondeu com erro {resp.status_code}. Confira se o endereço está certo.")
        tipo = resp.headers.get("Content-Type", "")
        if "html" not in tipo.lower():
            resp.close()
            raise ErroScanner("O endereço não é uma página da web (HTML).")

        corpo = b""
        for pedaco in resp.iter_content(64 * 1024):
            corpo += pedaco
            if len(corpo) > TAMANHO_MAXIMO:
                resp.close()
                raise ErroScanner("A página é grande demais para ser analisada.")
        resp.encoding = resp.encoding or resp.apparent_encoding
        return atual, corpo.decode(resp.encoding or "utf-8", errors="replace")

    raise ErroScanner("O site redirecionou muitas vezes seguidas.")


# --------------------------------------------------------------------------- 2. verificações

def _trecho(tag, limite=200) -> str:
    """Pedaço do HTML do elemento, para mostrar onde está o problema."""
    texto = re.sub(r"\s+", " ", str(tag)).strip()
    return texto if len(texto) <= limite else texto[: limite - 3] + "..."


def _linha(tag) -> str:
    return f"linha {tag.sourceline}" if getattr(tag, "sourceline", None) else ""


def _oculto(tag) -> bool:
    """Elementos escondidos (e o que está dentro deles) não chegam ao leitor de tela, então não contam."""
    for t in [tag, *tag.parents]:
        if getattr(t, "name", None) is None:
            continue
        if t.name in ("noscript", "template"):
            return True
        if t.has_attr("hidden") or (t.get("aria-hidden") or "").lower() == "true":
            return True
        estilo = (t.get("style") or "").replace(" ", "").lower()
        if "display:none" in estilo or "visibility:hidden" in estilo:
            return True
        if t.name == "input" and (t.get("type") or "").lower() == "hidden":
            return True
    return False


def _tem_nome_aria(tag, sopa) -> bool:
    if (tag.get("aria-label") or "").strip() or (tag.get("title") or "").strip():
        return True
    ids = (tag.get("aria-labelledby") or "").split()
    return any(sopa.find(id=i) and sopa.find(id=i).get_text(strip=True) for i in ids)


def _nome_visivel(tag) -> str:
    """Texto do elemento, contando o alt das imagens dentro dele."""
    partes = [tag.get_text(" ", strip=True)]
    partes += [(img.get("alt") or "").strip() for img in tag.find_all("img")]
    partes += [(svg.get("aria-label") or "").strip() for svg in tag.find_all("svg")]
    return " ".join(p for p in partes if p).strip()


def analisar_html(html: str) -> list[Ocorrencia]:
    sopa = BeautifulSoup(html, "html.parser")
    achados: list[Ocorrencia] = []

    def add(codigo, tag=None, local=""):
        if tag is not None and _oculto(tag):
            return
        achados.append(Ocorrencia(codigo, _trecho(tag) if tag is not None else "", local or (_linha(tag) if tag is not None else "")))

    # Acessibilidade
    for img in sopa.find_all("img"):
        if not img.has_attr("alt") and not _tem_nome_aria(img, sopa) and img.get("role") != "presentation":
            add("img-sem-alt", img)
    for btn in sopa.find_all("input", attrs={"type": re.compile("^image$", re.I)}):
        if not (btn.get("alt") or "").strip() and not _tem_nome_aria(btn, sopa):
            add("img-sem-alt", btn)
    for quadro in sopa.find_all("iframe"):
        if not (quadro.get("title") or "").strip() and not _tem_nome_aria(quadro, sopa):
            add("iframe-sem-titulo", quadro)

    # Legibilidade
    html_tag = sopa.find("html")
    if html_tag is None or not (html_tag.get("lang") or "").strip():
        add("pagina-sem-idioma", local="tag <html>")
    titulo = sopa.find("title")
    if titulo is None or not titulo.get_text(strip=True):
        add("pagina-sem-titulo", local="tag <head>")

    # Navegação
    cabecalhos = sopa.find_all(re.compile(r"^h[1-6]$"))
    if not any(h.name == "h1" for h in cabecalhos):
        add("sem-h1", local="página inteira")
    anterior = 0
    for h in cabecalhos:
        nivel = int(h.name[1])
        if anterior and nivel > anterior + 1:
            add("titulos-fora-de-ordem", h, f"{_linha(h)}: h{anterior} seguido de h{nivel}".strip(": "))
        anterior = nivel

    # Experiência mobile
    viewport = sopa.find("meta", attrs={"name": re.compile("^viewport$", re.I)})
    if viewport is None:
        add("sem-viewport", local="tag <head>")
    else:
        conteudo = (viewport.get("content") or "").lower().replace(" ", "")
        maximo = re.search(r"maximum-scale=([\d.]+)", conteudo)
        if "user-scalable=no" in conteudo or "user-scalable=0" in conteudo or (maximo and float(maximo.group(1)) < 2):
            add("zoom-bloqueado", viewport)

    # Formulários
    ignorar = {"hidden", "submit", "button", "image", "reset"}
    for campo in sopa.find_all(["input", "select", "textarea"]):
        if campo.name == "input" and (campo.get("type") or "text").lower() in ignorar:
            continue
        rotulado = (
            _tem_nome_aria(campo, sopa)
            or (campo.get("id") and sopa.find("label", attrs={"for": campo["id"]}))
            or campo.find_parent("label")
        )
        if not rotulado:
            add("campo-sem-rotulo", campo)

    # Botões e links
    for link in sopa.find_all("a", href=True):
        nome = _nome_visivel(link)
        if not nome and not _tem_nome_aria(link, sopa):
            add("link-sem-nome", link)
        elif nome.lower().strip(" .:!>»→") in TEXTOS_GENERICOS and not _tem_nome_aria(link, sopa):
            add("link-generico", link)
    botoes = sopa.find_all("button") + sopa.find_all("input", attrs={"type": re.compile("^(submit|button|reset)$", re.I)})
    for b in botoes:
        nome = _nome_visivel(b) if b.name == "button" else (b.get("value") or "").strip()
        if not nome and not _tem_nome_aria(b, sopa):
            add("botao-sem-nome", b)

    return achados


# --------------------------------------------------------------------------- 3. pontuação

def calcular_pontuacao(achados: list[Ocorrencia]) -> tuple[float, dict[str, float]]:
    """Nota de cada categoria começa em 100. Cada tipo de problema encontrado desconta o peso da sua
    prioridade (crítico 30, importante 15, melhoria 5). Cada repetição do mesmo problema desconta
    mais 20% do peso, até no máximo o dobro. A nota geral é a média das categorias."""
    por_codigo: dict[str, int] = {}
    for o in achados:
        por_codigo[o.codigo] = por_codigo.get(o.codigo, 0) + 1

    notas = {cat: 100.0 for cat in CATEGORIAS_AVALIADAS}
    for codigo, qtd in por_codigo.items():
        item = POR_CODIGO[codigo]
        peso = PESO[item["prioridade"]]
        desconto = min(peso + peso * 0.2 * (qtd - 1), peso * 2)
        notas[item["categoria"]] -= desconto
    notas = {cat: round(max(0.0, n), 2) for cat, n in notas.items()}
    geral = round(sum(notas.values()) / len(notas), 2)
    return geral, notas


def faixa(nota) -> str:
    """Texto simples para a nota geral."""
    nota = float(nota)
    if nota >= 90:
        return "Muito bom"
    if nota >= 70:
        return "Bom, com pontos a corrigir"
    if nota >= 50:
        return "Precisa de atenção"
    return "Barreiras sérias"
