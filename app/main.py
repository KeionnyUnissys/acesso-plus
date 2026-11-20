"""Páginas públicas e área logada."""
from urllib.parse import urlsplit

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from . import db
from . import scanner
from .catalogo import TEXTO_APROVADO, garantir_catalogo
from .forms import SiteForm
from .models import PRIORIDADES, Analise, Empresa, PontuacaoCategoria, Problema, ProblemaEncontrado, Site

bp = Blueprint("main", __name__)


def site_do_usuario(id_site):
    """Busca o site garantindo que ele pertence ao usuário logado (senão, 404)."""
    site = db.session.get(Site, id_site)
    if site is None or site.empresa.id_usuario != current_user.id_usuario:
        abort(404)
    return site


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/painel", methods=["GET", "POST"])
@login_required
def painel():
    form = SiteForm()
    if form.validate_on_submit():
        url = normalizar_url(form.url.data)
        if url is None:
            form.url.errors.append("Use um endereço público começando com http:// ou https://.")
        else:
            empresa = current_user.empresas[0]
            if any(s.url == url for s in empresa.sites):
                flash("Este site já está cadastrado.", "aviso")
            else:
                empresa.sites.append(Site(url=url))
                db.session.commit()
                flash("Site cadastrado.", "sucesso")
            return redirect(url_for("main.painel"))
    sites = (
        db.session.execute(
            db.select(Site).join(Empresa).filter(Empresa.id_usuario == current_user.id_usuario)
            .order_by(Site.data_cadastro.desc())
        ).scalars().all()
    )
    return render_template("painel.html", form=form, sites=sites)


@bp.route("/sites/<int:id_site>/remover", methods=["POST"])
@login_required
def remover_site(id_site):
    site = site_do_usuario(id_site)  # cada usuário só mexe nos próprios sites
    db.session.delete(site)
    db.session.commit()
    flash("Site removido.", "sucesso")
    return redirect(url_for("main.painel"))


@bp.route("/sites/<int:id_site>/analisar", methods=["POST"])
@login_required
def analisar_site(id_site):
    site = site_do_usuario(id_site)
    analise = executar_analise(site)
    if analise.status == "ERRO":
        return redirect(url_for("main.painel"))
    flash("Análise concluída.", "sucesso")
    return redirect(url_for("main.ver_analise", id_analise=analise.id_analise))


@bp.route("/analises/<int:id_analise>")
@login_required
def ver_analise(id_analise):
    analise = db.session.get(Analise, id_analise)
    if analise is None or analise.site.empresa.id_usuario != current_user.id_usuario or analise.status != "CONCLUIDA":
        abort(404)

    # Agrupa as ocorrências por tipo de problema, na ordem: crítico, importante, melhoria
    grupos = {}
    for oc in analise.problemas:
        g = grupos.setdefault(oc.id_problema, {"problema": oc.problema, "prioridade": oc.prioridade, "itens": []})
        g["itens"].append(oc)
    ordem = {p: i for i, p in enumerate(PRIORIDADES)}
    grupos = sorted(grupos.values(), key=lambda g: (ordem[g["prioridade"]], -len(g["itens"])))

    # Verificações em que o site passou (aparecem como "Aprovado")
    encontrados = [g["problema"].codigo for g in grupos]
    aprovados = db.session.execute(
        db.select(Problema).filter(Problema.codigo.not_in(encontrados)).order_by(Problema.id_problema)
    ).scalars().all()

    contagem = {p: sum(1 for g in grupos if g["prioridade"] == p) for p in PRIORIDADES}
    contagem["APROVADO"] = len(aprovados)
    pontuacoes = sorted(analise.pontuacoes, key=lambda p: p.categoria.nome)
    return render_template("analise.html", analise=analise, grupos=grupos, aprovados=aprovados,
                           contagem=contagem, pontuacoes=pontuacoes, faixa=scanner.faixa(analise.pontuacao_geral),
                           textos_aprovado=TEXTO_APROVADO,
                           historico=[a for a in analise.site.analises if a.status == "CONCLUIDA"][:10])


def executar_analise(site: Site) -> Analise:
    """Roda o scanner e grava a análise, as notas por categoria e os problemas encontrados."""
    categorias = garantir_catalogo(db)
    analise = Analise(site=site, status="PROCESSANDO")
    db.session.add(analise)
    db.session.commit()

    try:
        _, html = scanner.baixar_pagina(site.url)
        achados = scanner.analisar_html(html)
    except scanner.ErroScanner as erro:
        analise.status = "ERRO"
        db.session.commit()
        flash(str(erro), "erro")
        return analise

    geral, notas = scanner.calcular_pontuacao(achados)
    analise.pontuacao_geral = geral
    for nome_cat, nota in notas.items():
        analise.pontuacoes.append(PontuacaoCategoria(categoria=categorias[nome_cat], pontuacao=nota))
    problemas = {p.codigo: p for p in db.session.execute(db.select(Problema)).scalars()}
    for oc in achados:
        analise.problemas.append(ProblemaEncontrado(
            problema=problemas[oc.codigo], prioridade=oc.prioridade,
            elemento_afetado=oc.elemento[:255] or None, localizacao=oc.localizacao or None,
        ))
    analise.status = "CONCLUIDA"
    db.session.commit()
    return analise


def normalizar_url(bruta: str):
    """Aceita só http/https com domínio. Bloqueia endereços locais (o scanner não deve acessar a rede interna)."""
    texto = bruta.strip()
    if "://" not in texto:
        texto = "https://" + texto
    partes = urlsplit(texto)
    if partes.scheme not in ("http", "https") or not partes.hostname:
        return None
    host = partes.hostname.lower()
    if host in ("localhost",) or host.endswith(".local") or host.startswith(("127.", "10.", "192.168.", "0.")) or host == "::1":
        return None
    if "." not in host:
        return None
    caminho = partes.path or "/"
    return f"{partes.scheme}://{host}{(':' + str(partes.port)) if partes.port else ''}{caminho}"
