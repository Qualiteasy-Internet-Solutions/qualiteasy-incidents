<?php

// Ajust cosmètic de la instal·lació local de demostració. Conserva els IDs
// i la jerarquia d'entitats que proporcionen l'aïllament entre clients.
require_once '/var/www/glpi/vendor/autoload.php';
(new \Glpi\Kernel\Kernel())->boot();

global $DB;
$root = $DB->request(['FROM' => 'glpi_entities', 'WHERE' => ['id' => 0]])->current();
if ($root && $root['name'] !== 'Qualiteasy') {
    $DB->update('glpi_entities', ['name' => 'Qualiteasy', 'completename' => 'Qualiteasy'], ['id' => 0]);
}
foreach ([1, 2] as $entityId) {
    $row = $DB->request(['FROM' => 'glpi_entities', 'WHERE' => ['id' => $entityId]])->current();
    if ($row && (int) $row['entities_id'] === 0) {
        $DB->update('glpi_entities', ['completename' => 'Qualiteasy > ' . $row['name']], ['id' => $entityId]);
    }
}

foreach (['alella_municipal_demo', 'alella_operari_demo', 'clientb_operari_demo'] as $account) {
    $row = $DB->request(['FROM' => 'glpi_users', 'WHERE' => ['name' => $account]])->current();
    if ($row) {
        $DB->update('glpi_users', [
            'use_flat_dropdowntree' => 0,
            'use_flat_dropdowntree_on_search_result' => 0,
        ], ['id' => (int) $row['id']]);
    }
}

echo "Arrel etiquetada Qualiteasy i desplegables curts als usuaris de prova.\n";
