# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é este projeto

App Django para gerenciar a pauta do Conselho Gestor do Ibama — a reunião quinzenal (toda
sexta-feira) do presidente com diretores e seccionais. Diretorias/seccionais submetem sugestões de
pauta (deliberativas ou informativas) com contexto e link/processo SEI; a assessoria analisa e
registra a deliberação do presidente (aprovada, backlog ou recusada). O app tem duas metades
completamente diferentes:

- **Público, sem login**: quem submete pauta só se identifica com nome/e-mail/unidade — não há
  cadastro de conta.
- **Painel de gestão, com login**: só a assessoria opera essa parte, autenticada com um único
  superusuário Django. Não existe um segundo papel de "presidente" logado no sistema — a decisão do
  presidente é registrada manualmente pela assessoria depois da reunião/conversa.

O plano de design original (contexto, decisões e trade-offs) está em
`C:\Users\Ibama\.claude\plans\preciso-criar-um-aplicativo-dynamic-blum.md`.

## Comandos

Ambiente virtual em `.venv/` (Windows). Ativar ou chamar os binários diretamente:

```powershell
.\.venv\Scripts\python.exe manage.py runserver          # servidor de dev em http://127.0.0.1:8000/
.\.venv\Scripts\python.exe manage.py migrate             # aplicar migrations
.\.venv\Scripts\python.exe manage.py makemigrations pauta # gerar migration após mudar models.py
.\.venv\Scripts\python.exe manage.py createsuperuser      # criar usuário do painel de gestão
.\.venv\Scripts\python.exe manage.py test pauta           # rodar testes (pauta/tests.py)
.\.venv\Scripts\python.exe manage.py shell                # shell interativo com models carregados
```

Não rode `python`/`pip` globais — sempre pelo `.venv\Scripts\`. Dependências ficam em
`requirements.txt` (hoje só `Django`).

## Arquitetura

Projeto Django padrão com um único app (`pauta`) de propósito geral — não há apps separados para
autenticação/papéis porque o modelo de permissões é só "público" vs. "assessoria logada" (ver
`pauta/models.py`, `pauta/views.py`).

**Models (`pauta/models.py`)**:
- `Unidade` — três tipos (`DIRETORIA`, `SECCIONAL`, `CENTRAL`), pré-cadastradas via data
  migrations (não cadastro manual): `0002_seed_unidades_oficiais.py` cria as 5 diretorias
  (Dilic, Diqua, DBFlo, Dipro, Diplan) e as Supes por estado; `0004_ajusta_unidades_centrais.py`
  corrige isso removendo a Supes-DF (não existe — o DF é a sede central, não uma Supes
  decentralizada, restando 26 Supes estaduais) e adiciona os órgãos ligados diretamente à
  presidência no mesmo nível hierárquico (tipo `CENTRAL`): PFE, Auditoria Interna (Audit),
  Corregedoria (Coger), Ouvidoria (Ouv), Assessoria de Gestão Estratégica (Agest). Fontes nas
  próprias migrations. Novas unidades além dessas se cadastram via `/admin/`; as migrations usam
  `get_or_create` por sigla, então não duplicam se já existirem. **Não editar a migration 0002
  retroativamente** — correções de dados de unidades entram como nova migration (padrão já usado
  na 0004), preservando o histórico.
- `Reuniao` — data da reunião (sempre sexta-feira). `prazo_submissao` é calculado
  (`data - 7 dias`), não armazenado. `esta_aberta` combina esse prazo com o campo `status` para
  decidir se a submissão pública deve ser aceita — essa é a trava de prazo do app inteiro.
  `Reuniao.proxima_aberta()` é usado tanto no formulário público quanto no painel para achar a
  reunião "corrente". **Usa `django.utils.timezone.localdate()`, nunca `datetime.date.today()`**
  para essas comparações — `date.today()` lê o relógio do SO ignorando `TIME_ZONE`, o que gera
  prazo errado (até 3h de diferença) se o servidor rodar em UTC (comum em nuvem). Bug real
  encontrado e corrigido em 2026-07-05; não reintroduzir `date.today()` aqui.
  `Reuniao.garantir_proximas_semanas()` (desde 2026-07-06) cria automaticamente as próximas 8
  semanas de sextas-feiras como `Reuniao` (`status=ABERTA`, o default do model) sempre que
  `nova_pauta`, `gestao_painel` ou `AcaoPautaForm` são carregados — a assessoria não precisa mais
  cadastrar reunião nenhuma no `/admin/` no dia a dia; ela só escolhe/realoca a data de cada item
  pelo campo `reuniao` de `AcaoPautaForm` na hora de analisar. `/admin/` continua existindo só para
  exceções (ex.: fechar uma sexta sem reunião por feriado/recesso, mudando o `status` daquela
  `Reuniao` específica para `FECHADA`).
- `PautaItem` — o item de pauta em si. Guarda quem enviou (nome/e-mail, sem FK de usuário) e um
  `status` linear: `ENVIADA → EM_ANALISE → ANALISADA → (APROVADA | BACKLOG | RECUSADA)`. Em vez de
  uma tabela de histórico separada, os marcos de tempo (`enviado_em`, `analisado_em`,
  `decidido_em`) ficam como campos direto no item — isso é o que alimenta a timeline visual em
  "Acompanhar pauta". `analisado_em`/`decidido_em` são preenchidos automaticamente em
  `views.gestao_item_editar` na primeira vez que o status cruza aquele marco (não são editáveis
  direto no form). O campo `reuniao` **é editável** em `AcaoPautaForm` — é assim que a assessoria
  implementa "colocar em backlog para outra reunião": muda `status` para `BACKLOG` e reatribui
  `reuniao` na mesma tela/submissão. Sem esse campo o item ficaria preso para sempre à reunião
  original (gap real encontrado e corrigido em 2026-07-05).
- **Sem upload de arquivo.** O model já teve um campo `anexo` (`FileField`) com validação de
  extensão/tamanho; foi removido a pedido do usuário ("não quero carregar meu servidor") em
  2026-07-05 — ver migration `0006_remove_pautaitem_anexo.py`. `MEDIA_URL`/`MEDIA_ROOT` também
  foram removidos de `settings.py`/`urls.py`. O contexto para o presidente é só texto
  (`contexto`) + `link_sei`; não reintroduzir upload de arquivo sem pedido explícito do usuário.

**Views (`pauta/views.py`)** — cada view corresponde a uma página, sem DRF/API, só forms + templates
server-side:
- `nova_pauta` — pública. Bloqueia POST no servidor (não só na UI) se `Reuniao.proxima_aberta()` for
  `None` ou não estiver `esta_aberta`.
- `acompanhar` — pública, busca por `email_solicitante` via querystring GET (por design: sem senha,
  então usa GET para ser algo compartilhável/sem CSRF).
- `gestao_painel`, `gestao_item_editar`, `gestao_pauta_final` — atrás de `@login_required`
  (`LOGIN_URL` aponta pro login customizado em `pauta/urls.py`, reaproveitando
  `django.contrib.auth`, sem sistema de senha próprio). Depois de salvar, `gestao_item_editar`
  redireciona para si mesmo (não para o painel) para que o resumo copiável já apareça atualizado.

**Sem envio automático de e-mail** (decisão revertida em 2026-07-05 — chegou a existir uma versão
com `send_mail`, removida porque não havia SMTP real configurado). Em vez disso,
`pauta/resumo.py::montar_resumo_status(request, item)` monta um texto pronto (destinatário,
assunto, corpo, link de acompanhamento) que `gestao_item_editar.html` mostra numa textarea readonly
com botão "Copiar texto" (clipboard API) e um link `mailto:` — a assessoria copia/cola ou abre no
próprio cliente de e-mail manualmente. Não reintroduzir envio automático sem antes confirmar que
existe SMTP configurado (`EMAIL_HOST` etc. não existem mais em `settings.py`).

**Templates** — `templates/base.html` é o layout com navbar/Bootstrap; todo template de página
estende ele. CSS institucional fica em `static/css/style.css`, carregado via `STATICFILES_DIRS`.
Bootstrap 5 e Bootstrap Icons vêm de CDN (jsdelivr) — o app depende de internet para o CSS/JS de
terceiros, não é self-contained.

**Fluxo ponta a ponta**: submissão pública cria `PautaItem` preso à `Reuniao.proxima_aberta()` →
assessoria vê no kanban de `gestao_painel` (agrupado por `status`) → abre `gestao_item_editar` para
registrar parecer/decisão e avançar `status` → itens `APROVADA` aparecem em `gestao_pauta_final`
(página imprimível, ordenada por `ordem_apresentacao`) → o solicitante original confere tudo isso
de volta em `acompanhar` pelo e-mail que usou.

## Convenções deste projeto

- Interface toda em português (pt-BR), incluindo `verbose_name`/labels de models e forms.
- `TIME_ZONE` é `America/Sao_Paulo`; datas de reunião são sempre sextas-feiras por convenção de
  domínio, mas isso não é validado no model — é responsabilidade de quem cadastra em `/admin/`.
- Nenhuma notificação é enviada automaticamente pelo sistema — ver seção "Sem envio automático de
  e-mail" acima. O acompanhamento é manual (consulta pública) ou via resumo copiável para a
  assessoria mandar por conta própria.
- `PautaItem.tempo_solicitado_min` é um `PositiveIntegerField` com `choices` fixas (5, 10, 15, 30
  minutos — `PautaItem.TEMPO_CHOICES`), renderizado como `<select>`. Não trocar de volta para
  input numérico livre nem adicionar outros valores sem pedido explícito.

## Identidade visual (skill `ibama-visual-identity`)

O visual segue a skill do claude.ai `ibama-visual-identity` (colada pelo usuário em 2026-07-05, não
instalada como skill do Claude Code — o conteúdo dela foi copiado manualmente para este projeto).
Tokens de cor/tipografia estão centralizados em `static/css/style.css` (`:root`), não devem ser
reinventados ad hoc em templates:

- **Paleta**: navy `#16316F` (títulos, cabeçalhos de tabela/kanban, rodapé), verde `#1DA838`
  (botão primário, acento), azul-água `#0093DD`, terracota `#9E441D`, mais os acentos gov.br (azul
  `#377EC1`, verde `#52AE32`, amarelo `#FBBA00`) usados só na faixa superior segmentada
  (`.faixa-topo` em `base.html`). Fundo é sempre branco — nunca usar fundo cheio colorido/navy numa
  página inteira.
- **Cores de status** (`badge-ENVIADA` … `badge-RECUSADA` em `style.css`) seguem a tabela
  sucesso/atenção/erro/informação do guia, mapeadas para os 6 status de `PautaItem`: `APROVADA`
  = sucesso (verde), `EM_ANALISE` = atenção (âmbar), `ANALISADA` = tom navy, `ENVIADA` =
  informação (azul), `BACKLOG` = terracota, `RECUSADA` = erro (vermelho). Ao adicionar um status
  novo, escolher uma dessas 4 famílias de cor, não inventar uma nova.
- **Logo**: arquivo oficial em `static/img/logo_ibama.png` (PNG com canal alfa, copiado de
  `OneDrive - ibama.gov.br\Ibama\4. Icones\Logo_IBAMA.svg.png` em 2026-07-05). Usado direto
  (fundo branco) no navbar de `base.html`; no rodapé (fundo navy) fica dentro de
  `.logo-respaldo`, o círculo branco que a skill exige atrás da logo sobre fundo escuro. Nunca
  recriar a logo — se precisar de outro tamanho/corte, reexportar a partir desse mesmo arquivo.
- **Tipografia**: `font-family` declarada como `"Rawline"` com fallback de sistema; não é
  necessário embutir a fonte (mesma orientação da skill para PPTX/DOCX).
- Regras não aplicadas por não fazerem sentido num app web (a skill foi escrita para
  PPTX/DOCX/telas estáticas): numeração de página "X de Y" e barra de rodapé fixa por slide/página
  impressa — aqui o rodapé é um elemento de layout HTML normal, sem paginação.

## Deploy e infraestrutura

- **Repositório:** https://github.com/SilencedTunic/conselho-gestor-ibama (branch `main`).
- **Hospedagem:** Render (render.com), via Blueprint declarado em `render.yaml` na raiz — cria só
  o web service. `SECRET_KEY` é gerada automaticamente pelo Render (`generateValue: true`);
  `DEBUG=False` vem fixo no blueprint.
- **Banco de dados: Postgres gratuito no Neon (neon.tech), não no Render.** Decisão tomada em
  2026-07-05 porque o Postgres free do próprio Render expira uns 30 dias após criado e depois é
  **excluído definitivamente** (14 dias de carência) — inviável para um app que roda por meses
  até migrar para a infraestrutura definitiva do Ibama. O plano free do Neon não expira. A
  connection string do Neon fica na variável de ambiente `DATABASE_URL` do serviço no Render
  (`sync: false` no `render.yaml` — preenchida manualmente no dashboard, nunca commitada).
  `dj_database_url` (usado em `settings.py`) já interpreta `sslmode` na query string da connection
  string do Neon sem nenhuma mudança de código.
- **Superusuário do painel de gestão é criado automaticamente no deploy**, não por
  `createsuperuser` interativo — o plano free do Render **não dá acesso a Shell/SSH** (restrito a
  planos pagos). O `startCommand` do `render.yaml` roda `python manage.py ensure_superuser`
  (comando em `pauta/management/commands/ensure_superuser.py`) depois do `migrate`: se as
  variáveis de ambiente `DJANGO_SUPERUSER_USERNAME`/`DJANGO_SUPERUSER_EMAIL`/
  `DJANGO_SUPERUSER_PASSWORD` estiverem definidas (`sync: false`, preenchidas no dashboard do
  Render), cria o usuário se não existir ou atualiza senha/permissões se já existir —
  idempotente, seguro rodar em todo deploy. Para resetar a senha do admin em produção, basta
  mudar `DJANGO_SUPERUSER_PASSWORD` no dashboard do Render e fazer um novo deploy (push, ou
  "Manual Deploy" no painel).
- **Plano free do Render hiberna o serviço após ~15 min sem tráfego** — a próxima requisição
  espera ~1 min até o container subir de novo, e nesse intervalo o navegador vê uma tela de
  "waking up" servida pelo **proxy do Render**, antes mesmo da requisição chegar ao Django (não
  tem opção documentada de customizar essa tela a partir do repositório). Mitigação em vigor desde
  2026-07-06: um cronjob gratuito no cron-job.org bate na URL pública (rota `/`, `views.nova_pauta`)
  a cada 10 minutos só para resetar o timer de inatividade do Render — qualquer requisição HTTP
  serve para isso, não precisou de nenhum endpoint novo no app. Se a tela de "waking up" voltar a
  aparecer, o cronjob provavelmente parou (conta expirada, etc.) — não é regressão de código.
- **O deploy é automático a cada push para `main`** — o Render está conectado ao GitHub e
  redeploya sozinho (build: `pip install` + `collectstatic`; start: `migrate` + `ensure_superuser`
  + `gunicorn`, todos definidos no `render.yaml`). Por isso, **toda modificação neste projeto
  termina com commit + push, não só a edição local** — uma mudança só "pronta no disco" não chega
  a lugar nenhum. Isso vale tanto para código quanto para o próprio `CLAUDE.md`.
- Fluxo de commit+push nesta máquina (Windows): o Git foi instalado via `winget`, mas o PATH da
  sessão de terminal do Claude Code não pega a atualização automaticamente — refrescar antes de
  qualquer comando `git`:
  ```powershell
  $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
  git add -A
  git commit -m "descrição objetiva da mudança"
  git push
  ```
- Identidade de commit configurada localmente neste repositório (não global no Windows):
  `user.name = "Ibama - Assessoria da Presidencia"`.

## Verificação manual (jornadas testadas em 2026-07-05)

App testado de ponta a ponta simulando solicitante, assessoria e presidente (via requisições HTTP
diretas ao `runserver`, não é uma suíte automatizada em `pauta/tests.py`). Cobertura: submissão
pública + bloqueio de prazo, e-mail malformado, múltiplas reuniões no kanban (incluindo reunião
vazia), pipeline completo de status com timestamps, reatribuição de reunião (backlog), geração da
pauta final, proteção de login em todas as rotas `/gestao/*`. Screenshots via Edge headless
(`msedge --headless=new --screenshot=...`) confirmaram a identidade visual, mas **captura em
viewport estreito (mobile) neste ambiente sandboxed corta texto mesmo em HTML puro sem CSS** — é
limitação da ferramenta, não do app; não confiar em screenshot mobile deste ambiente como prova de
bug de responsividade sem checar primeiro com uma página mínima de controle.

## Manutenção deste arquivo

Sempre que uma alteração mudar a arquitetura, os models, o fluxo de status ou os comandos de
desenvolvimento descritos acima, atualize este CLAUDE.md como parte da mesma alteração — não deixe
para depois.

**Toda alteração neste projeto (código ou este arquivo) termina com commit + push para `main`**
(ver seção "Deploy e infraestrutura") — é isso que faz o Render atualizar o app no ar sozinho.
Terminar uma tarefa sem esse passo deixa a mudança só local, sem efeito nenhum no link público.
