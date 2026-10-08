# Gestor d’incidències Qualiteasy · prova GLPI

Aquesta branca recull la prova local de GLPI 11 com a possible base de la gestió d'incidències. Es va provar separadament de Zammad, amb dues entitats fictícies i incidències sintètiques. Les dades i contrasenyes del Docker local **no** formen part del repositori públic.

## Arrencada

1. Crea `.env` amb `GLPI_DB_PASSWORD=` i una contrasenya aleatòria pròpia. No la publiquis.
2. Executa `docker compose up -d`. La UI s'exposa només a `http://127.0.0.1:8090`.
3. Completa la instal·lació inicial, canvia els comptes per defecte i crea les entitats i usuaris de prova indicats a [PROVA_MULTIENTITAT.md](PROVA_MULTIENTITAT.md).

La configuració operativa i els casos ficticis visibles de la prova original viuen al volum Docker local, no a la branca Git. Per repetir-la en una altra màquina s'han de recrear les entitats, els perfils i els casos de prova. Aquest és el treball pendent per convertir-la en una prova automatitzada.

## Prova visual Qualiteasy

Amb els contenidors ja en marxa, executa `python3 theme/install.py`. L'ordre copia una paleta SCSS al volum persistent de GLPI i neteja la memòria cau; **no reconstrueix ni recrea els contenidors**. A les preferències de l'usuari, selecciona la paleta «Qualiteasy». La paleta usa els colors del pilot i posa el logotip Qualiteasy a la barra lateral.

El fitxer font és `theme/qualiteasy.scss.in`; l'instal·lador hi incorpora el logotip oficial `theme/qualiteasy-logo.png` en una URL de dades i genera el SCSS que GLPI llegeix. No modifica el nucli. El logo a la barra és un ajust de CSS de prova, no el plugin oficial de Branding; no canvia el login ni el favicon. El tema tampoc tradueix «Tiquets» a «Incidències» ni converteix el quadre inicial en la safata visual del pilot Zammad.

## Estat de la decisió

GLPI permet compartimentació per entitats dins d'una instància, i l'aïllament bàsic es va observar a la UI i l'API. Encara falta provar un perfil Brigada amb restriccions de transició, l'experiència mòbil, les fotografies, el flux municipal complet i el cost d'operació per molts clients. La decisió GLPI/Zammad continua oberta.

La [branca demo-estatica](https://github.com/Qualiteasy-Internet-Solutions/qualiteasy-incidents/tree/demo-estatica) conté la demostració pública sense backend.
