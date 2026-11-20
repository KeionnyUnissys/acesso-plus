"""Catálogo de problemas que o scanner sabe encontrar.

Versão inicial escrita para a entrega de 19/11. A Maria Eduarda pode revisar os textos:
basta editar as frases aqui e rodar `flask --app run init-db` de novo (os registros são atualizados).

Cada item: código usado pelo scanner, categoria, prioridade, título, o que é, quem é afetado e como corrigir.
"""

CATALOGO = [
    {
        "codigo": "img-sem-alt",
        "aprovado": "Todas as imagens têm texto alternativo",
        "categoria": "Acessibilidade",
        "prioridade": "CRITICO",
        "titulo": "Imagem sem texto alternativo",
        "descricao": "A imagem não tem o atributo alt, que descreve o que ela mostra.",
        "impacto": "Pessoas cegas que usam leitor de tela não sabem o que a imagem mostra. O leitor costuma ler só o nome do arquivo.",
        "recomendacao": "Adicione alt com uma descrição curta, por exemplo alt=\"Fachada da loja\". Se a imagem for só enfeite, use alt=\"\".",
    },
    {
        "codigo": "iframe-sem-titulo",
        "aprovado": "Conteúdos incorporados têm título",
        "categoria": "Acessibilidade",
        "prioridade": "IMPORTANTE",
        "titulo": "Conteúdo incorporado sem título",
        "descricao": "Um mapa, vídeo ou outro conteúdo incorporado (iframe) não tem o atributo title.",
        "impacto": "Quem usa leitor de tela ouve apenas \"quadro\" e não sabe o que há dentro dele.",
        "recomendacao": "Adicione title descrevendo o conteúdo, por exemplo title=\"Mapa com a localização da loja\".",
    },
    {
        "codigo": "pagina-sem-idioma",
        "aprovado": "O idioma da página está definido",
        "categoria": "Legibilidade",
        "prioridade": "IMPORTANTE",
        "titulo": "Página sem idioma definido",
        "descricao": "A tag <html> não informa o idioma da página (atributo lang).",
        "impacto": "O leitor de tela pode ler o texto em português com pronúncia de outro idioma, ficando incompreensível.",
        "recomendacao": "Use <html lang=\"pt-BR\"> no início da página.",
    },
    {
        "codigo": "pagina-sem-titulo",
        "aprovado": "A página tem título",
        "categoria": "Legibilidade",
        "prioridade": "IMPORTANTE",
        "titulo": "Página sem título",
        "descricao": "A página não tem a tag <title> ou ela está vazia.",
        "impacto": "Fica difícil identificar a aba no navegador, nos favoritos e nos resultados de busca. O leitor de tela não anuncia onde a pessoa está.",
        "recomendacao": "Coloque um <title> com o nome da empresa e da página, por exemplo \"Início | Padaria Pão Quente\".",
    },
    {
        "codigo": "sem-h1",
        "aprovado": "A página tem título principal (h1)",
        "categoria": "Navegação",
        "prioridade": "IMPORTANTE",
        "titulo": "Página sem título principal (h1)",
        "descricao": "A página não tem um título principal marcado com <h1>.",
        "impacto": "Quem navega pelos títulos com leitor de tela não encontra o assunto principal da página. Buscadores também usam o h1.",
        "recomendacao": "Marque o título principal da página com <h1>, uma única vez.",
    },
    {
        "codigo": "titulos-fora-de-ordem",
        "aprovado": "Os títulos seguem uma ordem lógica",
        "categoria": "Navegação",
        "prioridade": "MELHORIA",
        "titulo": "Títulos fora de ordem",
        "descricao": "Os títulos pulam níveis, por exemplo de <h2> direto para <h4>.",
        "impacto": "A estrutura da página fica confusa para quem navega pelos títulos com leitor de tela.",
        "recomendacao": "Use os níveis em sequência: h1 para o título principal, h2 para seções, h3 para subseções.",
    },
    {
        "codigo": "sem-viewport",
        "aprovado": "A página se ajusta à tela do celular",
        "categoria": "Experiência mobile",
        "prioridade": "CRITICO",
        "titulo": "Página não ajustada para celular",
        "descricao": "Falta a tag <meta name=\"viewport\">, que adapta a página à tela do celular.",
        "impacto": "No celular a página aparece minúscula e a pessoa precisa dar zoom e arrastar para ler. Afeta principalmente idosos e pessoas com baixa visão.",
        "recomendacao": "Adicione <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> dentro do <head>.",
    },
    {
        "codigo": "zoom-bloqueado",
        "aprovado": "O zoom no celular está liberado",
        "categoria": "Experiência mobile",
        "prioridade": "IMPORTANTE",
        "titulo": "Zoom bloqueado no celular",
        "descricao": "A página impede que a pessoa aumente o texto com os dedos (user-scalable=no ou maximum-scale baixo).",
        "impacto": "Pessoas com baixa visão não conseguem ampliar o texto para ler.",
        "recomendacao": "Retire user-scalable=no e maximum-scale da tag viewport.",
    },
    {
        "codigo": "campo-sem-rotulo",
        "aprovado": "Os campos de formulário têm rótulo",
        "categoria": "Formulários",
        "prioridade": "CRITICO",
        "titulo": "Campo de formulário sem rótulo",
        "descricao": "Um campo para preencher não tem <label> ligado a ele nem outra forma de nome acessível.",
        "impacto": "Quem usa leitor de tela não sabe o que digitar. O texto de exemplo (placeholder) some ao começar a digitar e não substitui o rótulo.",
        "recomendacao": "Ligue um <label for=\"id-do-campo\"> ao campo, por exemplo <label for=\"email\">E-mail</label>.",
    },
    {
        "codigo": "link-sem-nome",
        "aprovado": "Todos os links têm nome",
        "categoria": "Botões e links",
        "prioridade": "CRITICO",
        "titulo": "Link sem nome",
        "descricao": "O link não tem texto nem descrição, geralmente porque é só um ícone ou uma imagem sem alt.",
        "impacto": "O leitor de tela anuncia apenas \"link\", sem dizer para onde ele leva. Comum em ícones de WhatsApp e redes sociais.",
        "recomendacao": "Coloque um texto no link ou aria-label, por exemplo aria-label=\"Falar no WhatsApp\".",
    },
    {
        "codigo": "botao-sem-nome",
        "aprovado": "Todos os botões têm nome",
        "categoria": "Botões e links",
        "prioridade": "CRITICO",
        "titulo": "Botão sem nome",
        "descricao": "O botão não tem texto nem descrição, geralmente porque é só um ícone.",
        "impacto": "Quem usa leitor de tela não sabe o que o botão faz, por exemplo se ele envia, busca ou fecha algo.",
        "recomendacao": "Escreva o texto no botão ou use aria-label, por exemplo aria-label=\"Buscar\".",
    },
    {
        "codigo": "link-generico",
        "aprovado": "Os links dizem para onde levam",
        "categoria": "Botões e links",
        "prioridade": "MELHORIA",
        "titulo": "Link com texto genérico",
        "descricao": "O texto do link não diz para onde ele leva, como \"clique aqui\" ou \"saiba mais\".",
        "impacto": "Fora do contexto, por exemplo em uma lista de links do leitor de tela, vários \"saiba mais\" iguais não ajudam a escolher.",
        "recomendacao": "Use um texto que explique o destino, por exemplo \"Ver o cardápio completo\".",
    },
]

POR_CODIGO = {item["codigo"]: item for item in CATALOGO}
TEXTO_APROVADO = {item["codigo"]: item["aprovado"] for item in CATALOGO}


def garantir_catalogo(db):
    """Cadastra ou atualiza as categorias e os problemas do catálogo. Pode ser chamada várias vezes."""
    from .cli import CATEGORIAS
    from .models import Categoria, Problema

    categorias = {}
    for nome, desc in CATEGORIAS:
        cat = db.session.execute(db.select(Categoria).filter_by(nome=nome)).scalar()
        if cat is None:
            cat = Categoria(nome=nome, descricao=desc)
            db.session.add(cat)
        categorias[nome] = cat
    db.session.flush()

    for item in CATALOGO:
        prob = db.session.execute(db.select(Problema).filter_by(codigo=item["codigo"])).scalar()
        if prob is None:
            prob = Problema(codigo=item["codigo"])
            db.session.add(prob)
        prob.categoria = categorias[item["categoria"]]
        prob.titulo = item["titulo"]
        prob.descricao = item["descricao"]
        prob.impacto = item["impacto"]
        prob.recomendacao = item["recomendacao"]
        prob.prioridade_padrao = item["prioridade"]
    db.session.commit()
    return categorias
