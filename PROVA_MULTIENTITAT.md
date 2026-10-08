# Resultats de la prova GLPI multientitat

## Configuració provada localment

- Una instal·lació GLPI 11.0.9 amb MariaDB 11.8.
- Dues entitats filles de l'arrel: `Alella · prova` i `Client B · prova`.
- Usuaris ficticis d'operari i gestor municipal vinculats a l'entitat corresponent. Es va retirar el permís recursiu de Self-Service a l'entitat arrel que apareixia en crear usuaris per CLI.
- Dos tiquets ficticis independents, un per entitat. Cap registre ni fotografia real d'Alella no es va importar.

## Observacions verificades

| Escenari | Resultat local |
|---|---|
| Operari d'Alella consulta `getMyEntities` i `/Ticket/` | Només veu l'entitat i el tiquet d'Alella. |
| Operari del Client B consulta els mateixos recursos | Només veu l'entitat i el tiquet del Client B. |
| Accés directe d'un usuari al tiquet de l'altra entitat | HTTP 403. |
| Operari registra una solució | El tiquet passa a resolt i la solució queda pendent d'aprovació. |
| Ajuntament accepta la solució per `/Ticket/{id}` amb `_accepted=1` | El tiquet passa a tancat i queda registrada la persona que valida. |
| Operari amb perfil Technician estàndard envia directament `status=6` | **Ha pogut tancar el tiquet**. Cal un perfil Brigada amb matriu de cicle de vida restringida i repetir la prova. |

Actualitzar només l'estat de la solució no tanca correctament el tiquet ni registra l'aprovador. La integració ha de seguir el flux del tiquet.

## Encaix i límits

Les entitats i els perfils permeten una sola instal·lació per diversos clients amb visibilitat separada en les operacions provades. Comparteixen base de dades, fitxers, administració, actualitzacions i domini de fallada: això no és aïllament físic per client. Cal provar adjunts, cerca, informes, notificacions, API addicionals i permisos d'administrador.

GLPI requereix MySQL/MariaDB per al seu nucli; Qualiteasy pot mantenir el backend de qualitat a PostgreSQL i integrar-se per API, però això introdueix dos magatzems de dades. El flux d'Alella requereix una alta mòbil de tres camps, assignació municipal, pretancament de brigada i validació final; el formulari i els permisos s'han d'ajustar abans de considerar GLPI un substitut viable.

L'SSO oficial OAuth/Keycloak i alguns canals poden dependre d'una subscripció o plugin concrets; cal confirmar l'edició i el cost abans de decidir.

Referències: [entitats GLPI](https://help.glpi-project.org/documentation/modules/administration/entities), [cicle dels tiquets](https://help.glpi-project.org/documentation/modules/assistance/tickets/ticketlifecycle), [matriu de cicle de vida](https://help.glpi-project.org/documentation/modules/administration/profiles/lifecyclematrix).
