#!/bin/sh
set -e

echo "==> Aguardando MySQL em ${DB_HOST:-db}:${DB_PORT:-3306}..."
until mysqladmin ping -h "${DB_HOST:-db}" -P "${DB_PORT:-3306}" \
      -u "${DB_USER:-mtg_ingest}" -p"${DB_PASSWORD:-mtgpass}" --silent 2>/dev/null; do
  sleep 2
done
echo "==> MySQL disponivel."

echo "==> Verificando o schema das tabelas legadas (cards, rules)..."
if ! python manage.py card_count > /dev/null 2>&1; then
  echo "!! Tabela 'cards' nao encontrada. Isso acontece quando o volume do MySQL"
  echo "!! foi criado antes do docker/mysql/init/01-schema.sql existir."
  echo "!! Rode: docker compose down -v && docker compose up --build"
fi

echo "==> Aplicando migrations..."
python manage.py migrate --noinput

if [ "${SEED_ON_START:-0}" = "1" ]; then
  COUNT=$(python manage.py card_count 2>/dev/null || echo 0)
  if [ "$COUNT" = "0" ]; then
    # Roda em segundo plano: a API sobe na hora e as cartas vao aparecendo
    # conforme sao gravadas. Antes o gunicorn so subia no fim do download,
    # e o front respondia 502 durante varios minutos.
    echo "==> Banco vazio. Importando as ${SEED_RECENT_SETS:-8} colecoes mais recentes"
    echo "==> do Scryfall EM SEGUNDO PLANO. O site ja esta utilizavel; as cartas"
    echo "==> vao aparecendo conforme a importacao avanca (recarregue a pagina)."
    (
      python manage.py seed_cards --recent "${SEED_RECENT_SETS:-8}" \
        && echo "==> Seed concluido: $(python manage.py card_count) cartas no banco." \
        || echo "!! Seed falhou. Rode manualmente: docker compose exec api python manage.py seed_cards --recent 8"
    ) &
  else
    echo "==> Banco ja possui $COUNT cartas, pulando seed."
  fi
fi

echo "==> Iniciando servidor da API."
exec "$@"
