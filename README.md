# MTG Nexus

Grimório de cartas, coleções e regras de Magic: The Gathering.
Backend em Django REST + MySQL, frontend em Vue 3 (Vite), tudo containerizado.

---

## Usando o MariaDB do host (sem container de banco)

O `docker-compose.yml` não sobe um container de banco: `api`, `worker` e
`adminer` se conectam ao MariaDB/MySQL **já instalado na máquina**, via
`host.docker.internal`. Antes do primeiro `docker compose up`, prepare o
MariaDB do host:

### 1. Liberar conexões vindas do Docker

Por padrão o MariaDB do Debian só aceita conexão de `127.0.0.1` — os
containers nunca vão conseguir entrar, mesmo com usuário e senha certos.

```bash
sudo sed -i "s/^bind-address.*/bind-address = 0.0.0.0/" /etc/mysql/mariadb.conf.d/50-server.cnf
sudo systemctl restart mariadb
```

(o caminho do arquivo pode variar por distro; `sudo find /etc -name "*.cnf" | xargs grep -l bind-address` acha o correto)

### 2. Criar o banco, o usuário e o schema

```bash
sudo mysql -e "
CREATE DATABASE IF NOT EXISTS mtg_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'mtg_ingest'@'%' IDENTIFIED BY 'mtgpass';
GRANT ALL ON mtg_db.* TO 'mtg_ingest'@'%';
FLUSH PRIVILEGES;
SET GLOBAL group_concat_max_len=1000000;"

sudo mysql mtg_db < docker/mysql/init/01-schema.sql
```

Troque `mtgpass` por uma senha de verdade e repita no `DB_PASSWORD` do `.env`.
O `group_concat_max_len` não persiste após reiniciar o serviço; para deixar
permanente, adicione `group_concat_max_len = 1000000` na seção `[mysqld]` do
mesmo arquivo de configuração do bind-address.

### 3. Firewall local (se houver)

Se a máquina usa `ufw`/`iptables`, a rede de containers do Docker (tipicamente
`172.17.0.0/16` ou `172.18.0.0/16` — confirme com `docker network inspect
bridge`) precisa ter acesso à porta 3306. Numa instalação padrão sem regras
restritivas isso já funciona; só ajuste se `wait_for_db` ficar tentando sem
sucesso.

### 4. Testar antes de subir o compose

```bash
mysql -h 127.0.0.1 -u mtg_ingest -p mtg_db -e "SHOW TABLES;"
```

Se isso conectar, o Docker também vai conseguir.

---

## Subindo em localhost

Pré-requisitos: Docker, Docker Compose e o MariaDB do host configurado acima.

```bash
cp .env.example .env
docker compose up --build
```

| Serviço  | URL                     |
|----------|-------------------------|
| Site     | http://localhost:8080   |
| API      | http://localhost:8000/api/ |
| MariaDB  | localhost:3306 (do host, fora do compose) |
| Adminer  | http://localhost:8081   |
| Admin    | http://localhost:8000/admin/ |

No Adminer, entre com **Servidor** `host.docker.internal`, usuário e senha
iguais aos do `.env` (`DB_USER` / `DB_PASSWORD`) e base `mtg_db`.

No primeiro boot o container da API aguarda o MariaDB do host responder, aplica
as migrations e importa as 8 coleções mais recentes do Scryfall (alguns
minutos). Para pular a carga inicial, use `SEED_ON_START=0` no `.env`.

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
docker compose down -v          # para tudo (o banco não é afetado: vive no host)
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
