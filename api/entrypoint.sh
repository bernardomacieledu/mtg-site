#!/bin/sh
set -e

echo "==> [1/4] Aguardando o banco em ${DB_HOST:-db}:${DB_PORT:-3306}..."
python manage.py wait_for_db --timeout "${DB_WAIT_TIMEOUT:-180}"

echo "==> [2/4] Verificando o schema das tabelas legadas (cards, rules)..."
if ! python manage.py card_count > /dev/null 2>&1; then
  echo "    !! Tabela 'cards' nao encontrada. O volume do MySQL provavelmente foi"
  echo "    !! criado antes do docker/mysql/init/01-schema.sql existir."
  echo "    !! Rode: docker compose down -v && docker compose up --build"
else
  echo "    schema OK ($(python manage.py card_count) cartas no banco)."
fi

echo "==> [3/4] Aplicando migrations..."
python manage.py migrate --noinput

echo "==> [4/4] Carga inicial de cartas..."
if [ "${SEED_ON_START:-0}" = "1" ]; then
  COUNT=$(python manage.py card_count 2>/dev/null || echo 0)
  if [ "$COUNT" = "0" ]; then
    echo "    Banco vazio. Importando as ${SEED_RECENT_SETS:-8} colecoes mais recentes"
    echo "    do Scryfall EM SEGUNDO PLANO (alguns minutos)."
    echo "    O site ja fica utilizavel; as cartas aparecem conforme sao gravadas."
    echo "    Progresso: docker compose exec api python manage.py card_count"
    echo "    ou acesse http://localhost:8000/api/health/"
    (
      python manage.py seed_cards --recent "${SEED_RECENT_SETS:-8}" \
        && echo "==> SEED CONCLUIDO: $(python manage.py card_count) cartas no banco." \
        || echo "!! Seed falhou. Rode: docker compose exec api python manage.py seed_cards --recent 8"
    ) &
  else
    echo "    Banco ja possui $COUNT cartas, pulando seed."
  fi
else
  echo "    SEED_ON_START=0, pulando."
fi

echo "==> API pronta em http://localhost:${API_PORT:-8000}/api/"
exec "$@"
