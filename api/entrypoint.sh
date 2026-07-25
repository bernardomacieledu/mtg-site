#!/bin/sh
set -e

echo "==> Aguardando MySQL em ${DB_HOST:-db}:${DB_PORT:-3306}..."
until mysqladmin ping -h "${DB_HOST:-db}" -P "${DB_PORT:-3306}" \
      -u "${DB_USER:-mtg_ingest}" -p"${DB_PASSWORD:-mtgpass}" --silent 2>/dev/null; do
  sleep 2
done
echo "==> MySQL disponivel."

echo "==> Aplicando migrations..."
python manage.py migrate --noinput

if [ "${SEED_ON_START:-0}" = "1" ]; then
  # Só popula se a tabela estiver vazia (evita re-download a cada restart)
  COUNT=$(python manage.py card_count 2>/dev/null || echo 0)
  if [ "$COUNT" = "0" ]; then
    echo "==> Banco vazio: importando as ${SEED_RECENT_SETS:-8} coleções mais recentes do Scryfall..."
    python manage.py seed_cards --recent "${SEED_RECENT_SETS:-8}" || echo "!! Seed falhou (siga sem dados; rode manualmente depois)."
  else
    echo "==> Banco já possui $COUNT cartas, pulando seed."
  fi
fi

exec "$@"
