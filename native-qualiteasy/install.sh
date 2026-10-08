#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
rails=$(docker compose ps -q zammad-railsserver)
nginx=$(docker compose ps -q zammad-nginx)
[ -n "$rails" ] && [ -n "$nginx" ] || { echo "Arrenca primer els serveis Zammad" >&2; exit 1; }
if [ "${1:-}" != "--assets-only" ]; then
  docker cp native-qualiteasy/application.html.erb "$rails:/opt/zammad/app/views/layouts/application.html.erb"
fi
docker cp native-qualiteasy/public/. "$nginx:/opt/zammad/public/assets/qualiteasy/"
if [ "${1:-}" != "--assets-only" ]; then
  docker restart "$rails"
fi
printf '%s\n' 'Tema Qualiteasy copiat. Cap imatge ni contenidor reconstruït.'
