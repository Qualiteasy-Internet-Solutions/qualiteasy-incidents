# Qualiteasy · demo estàtica d'incidències per a Alella

Prototip interactiu per revisar amb l'Ajuntament el recorregut d'una incidència: avís simple de brigada o alta municipal, revisió, assignació, execució, pretancament amb fotografia, validació o retorn, ordre de treball imprimible i possible derivació excepcional a una no conformitat.

## Abast de la demostració

- Els sis perfils són simulats. Els botons mostren què podria fer cada persona, però **no són control d'accés real**.
- Les incidències i fotografies inicials són **fictícies i sintètiques**. Els carrers i punts del mapa són orientatius.
- Els canvis i fotos afegits viuen **només en memòria de la pestanya**. Recarregar la pàgina restableix la mostra.
- No hi ha backend, autenticació, base de dades, integració amb Zammad o Qualiteasy, ni enviament de correus o WhatsApp. Els avisos es previsualitzen.
- El mapa carrega tessel·les d'OpenStreetMap quan hi ha connexió. El GPS del formulari requereix permís del navegador i un origen segur (HTTPS o localhost).

## Execució local

```sh
python3 -m http.server 8093
```

Obre `http://localhost:8093/`. Per publicar amb GitHub Pages, selecciona la branca `demo-estatica` i la carpeta `/ (root)` a **Settings → Pages**. Tots els recursos usen rutes relatives.

## Relació amb el prototip operatiu

Aquesta demo reutilitza el disseny del prototip local d'Alella i substitueix la seva API per un model temporal al navegador. És un artefacte de revisió visual i de flux, no una implementació de producció.
