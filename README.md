# Gestor d’incidències Qualiteasy · prova Zammad

Aquesta branca conserva el prototip local d'un flux municipal d'incidències: formulari mòbil simple, panell municipal, assignació, pretancament, validació, ordre de treball, mapa i derivació a NC de prova. També conté els ajustos de tema de la interfície nativa i el script de configuració per API.

## Arrencada local

El `docker-compose.yml` i `.env.dist` provenen de [zammad-docker-compose](https://github.com/zammad/zammad-docker-compose), revisió `9ba7510`, sota la llicència adjunta. Cal Docker amb prou memòria i només s'ha d'exposar el port a localhost en aquesta prova.

1. Copia `.env.dist` a `.env`, defineix una contrasenya pròpia a `POSTGRES_PASS` i posa `NGINX_EXPOSE_PORT=127.0.0.1:8084`. No publiquis `.env`.
2. Executa `docker compose up -d` i acaba la configuració inicial de Zammad.
3. Crea un token API de prova amb permisos administratius i desa'l a `.zammad-api-token` amb permisos `0600`.
4. Executa `python3 poc_api.py configure --base-url http://127.0.0.1:8084`. Si crea atributs nous, reinicia els serveis de Zammad.
5. Executa `ZAMMAD_URL=http://127.0.0.1:8084 python3 -B mobile-intake/dashboard_server.py` i obre `http://127.0.0.1:8083/demo`.

Els casos i usuaris creats a la instància Docker local original no s'han publicat: s'han mantingut fora del repositori els registres derivats de dades de client. Per repetir el flux, crea casos ficticis des de l'aplicació o amb `python3 poc_api.py ticket --base-url http://127.0.0.1:8084`. Els sis perfils del panell són simulats; la capa de flux desa metadades en un SQLite local ignorat per Git. Els fitxers i estats del Zammad local són als volums Docker.

## Límits de l'experiment

Zammad gestiona tiquets, però no proporciona aïllament multitenant fort dins d'una sola instància. El prototip no és una autorització de producció, ni envia WhatsApp real, ni crea NC al backend Qualiteasy. La [branca demo-estatica](https://github.com/Qualiteasy-Internet-Solutions/qualiteasy-incidents/tree/demo-estatica) és la versió pública sense backend per ensenyar el recorregut.
