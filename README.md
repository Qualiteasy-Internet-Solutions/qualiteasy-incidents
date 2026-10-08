# Qualiteasy · prova multientitat amb GLPI

Aquesta branca recull la prova local de GLPI 11 com a possible base de la gestió d'incidències. Es va provar separadament de Zammad, amb dues entitats fictícies i tiquets sintètics. Les dades i contrasenyes del Docker local **no** formen part del repositori públic.

## Arrencada

1. Crea `.env` amb `GLPI_DB_PASSWORD=` i una contrasenya aleatòria pròpia. No la publiquis.
2. Executa `docker compose up -d`. La UI s'exposa només a `http://127.0.0.1:8090`.
3. Completa la instal·lació inicial, canvia els comptes per defecte i crea les entitats i usuaris de prova indicats a [PROVA_MULTIENTITAT.md](PROVA_MULTIENTITAT.md).

La configuració operativa de la prova original viu al volum Docker local, no a la branca Git. Per repetir-la en una altra màquina s'han de recrear les entitats, els perfils i els casos de prova. Aquest és el treball pendent per convertir-la en una prova automatitzada.

## Estat de la decisió

GLPI permet compartimentació per entitats dins d'una instància, i l'aïllament bàsic es va observar a la UI i l'API. Encara falta provar un perfil Brigada amb restriccions de transició, l'experiència mòbil, les fotografies, el flux complet d'Alella i el cost d'operació per molts clients. La decisió GLPI/Zammad continua oberta.

La [branca demo-estatica](https://github.com/Qualiteasy-Internet-Solutions/qualiteasy-incidents/tree/demo-estatica) conté la demostració pública sense backend.
