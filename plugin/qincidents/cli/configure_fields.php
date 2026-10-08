<?php

// Executar dins del contenidor GLPI amb el plugin oficial Fields ja activat.
require_once '/var/www/glpi/vendor/autoload.php';
(new \Glpi\Kernel\Kernel())->boot();

if (!Plugin::isPluginActive('fields')) {
    fwrite(STDERR, "Cal instal·lar i activar el plugin Fields.\n");
    exit(1);
}

$entityId = 1; // Entitat fictícia Alella · prova d'aquesta instal·lació local.
$containerName = 'dadesmunicipalsqualiteasy';
$container = new PluginFieldsContainer();
$found = $container->find(['name' => $containerName]);
$containerId = $found ? (int) array_key_first($found) : 0;
if (!$containerId) {
    $containerId = (int) $container->add([
        'name' => $containerName,
        'label' => 'Dades municipals Qualiteasy',
        'itemtypes' => ['Ticket'],
        'type' => 'dom',
        'entities_id' => $entityId,
        'is_recursive' => 0,
        'is_active' => 1,
    ]);
    if (!$containerId) {
        fwrite(STDERR, "No s'ha pogut crear el bloc municipal.\n");
        exit(1);
    }
}

$definitions = [
    ['qdepartamentorigen', 'Departament d’origen', 'text'],
    ['qcarrecautor', 'Càrrec de l’autor', 'text'],
    ['qdepartamentdesti', 'Departament destí', 'text'],
    ['qambitmunicipal', 'Àmbit municipal', 'text'],
    ['qcausa', 'Causa coneguda', 'textarea'],
    ['qaccioimmediata', 'Acció immediata / ordre de treball', 'textarea'],
    ['qdatalimit', 'Data límit de l’actuació', 'datetime'],
    ['qcarrecresponsable', 'Càrrec del responsable de l’actuació', 'text'],
    ['qubicacio', 'Carrer i punt concret', 'text'],
    ['qlatitud', 'Latitud', 'number'],
    ['qlongitud', 'Longitud', 'number'],
    ['qobservacioubicacio', 'Precisió de la ubicació', 'text'],
    ['qfeinaexecutada', 'Feina executada per la Brigada', 'textarea'],
    ['qdatafinalitzacio', 'Data de finalització real de la feina', 'datetime'],
    ['qverificador', 'Persona que fa el pretancament', 'text'],
    ['qcarrecverificador', 'Càrrec de qui fa el pretancament', 'text'],
    ['qtancador', 'Persona que valida el tancament', 'text'],
    ['qcarrectancador', 'Càrrec de qui valida el tancament', 'text'],
    ['qdepartamentorigenid', 'Departament d’origen · catàleg', 'dropdown-Group'],
    ['qdepartamentdestiid', 'Departament destí · catàleg', 'dropdown-Group'],
    ['qambitmunicipalid', 'Àmbit municipal · catàleg', 'dropdown'],
    ['qverificadorid', 'Persona que fa el pretancament · usuari', 'dropdown-User'],
    ['qtancadorid', 'Persona que valida el tancament · usuari', 'dropdown-User'],
];

$fields = new PluginFieldsField();
foreach ($definitions as [$name, $label, $type]) {
    if ($fields->find(['plugin_fields_containers_id' => $containerId, 'name' => $name])) {
        continue;
    }
    $id = $fields->add([
        'plugin_fields_containers_id' => $containerId,
        'name' => $name,
        'label' => $label,
        'type' => $type,
        'is_active' => 1,
        'is_readonly' => 0,
        'mandatory' => 0,
    ]);
    if (!$id) {
        fwrite(STDERR, "No s'ha pogut crear el camp {$name}.\n");
        exit(1);
    }
}

// Els cinc valors antics eren text lliure: es conserven a la BD per traça,
// però el formulari presenta els nous selectors en comptes de duplicar-los.
foreach (['qdepartamentorigen', 'qdepartamentdesti', 'qambitmunicipal', 'qverificador', 'qtancador'] as $oldName) {
    foreach ($fields->find(['plugin_fields_containers_id' => $containerId, 'name' => $oldName]) as $old) {
        if ((int) $old['is_active'] !== 0) {
            $fields->update(['id' => (int) $old['id'], 'is_active' => 0]);
        }
    }
}

$groupIds = [];
$groups = new Group();
foreach (['Brigada municipal', 'Administració municipal', 'Serveis municipals'] as $name) {
    $existing = $groups->find(['name' => $name, 'entities_id' => $entityId]);
    $groupIds[$name] = $existing ? (int) array_key_first($existing) : (int) $groups->add([
        'name' => $name,
        'entities_id' => $entityId,
        'is_recursive' => 0,
    ]);
}

$catalogClass = PluginFieldsDropdown::getClassname('qambitmunicipalid');
$catalog = new $catalogClass();
$categoryIds = [];
foreach (['Via pública · fonts', 'Via pública · mobiliari', 'Parcs i equipaments', 'Edificis', 'Actes'] as $name) {
    $existing = $catalog->find(['name' => $name, 'entities_id' => $entityId]);
    $categoryIds[$name] = $existing ? (int) array_key_first($existing) : (int) $catalog->add([
        'name' => $name,
        'entities_id' => $entityId,
        'is_recursive' => 0,
    ]);
}

$table = getTableForItemType(PluginFieldsContainer::getClassname('Ticket', $containerName));
$cases = json_decode(file_get_contents(__DIR__ . '/../demo/cases.json'), true, 512, JSON_THROW_ON_ERROR);
global $DB;
foreach ($cases as $ticketId => $case) {
    $exists = $DB->request([
        'FROM' => $table,
        'WHERE' => ['items_id' => (int) $ticketId, 'itemtype' => 'Ticket'],
    ]);
    if (count($exists)) {
        continue; // No esborrar modificacions fetes des del formulari.
    }
    $DB->insert($table, [
        'items_id' => (int) $ticketId,
        'itemtype' => 'Ticket',
        'plugin_fields_containers_id' => $containerId,
        'entities_id' => $entityId,
        'qdepartamentorigen' => $case['origin_department'],
        'qcarrecautor' => $case['reporter_position'],
        'qdepartamentdesti' => $case['target_department'],
        'qambitmunicipal' => $case['category'],
        'qcausa' => $case['cause'],
        'qaccioimmediata' => $case['action'],
        'qcarrecresponsable' => 'Brigada municipal',
        'qubicacio' => $case['location'],
        'qlatitud' => $case['lat'] === null ? null : (string) $case['lat'],
        'qlongitud' => $case['lon'] === null ? null : (string) $case['lon'],
        'qobservacioubicacio' => $case['location_note'],
        'qfeinaexecutada' => $case['work_done'],
        'qverificador' => $case['preclose_by'],
        'qcarrecverificador' => $case['preclose_position'],
        'qtancador' => $case['close_by'],
        'qcarrectancador' => $case['close_position'],
    ]);
}

// Mostres dels selectors: només s'omplen els valors encara buits.
foreach ($cases as $ticketId => $case) {
    $rows = $DB->request(['FROM' => $table, 'WHERE' => ['items_id' => (int) $ticketId, 'itemtype' => 'Ticket']]);
    foreach ($rows as $row) {
        $originGroup = str_contains($case['origin_department'], 'Brigada') ? 'Brigada municipal' : 'Administració municipal';
        $values = [
            'groups_id_qdepartamentorigenid' => $groupIds[$originGroup],
            'groups_id_qdepartamentdestiid' => $groupIds['Serveis municipals'],
            'plugin_fields_qambitmunicipaliddropdowns_id' => $categoryIds[$case['category']],
            'users_id_qverificadorid' => $ticketId == 6 ? 7 : 0,
            'users_id_qtancadorid' => $ticketId == 5 || $ticketId == 6 ? 9 : 0,
        ];
        foreach ($values as $column => $value) {
            if ((int) ($row[$column] ?? 0) === 0 && $value !== 0) {
                $DB->update($table, [$column => $value], ['id' => (int) $row['id']]);
            }
        }
        break;
    }
}

echo "Bloc municipal {$containerId}: selectors i camps configurats; tres casos inicials.\n";
