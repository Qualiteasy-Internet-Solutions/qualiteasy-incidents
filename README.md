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

## Fitxa municipal de demostració

Amb GLPI en marxa, executa `python3 plugin/install_fields.py` i `python3 plugin/install.py`. El primer instal·la la versió 1.24.5 del [plugin oficial Fields](https://github.com/pluginsGLPI/fields) amb verificació SHA-256; el segon instal·la l'extensió Qualiteasy. No reconstrueixen Docker ni modifiquen el nucli. A la instal·lació local que conté els tiquets ficticis `#4`, `#5` i `#6`, executa també `docker compose exec -T glpi php plugins/qincidents/cli/configure_fields.php` per crear els camps i catàlegs del pilot. `simplify_entities.php` canvia l'etiqueta arrel i les preferències dels comptes de prova; està pensat només per a aquella instal·lació fictícia.

Els enllaços habituals dels tres tiquets obren per defecte `http://127.0.0.1:8090/plugins/qincidents/front/fiche.php?id=4` (amb l'ID corresponent). **Editar al registre operatiu** obre el formulari natiu amb els camps de Fields, selectors de departament/àmbit/persona, dues dates, foto/PDF i botó per obtenir coordenades GPS. En desar, es torna a la fitxa Qualiteasy. La fitxa llegeix els camps desats, l'estat, la data, l'assignació i els annexos vinculats al tiquet; mostra mapa si hi ha coordenades i es pot imprimir. L'usuari d'un altre client no pot llegir el cas.

És una **prova amb tres IDs fixos**. `demo/cases.json` encara aporta valors inicials i fotografies sintètiques quan no hi ha annexos natius. S'ha comprovat que un camp addicional es desa i reapareix a la fitxa, i que una imatge PNG es vincula com a Document de GLPI; PDF consta com a tipus admès en la configuració. La llista de persones dels dos selectors propis es filtra visualment als comptes locals de la demostració i el hook comprova l'assignació directa a l'entitat en desar. Cal substituir aquesta regla per rols i membresies reals abans de producció. Continuen pendents els avisos, la foto de pretancament vinculada a fase, els permisos definitius de Brigada i la derivació a NC. El directori de plugins s'ha de reinstal·lar després de recrear el contenidor perquè no està muntat com a volum.

## Estat de la decisió

GLPI permet compartimentació per entitats dins d'una instància, i l'aïllament bàsic es va observar a la UI i l'API. Encara falta provar un perfil Brigada amb restriccions de transició, l'experiència mòbil, les fotografies, el flux municipal complet i el cost d'operació per molts clients. La decisió GLPI/Zammad continua oberta.

La [branca demo-estatica](https://github.com/Qualiteasy-Internet-Solutions/qualiteasy-incidents/tree/demo-estatica) conté la demostració pública sense backend.
