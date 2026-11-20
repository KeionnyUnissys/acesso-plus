# Acesso+

Plataforma que analisa a página inicial do site de uma pequena empresa e mostra, em linguagem simples, as barreiras de acessibilidade encontradas.

Projeto do Laboratório de Inovação II (ADS-NOT 2A, 2026.2, Faculdade Senac DF).
Grupo: Keionny, Letícia e Maria Eduarda.

## O que já funciona

### Entrega de 12/11
- Cadastro de conta com nome, empresa, e-mail e senha.
- Login e logout.
- Senha guardada só como hash (scrypt), nunca em texto puro.
- Páginas internas bloqueadas para quem não entrou na conta.
- Cada usuário só vê e remove os próprios sites.
- Cadastro de sites. Endereços locais (localhost, rede interna) são recusados.
- Proteção contra CSRF em todos os formulários e cookies de sessão protegidos.

### Entrega de 19/11: scanner e score
- Botão **Analisar** em cada site do painel. O sistema baixa a página inicial e roda 12 verificações.
- Tela de resultado com nota geral (0 a 100), nota por categoria, problemas agrupados por prioridade
  (Crítico, Importante, Melhoria) e verificações aprovadas.
- Cada problema mostra **o que é**, **quem é afetado**, **como corrigir** e **onde está** (linha e trecho do HTML).
- Tudo fica gravado no banco: `analise`, `pontuacao_categoria` e `problema_encontrado`.
- Segurança do scanner: só acessa sites públicos (bloqueia IPs internos, inclusive após redirecionamento),
  limite de 10 s de espera e de 2 MB de página, mensagens claras quando o site está fora do ar.

**Demo de quinta:** entrar, colar uma URL em "Cadastrar um site", clicar em **Analisar** e mostrar a nota e os problemas.
Sites que funcionaram bem no teste de 15/11: `https://www.senac.br` (nota 68) e `https://www.gov.br/pt-br` (nota 92).
Conta de demonstração: `demo@exemplo.com.br`, senha `demo12345` (criada com `flask --app run criar-demo`).

### Entrega final (26/11): telas e acabamento
- Visual da Letícia aplicado em todas as telas (fonte Poppins, azul #2563EB, cartões, cabeçalho com logo e rodapé).
  As telas originais em HTML estático dela ficaram guardadas fora do projeto, na pasta de entregas.
- Ajustes de acessibilidade no visual: cores de texto com contraste de pelo menos 4,5:1, um único `<h1>` por página,
  logo do cabeçalho decorativa (`alt=""`, o nome "Acesso+" já aparece em texto) e foco visível.
- Versão para celular: no painel, cada site vira um cartão; botões ocupam a largura toda.
- Tela de resultado: seção **Por onde começar** (as 5 correções mais importantes), **Histórico deste site**
  (últimas análises com data e nota), botão **Salvar relatório em PDF** (usa a impressão do navegador) e **Analisar de novo**.
- Teste automático que roda o próprio scanner nas telas do Acesso+: todas passam nas 12 verificações.
- 26 testes automáticos passando.

### O que o scanner verifica

| Código | Categoria | Prioridade | Verificação |
|--------|-----------|------------|-------------|
| img-sem-alt | Acessibilidade | Crítico | Imagem sem texto alternativo |
| iframe-sem-titulo | Acessibilidade | Importante | Mapa/vídeo incorporado sem título |
| pagina-sem-idioma | Legibilidade | Importante | `<html>` sem `lang` |
| pagina-sem-titulo | Legibilidade | Importante | Sem `<title>` |
| sem-h1 | Navegação | Importante | Sem título principal `<h1>` |
| titulos-fora-de-ordem | Navegação | Melhoria | Títulos pulando nível (h2 → h4) |
| sem-viewport | Experiência mobile | Crítico | Sem ajuste para celular |
| zoom-bloqueado | Experiência mobile | Importante | Zoom bloqueado no celular |
| campo-sem-rotulo | Formulários | Crítico | Campo sem `<label>` |
| link-sem-nome | Botões e links | Crítico | Link só com ícone, sem nome |
| botao-sem-nome | Botões e links | Crítico | Botão só com ícone, sem nome |
| link-generico | Botões e links | Melhoria | "Clique aqui", "Saiba mais" |

Elementos escondidos (`display:none`, `hidden`, `aria-hidden="true"`, `<noscript>`) não contam, porque não chegam ao leitor de tela.

### Como a nota é calculada
- Cada categoria começa com 100.
- Cada **tipo** de problema encontrado desconta conforme a prioridade: Crítico 30, Importante 15, Melhoria 5.
- Cada repetição do mesmo problema desconta mais 20% do peso, até no máximo o dobro
  (ex.: 3 imagens sem alt = 30 + 6 + 6 = 42 pontos a menos em Acessibilidade).
- A nota nunca fica negativa. A **nota geral** é a média das 6 categorias.

Os textos dos problemas ficam em `sistema/catalogo.py` (versão inicial). A Maria Eduarda pode revisar as frases ali
e rodar `flask --app run init-db` para atualizar o banco.

## Próximas entregas

| Data  | O quê | Quem |
|-------|-------|------|
| 19/11 | ✅ Scanner, score geral e por categoria, tela de resultado (Letícia pode refazer o visual) | Keionny |
| 26/11 | ✅ Telas da Letícia integradas, histórico, PDF. Falta: slides e ensaio | Todas |
| 26/11 | Envio do código no Moodle (Atividade avaliativa 06) | Keionny |

## Como rodar no seu computador

Precisa ter o **Python 3.11 ou mais novo** instalado.

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

```bash
flask --app run init-db
```

Opcional, para criar a conta de demonstração:

```bash
flask --app run criar-demo
```

```bash
flask --app run run
```

Abra http://127.0.0.1:5000 no navegador.

O banco padrão é um arquivo SQLite em `instance/acesso_plus.db`, que não precisa de instalação. Para usar PostgreSQL, como no projeto físico, copie `.env.example` para `.env` e preencha `DATABASE_URL`.

## Rodar os testes

```bash
python -m pytest -q
```

## Onde fica cada coisa

O projeto é dividido em duas partes: **interface** (o que aparece na tela) e **sistema** (o código Python que faz o trabalho).

```
acesso-plus/
├── interface/              ← parte visual (Letícia)
│   ├── telas/              ← páginas em HTML
│   │   ├── base.html       ← cabeçalho, menu e rodapé usados por todas as telas
│   │   ├── index.html      ← página inicial
│   │   ├── painel.html     ← Meus sites
│   │   ├── analise.html    ← resultado da análise
│   │   ├── erro.html
│   │   ├── conta/          ← login.html e cadastro.html
│   │   └── componentes/    ← campo.html (campo de formulário reutilizado)
│   └── estaticos/
│       ├── css/estilo.css  ← todo o visual, dividido em 14 seções numeradas
│       ├── js/relatorio.js ← botão "Salvar relatório em PDF"
│       └── img/            ← logo e ícone
├── sistema/                ← código Python (Keionny)
│   ├── __init__.py         ← monta o app e liga a pasta interface/
│   ├── models.py           ← tabelas do banco (seguem o Projeto Físico)
│   ├── auth.py             ← cadastro, login e logout
│   ├── main.py             ← Meus sites e análises
│   ├── scanner.py          ← baixa a página, verifica e calcula a nota
│   ├── catalogo.py         ← textos dos problemas (Maria Eduarda revisa)
│   ├── forms.py            ← formulários e validações
│   └── cli.py              ← comandos init-db e criar-demo
├── banco_de_dados/         ← script SQL para PostgreSQL
├── testes/                 ← testes automáticos
├── config.py               ← configurações
└── run.py                  ← ponto de partida (flask --app run run)
```

As telas abertas direto no VS Code ou no navegador aparecem sem imagens e com os `{{ }}` à mostra, porque quem
preenche essas partes é o Flask. Para ver as telas de verdade, rode o sistema e abra http://127.0.0.1:5000.

### Para a Letícia (telas)

As telas usam Jinja, o HTML com `{{ }}` e `{% %}` do Flask. Pode mudar o HTML e o CSS à vontade. Só mantenha:

- os `name` dos campos e o `{{ form.hidden_tag() }}` dentro dos formulários;
- os `url_for(...)` dos links;
- os `<label>` ligados aos campos, porque o próprio Acesso+ precisa ser acessível.

### Para a Maria Eduarda (catálogo)

Cada problema do catálogo precisa de:

- **código**, por exemplo `img-sem-alt`;
- **categoria**: Acessibilidade, Legibilidade, Navegação, Experiência mobile, Formulários ou Botões e links;
- **título**;
- **o que é**;
- **quem é afetado**;
- **como corrigir**;
- **prioridade**: CRITICO, IMPORTANTE ou MELHORIA.

Pode montar numa planilha que depois vira os dados da tabela `problema`.

## Limite importante

A análise automática ajuda a encontrar barreiras, mas não garante que um site seja 100% acessível. Alguns critérios só uma pessoa consegue avaliar.
