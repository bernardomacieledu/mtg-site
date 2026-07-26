# MTG Nexus

Grimório de cartas, coleções e regras de Magic: The Gathering.
Backend em Django REST + MySQL, frontend em Vue 3 (Vite), tudo containerizado.

---

## Subindo em localhost

Pré-requisitos: Docker e Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

| Serviço  | URL                     |
|----------|-------------------------|
| Site     | http://localhost:8080   |
| API      | http://localhost:8000/api/ |
| MySQL    | localhost:3307          |
| Adminer  | http://localhost:8081   |
| Admin    | http://localhost:8000/admin/ |

No Adminer, entre com **Servidor** `db`, usuário e senha iguais aos do `.env`
(`DB_USER` / `DB_PASSWORD`) e base `mtg_db`.

No primeiro boot o container da API aguarda o MySQL, aplica as migrations e
importa as 8 coleções mais recentes do Scryfall (alguns minutos). Para pular a
carga inicial, use `SEED_ON_START=0` no `.env`.

### Carregando mais cartas

```bash
# as 20 coleções mais recentes
docker compose exec api python manage.py seed_cards --recent 20

# coleções específicas
docker compose exec api python manage.py seed_cards --sets blb,dsk,fdn

# regras abrangentes (baixe o .txt em https://magic.wizards.com/en/rules)
docker compose exec api python manage.py seed_rules --file /app/MagicCompRules.txt
```

### Comandos úteis

```bash
docker compose logs -f api      # acompanha a API
docker compose down             # para tudo
docker compose down -v          # para tudo e apaga o banco
```

---

## Desenvolvimento sem Docker

```bash
# Backend
cd api
pip install -r requirements.txt
export DB_HOST=127.0.0.1 DB_USER=mtg_ingest DB_PASSWORD=mtgpass DB_NAME=mtg_db
python manage.py migrate
python manage.py runserver

# Frontend (proxy /api -> 127.0.0.1:8000 já configurado no vite.config.js)
cd front
npm install
npm run dev
```

---

## Arquitetura

```
api/                 Django REST
  core/              settings (100% por variáveis de ambiente), urls, wsgi
  mtg_api/           cartas, coleções (sets), regras, import/export de listas
    management/commands/  seed_cards, seed_rules, card_count
  auth_app/          usuários (JWT), decks e coleções pessoais
front/               Vue 3 + Vite + Pinia
  src/composables/api.js   cliente HTTP único (injeta o JWT via interceptor)
  src/stores/              auth, collections
docker/mysql/init/   schema das tabelas legadas (cards, rules)
```

As tabelas `cards` e `rules` são `managed = False` no Django — o schema vive em
`docker/mysql/init/01-schema.sql` e é aplicado pelo MySQL no primeiro boot.

---

## Principais endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/cards/` | busca de cartas (`q`, `set`, `rarity`, `type`, `cmc`, `colors`, `page`) |
| GET | `/api/cards/images/?name=` | todas as impressões de uma carta |
| GET | `/api/collections/` | coleções do jogo, com bloco `latest` dos lançamentos recentes |
| GET | `/api/collections/<code>/` | resumo de uma coleção |
| GET | `/api/rules/` | regras abrangentes |
| POST | `/api/collection/import/` | interpreta uma decklist em texto |
| POST | `/api/auth/register/` · `/login/` · `/me/` | autenticação JWT |
| GET/POST | `/api/auth/collections/` · `/collections/save/` | coleções do usuário |
| PATCH/DELETE | `/api/auth/collections/<id>/rename/` · `/delete/` | edição |

---

## O que mudou nesta revisão

**Correções**
- `requirements.txt` não trazia `PyJWT` nem `PyMySQL`, ambos importados pelo código — a API não subia do zero.
- O token JWT não era enviado nas chamadas autenticadas: o store de auth escrevia em `axios.defaults`, mas as telas usavam uma instância criada com `axios.create()`, que copia os defaults na criação. Agora há um cliente único com interceptor.
- Rotas duplicadas em `mtg_api/urls.py` (`collection/import` e `collection/export` registradas 3×).
- `/api/cards/` respondia 500 com `page`, `cmc` ou datas inválidas na query string.
- Filtro de cor usava `LIKE '%W%'`, casando com qualquer letra do custo; agora considera símbolos e híbridos, e suporta incolor.
- O parser de decklist descartava silenciosamente linhas sem quantidade (`Lightning Bolt`); agora aceita `4x`, `SB:`, `(SET) 123` e cartas de dupla face.
- Import de lista fazia 2 queries por carta; passou a resolver tudo em uma consulta.
- `GROUP_CONCAT` truncava a lista de sets de cartas muito reimpressas.
- Busca de cartas disparava duas requisições por pesquisa e a paginação não ia para a URL.
- Biblioteca e detalhe de coleção liam apenas o `localStorage`, ignorando os dados do usuário logado.
- Credenciais e secrets deixaram de ser hardcoded; `.pyc` saíram do versionamento.

**Novidades**
- Página **Coleções** com próximos lançamentos e lançamentos recentes em destaque, busca e filtro por ano.
- Montagem de coleções carta a carta: botões `+`/`−` no grimório, dock flutuante de progresso e a tela `/colecao/montar`.
- Criar decks e coleções **exige conta**: os dados ficam no banco, vinculados ao usuário.
- Suporte a **múltiplas coleções por usuário** (antes havia só uma), com renomear, editar e excluir.
- Docker Compose completo com seed automático do banco.
