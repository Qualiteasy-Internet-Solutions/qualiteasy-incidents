# Resultats de la prova GLPI multientitat

## Configuració provada localment

- Una instal·lació GLPI 11.0.9 amb MariaDB 11.8.
- Dues entitats filles de l'arrel: `Alella · prova` i `Client B · prova`.
- Usuaris ficticis d'operari i gestor municipal vinculats a l'entitat corresponent. Es va retirar el permís recursiu de Self-Service a l'entitat arrel que apareixia en crear usuaris per CLI.
- Dos tiquets ficticis inicials independents, un per entitat, i més tard tres casos ficticis oberts en fases diferents a l’entitat del pilot municipal. Cap registre ni fotografia real de client no es va importar.

## Observacions verificades

| Escenari | Resultat local |
|---|---|
| Operari d'Alella consulta `getMyEntities` i `/Ticket/` | Només veu l'entitat i el tiquet d'Alella. |
| Operari del Client B consulta els mateixos recursos | Només veu l'entitat i el tiquet del Client B. |
| Accés directe d'un usuari al tiquet de l'altra entitat | HTTP 403. |
| Operari registra una solució | El tiquet passa a resolt i la solució queda pendent d'aprovació. |
| Ajuntament accepta la solució per `/Ticket/{id}` amb `_accepted=1` | El tiquet passa a tancat i queda registrada la persona que valida. |
| Operari amb perfil Technician estàndard envia directament `status=6` | **Ha pogut tancar el tiquet**. Cal un perfil Brigada amb matriu de cicle de vida restringida i repetir la prova. |

### Visibilitat de la safata local

Els dos primers casos del pilot municipal es van tancar durant les proves d’API i no destacaven al filtre habitual de feina oberta. El 8 d’octubre es van afegir tres casos estrictament ficticis: `#4` nou/pendent de revisió, `#5` en execució i `#6` resolt amb una solució pendent d’aprovació. L’API confirma que tant l’usuari municipal com l’operari de prova veuen els tres. A la UI cal seleccionar l’entitat del pilot i obrir **Assistència/Assistance → Tiquets/Tickets**.

El 8 d’octubre, es va assignar a l’usuari municipal fictici el perfil local `Qualiteasy Municipal · prova visual`, que conserva només drets d’incidències, seguiments, tasques i validació. La barra lateral va passar de sis seccions principals a **Suport** i **Eines** (només «Cerques desades»). L’operari continua amb `Technician`: la prova encara **no** separa les facultats reals de recepció, execució i tancament. La configuració dels perfils i casos roman al volum Docker local, no en aquesta branca Git.

### Comparació de l’aspecte

S’ha instal·lat la [paleta personalitzada nativa de GLPI 11](https://help.glpi-project.org/documentation/advanced/custom_palettes), amb colors Qualiteasy i el logotip oficial a la barra lateral mitjançant CSS. Això es pot repetir amb `python3 theme/install.py` i no exigeix reconstruir Docker. La prova al navegador confirma `data-glpi-theme="qualiteasy"` i el logotip visible. La pantalla continua essent la vista estàndard de GLPI: taules i pestanyes genèriques, «Tiquets», una capçalera i login de GLPI, sense el panell fotogràfic, mapa o accions per rol de la demo Zammad. Els perfils redueixen mòduls sobrants, però no creen aquesta experiència per si sols.

El [plugin oficial Branding](https://help.glpi-project.org/faq/plugins/branding) cobreix logo, favicon i login, però per a GLPI autohosted demana la subscripció Basic. El CSS de la paleta és una alternativa limitada per a la barra lateral i pot necessitar ajustos amb noves versions. El [quadre de comandament natiu](https://help.glpi-project.org/faq/glpi/dashboard) es pot personalitzar amb widgets; cal provar si n’hi ha prou per al circuit municipal abans de prometre equivalència visual.

Actualitzar només l'estat de la solució no tanca correctament el tiquet ni registra l'aprovador. La integració ha de seguir el flux del tiquet.

## Encaix i límits

Les entitats i els perfils permeten una sola instal·lació per diversos clients amb visibilitat separada en les operacions provades. Comparteixen base de dades, fitxers, administració, actualitzacions i domini de fallada: això no és aïllament físic per client. Cal provar adjunts, cerca, informes, notificacions, API addicionals i permisos d'administrador.

GLPI requereix MySQL/MariaDB per al seu nucli; Qualiteasy pot mantenir el backend de qualitat a PostgreSQL i integrar-se per API, però això introdueix dos magatzems de dades. El flux d'Alella requereix una alta mòbil de tres camps, assignació municipal, pretancament de brigada i validació final; el formulari i els permisos s'han d'ajustar abans de considerar GLPI un substitut viable.

L'SSO oficial OAuth/Keycloak i alguns canals poden dependre d'una subscripció o plugin concrets; cal confirmar l'edició i el cost abans de decidir.

Referències: [entitats GLPI](https://help.glpi-project.org/documentation/modules/administration/entities), [cicle dels tiquets](https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketlifecycle), [matriu de cicle de vida](https://help.glpi-project.org/documentation/modules/administration/profiles/lifecyclematrix).
