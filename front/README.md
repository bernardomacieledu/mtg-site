# MTG Nexus — Stack Completa

```
api/   → Django REST Framework (Python)
front/ → Vue 3 + Vite + Axios (Node.js)
```

---

## 🐍 API Django (`api/`)

### Instalar

```bash
cd api/

# Opção 1: mysqlclient (mais rápido, precisa de libs C)
pip install -r requirements.txt

# Opção 2: se mysqlclient falhar
pip install django djangorestframework django-cors-headers pymysql
```

### Rodar

```bash
python manage.py runserver 0.0.0.0:8000
```

### Endpoints disponíveis

| Método | URL | Descrição |
|--------|-----|-----------|
| GET | `/api/cards/` | Cartas paginadas (params: q, set, rarity, page) |
| GET | `/api/cards/images/?name=X` | Todas as artes de uma carta |
| GET | `/api/collections/` | Sets agrupados por ano |
| GET | `/api/rules/?q=X` | Regras por capítulo |
| GET | `/api/symbols/` | Mapa de símbolos de mana |
| GET | `/api/sets/` | Lista de sets para filtro |

---

## 🟢 Frontend Vue (`front/`)

### 1. Instalar Node.js (se não tiver)

**Debian/Ubuntu:**
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version   # deve mostrar v20.x
npm --version
```

**Verificar se já tem:**
```bash
node --version
npm --version
```

### 2. Instalar dependências e rodar

```bash
cd front/
npm install
npm run dev
```

Acesse: http://localhost:5173

> O Vite proxy redireciona `/api` → `http://127.0.0.1:8000` automaticamente no dev.

### 3. Build para produção

```bash
npm run build
# Gera a pasta dist/ com os arquivos estáticos prontos
```

---

## 🚀 Produção (servidor Debian/Ubuntu)

### Servir o Vue com Nginx

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    # Frontend Vue (dist/)
    root /var/www/mtg-nexus/front/dist;
    index index.html;
    location / { try_files $uri $uri/ /index.html; }

    # API Django (proxy)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Django com Gunicorn

```bash
pip install gunicorn
cd api/
gunicorn core.wsgi:application --bind 127.0.0.1:8000 --workers 3
```

---

## 🗂️ Estrutura de arquivos

```
front/src/
├── main.js
├── App.vue              ← Navbar + roteamento
├── style.css            ← Design system medieval global
├── router/index.js      ← Vue Router (/, /colecoes, /regras)
├── composables/
│   ├── api.js           ← Cliente Axios
│   └── useMana.js       ← Renderizador de símbolos de mana
├── components/
│   ├── CardItem.vue     ← Card com troca de arte por set
│   ├── SearchBar.vue    ← Filtros medievais
│   └── Pagination.vue
└── views/
    ├── CardsView.vue        ← Catálogo principal
    ├── CollectionsView.vue  ← Sets por ano
    └── RulesView.vue        ← Compêndio com sidebar
```
