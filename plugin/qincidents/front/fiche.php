<?php

require_once __DIR__ . '/../../../inc/includes.php';

Session::checkLoginUser();
$id = filter_input(INPUT_GET, 'id', FILTER_VALIDATE_INT);
if (!$id || $id < 1) {
    http_response_code(400);
    exit('Cal indicar una incidència.');
}

$ticket = new Ticket();
$ticket->check($id, READ); // Manté els permisos i l'aïllament d'entitat de GLPI.
$cases = json_decode(file_get_contents(__DIR__ . '/../demo/cases.json'), true);
$demo = is_array($cases) ? ($cases[(string) $id] ?? null) : null;
if ($demo === null) {
    http_response_code(404);
    exit('Aquesta incidència encara no té fitxa Qualiteasy de demostració.');
}

// Els camps configurats amb Fields són editables a GLPI i alimenten aquesta vista.
if (Plugin::isPluginActive('fields')) {
    global $DB;
    $table = getTableForItemType(PluginFieldsContainer::getClassname('Ticket', 'dadesmunicipalsqualiteasy'));
    if ($DB->tableExists($table)) {
        $rows = $DB->request(['FROM' => $table, 'WHERE' => ['items_id' => $id, 'itemtype' => 'Ticket']]);
        foreach ($rows as $row) {
            foreach ([
                'qdepartamentorigen' => 'origin_department',
                'qcarrecautor' => 'reporter_position',
                'qdepartamentdesti' => 'target_department',
                'qambitmunicipal' => 'category',
                'qcausa' => 'cause',
                'qaccioimmediata' => 'action',
                'qdatalimit' => 'due_date',
                'qubicacio' => 'location',
                'qobservacioubicacio' => 'location_note',
                'qfeinaexecutada' => 'work_done',
                'qdatafinalitzacio' => 'work_finished_at',
                'qverificador' => 'preclose_by',
                'qcarrecverificador' => 'preclose_position',
                'qtancador' => 'close_by',
                'qcarrectancador' => 'close_position',
            ] as $column => $key) {
                if (isset($row[$column])) {
                    $demo[$key] = (string) $row[$column];
                }
            }
            $demo['lat'] = is_numeric($row['qlatitud'] ?? null) ? (float) $row['qlatitud'] : null;
            $demo['lon'] = is_numeric($row['qlongitud'] ?? null) ? (float) $row['qlongitud'] : null;
            $catalogTable = getTableForItemType(PluginFieldsDropdown::getClassname('qambitmunicipalid'));
            foreach ([
                ['groups_id_qdepartamentorigenid', 'glpi_groups', 'origin_department'],
                ['groups_id_qdepartamentdestiid', 'glpi_groups', 'target_department'],
                ['plugin_fields_qambitmunicipaliddropdowns_id', $catalogTable, 'category'],
                ['users_id_qverificadorid', 'glpi_users', 'preclose_by'],
                ['users_id_qtancadorid', 'glpi_users', 'close_by'],
            ] as [$column, $lookupTable, $key]) {
                $selectedId = (int) ($row[$column] ?? 0);
                if ($selectedId > 0) {
                    $selection = $DB->request(['SELECT' => ['name'], 'FROM' => $lookupTable, 'WHERE' => ['id' => $selectedId]]);
                    foreach ($selection as $selected) {
                        $demo[$key] = (string) $selected['name'];
                        break;
                    }
                }
            }
            break;
        }
    }
}

function qe_h(?string $value): string
{
    return htmlspecialchars($value ?? '', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function qe_field(string $label, ?string $value): void
{
    $shown = trim((string) $value) !== '' ? $value : 'Pendent d’informar';
    echo '<div class="qe-field"><small>' . qe_h($label) . '</small><strong>' . qe_h($shown) . '</strong></div>';
}

$status = [1 => 'Pendent de revisió', 2 => 'En execució', 3 => 'En execució', 4 => 'En espera', 5 => 'Pendent de validació', 6 => 'Tancada'];
$stage = $status[(int) $ticket->fields['status']] ?? 'En seguiment';
$title = trim(preg_replace('/^\[[^]]+\]\s*/u', '', (string) $ticket->fields['name']));
$assignees = [];
global $DB;
foreach ($DB->request(['SELECT' => ['users_id'], 'FROM' => 'glpi_tickets_users', 'WHERE' => ['tickets_id' => $id, 'type' => 2]]) as $assignment) {
    $user = new User();
    if ($user->getFromDB((int) $assignment['users_id'])) {
        $assignees[] = (string) $user->fields['name'];
    }
}
$assignee = implode(', ', $assignees) ?: 'Pendent d’assignació';
$nativeDocuments = [];
foreach ($DB->request(['FROM' => 'glpi_documents_items', 'WHERE' => ['itemtype' => 'Ticket', 'items_id' => $id]]) as $link) {
    $document = new Document();
    if ($document->getFromDB((int) $link['documents_id']) && !(int) $document->fields['is_deleted']) {
        $nativeDocuments[] = [
            'id' => (int) $document->getID(),
            'name' => (string) $document->fields['filename'],
            'mime' => (string) $document->fields['mime'],
        ];
    }
}
$coords = isset($demo['lat'], $demo['lon'])
    && $demo['lat'] >= -90 && $demo['lat'] <= 90
    && $demo['lon'] >= -180 && $demo['lon'] <= 180
    ? [(float) $demo['lat'], (float) $demo['lon']] : null;

Html::header('Fitxa municipal · Qualiteasy', $_SERVER['PHP_SELF']);
echo '<link rel="stylesheet" href="/plugins/qincidents/public/fiche.css">';
echo '<script src="/plugins/qincidents/public/fiche.js" defer></script>';
echo '<main class="qe-sheet">';
echo '<header class="qe-head"><div><span class="qe-overline">QUALITEASY · INCIDÈNCIA #' . $id . '</span>';
echo '<h1>' . qe_h($title) . '</h1><p>Fitxa municipal i seguiment de la incidència</p></div>';
echo '<span class="qe-status">' . qe_h($stage) . '</span></header>';
echo '<div class="qe-alert">Demostració amb dades i fotografies sintètiques. Els annexos originals d’Alella no formen part d’aquesta prova.</div>';

echo '<section class="qe-card"><h2>Dades generals</h2><div class="qe-grid">';
qe_field('Departament d’origen', $demo['origin_department']);
qe_field('Data de registre', (string) $ticket->fields['date']);
qe_field('Autor / càrrec', $demo['reporter'] . ' · ' . $demo['reporter_position']);
qe_field('Origen · canal', $demo['origin']);
qe_field('Departament destí', $demo['target_department']);
qe_field('Àmbit · antic «Proveïdor»', $demo['category']);
qe_field('Problema', $title);
qe_field('Causa coneguda', $demo['cause']);
echo '</div></section>';

echo '<div class="qe-columns"><section class="qe-card"><h2>Fotografies i annexos</h2><div class="qe-gallery">';
if ($nativeDocuments) {
    foreach ($nativeDocuments as $document) {
        $url = '/front/document.send.php?docid=' . $document['id'] . '&tickets_id=' . $id;
        if (str_starts_with($document['mime'], 'image/')) {
            echo '<figure><button type="button" class="qe-zoom" data-photo="' . qe_h($url) . '" aria-label="Ampliar fotografia">';
            echo '<img src="' . qe_h($url) . '" alt="Fotografia adjunta al registre operatiu"></button>';
            echo '<figcaption><b>Annex de la incidència</b> · ' . qe_h($document['name']) . '</figcaption></figure>';
        } else {
            echo '<p><a class="qe-maplink" href="' . qe_h($url) . '" target="_blank" rel="noopener noreferrer">Descarregar ' . qe_h($document['name']) . '</a></p>';
        }
    }
} else {
    foreach ($demo['photos'] as $photo) {
        $filename = basename((string) $photo['file']);
        $url = '/plugins/qincidents/public/media/' . rawurlencode($filename);
        echo '<figure><button type="button" class="qe-zoom" data-photo="' . qe_h($url) . '" aria-label="Ampliar fotografia">';
        echo '<img src="' . qe_h($url) . '" alt="Imatge de demostració de la incidència"></button>';
        echo '<figcaption><b>' . qe_h($photo['phase']) . '</b> · ' . qe_h($photo['caption']) . '</figcaption></figure>';
    }
}
echo '</div><p class="qe-hint">Les imatges de mostra són sintètiques. Els nous fitxers es desen com a annexos del tiquet a GLPI.</p></section>';
echo '<section class="qe-card"><h2>Ubicació</h2><strong>' . qe_h($demo['location']) . '</strong>';
if ($coords) {
    echo '<div id="qe-map" data-lat="' . qe_h((string) $coords[0]) . '" data-lon="' . qe_h((string) $coords[1]) . '" role="img" aria-label="Mapa aproximat de la incidència"></div>';
    echo '<a class="qe-maplink" href="https://www.openstreetmap.org/?mlat=' . qe_h((string) $coords[0]) . '&amp;mlon=' . qe_h((string) $coords[1]) . '#map=17/' . qe_h((string) $coords[0]) . '/' . qe_h((string) $coords[1]) . '" target="_blank" rel="noopener noreferrer">Obrir al mapa ↗</a>';
} else {
    echo '<div class="qe-map-empty">Coordenades pendents de confirmar. L’adreça textual ja consta a la fitxa.</div>';
}
echo '<p class="qe-hint">' . qe_h($demo['location_note']) . '</p></section></div>';

echo '<section class="qe-card"><h2>Assignació i ordre de treball</h2><div class="qe-grid">';
qe_field('Acció immediata / feina encomanada', $demo['action']);
qe_field('Responsable de l’execució / càrrec', $assignee . ' · Brigada municipal');
qe_field('Data límit', $demo['due_date']);
qe_field('Prioritat', $demo['priority']);
echo '</div><p class="qe-hint">L’assignació efectiva es gestiona al registre operatiu. Els avisos per correu o WhatsApp encara no s’envien en aquest pilot.</p></section>';

echo '<section class="qe-card"><h2>Pretancament i validació</h2><div class="qe-grid">';
qe_field('Responsable de verificació / càrrec', $demo['preclose_by'] . ($demo['preclose_position'] ? ' · ' . $demo['preclose_position'] : ''));
qe_field('Feina executada', $demo['work_done']);
qe_field('Data de finalització real de la feina', $demo['work_finished_at'] ?? '');
qe_field('Responsable de tancament / càrrec', $demo['close_by'] . ($demo['close_position'] ? ' · ' . $demo['close_position'] : ''));
qe_field('Evidència fotogràfica del pretancament', 'Pendent d’adjuntar en aquesta prova');
echo '</div><p class="qe-hint">La solució pot quedar pendent d’acceptació municipal. Encara s’ha de validar que el perfil de Brigada no pugui tancar directament.</p></section>';

echo '<section class="qe-card"><h2>Qualitat i seguiment</h2><div class="qe-grid">';
qe_field('No conformitat formal', 'Sense NC vinculada');
qe_field('Auditories i accions', 'Pendent d’integració amb Qualiteasy');
echo '</div><p class="qe-hint">La derivació a NC és excepcional i requerirà una acció autoritzada al backend de Qualiteasy. Aquesta fitxa no crea una NC.</p></section>';

echo '<div class="qe-actions"><a class="qe-primary" href="/front/ticket.form.php?id=' . $id . '&amp;qe_native=1">Editar al registre operatiu</a>';
echo '<button type="button" id="qe-print" class="qe-secondary">Veure / imprimir ordre de treball</button>';
echo '<span>Per assignar, adjuntar evidències o aprovar la solució, utilitza el registre operatiu.</span></div>';
echo '</main><dialog id="qe-photo-dialog"><button type="button" id="qe-photo-close">Tanca ✕</button><img alt="Fotografia ampliada"><p>IMATGE SINTÈTICA · DEMOSTRACIÓ</p></dialog>';
Html::footer();
