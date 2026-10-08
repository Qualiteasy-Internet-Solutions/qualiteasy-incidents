<?php

function plugin_qincidents_install(): bool
{
    return true;
}

function plugin_qincidents_uninstall(): bool
{
    return true;
}

function plugin_qincidents_ticket_link(array $context): void
{
    $item = $context['item'] ?? null;
    if (!$item instanceof Ticket || !$item->getID()) {
        return;
    }

    $cases = json_decode(file_get_contents(__DIR__ . '/demo/cases.json'), true);
    if (!isset($cases[(string) $item->getID()])) {
        return;
    }

    $id = (int) $item->getID();
    echo '<section class="card mb-3"><div class="card-body">';
    echo '<strong>Fitxa municipal Qualiteasy</strong> · ';
    echo '<a class="btn btn-sm btn-primary ms-2" href="/plugins/qincidents/front/fiche.php?id=' . $id . '">';
    echo 'Veure fitxa completa, fotografies i mapa</a>';
    echo '</div></section>';
}

function plugin_qincidents_restrict_demo_users(Ticket $ticket): void
{
    // La prova municipal només accepta usuaris amb perfil assignat directament
    // a Alella. No afecta els altres clients ni els camps natius de GLPI.
    $entityId = (int) ($ticket->input['entities_id'] ?? $ticket->fields['entities_id'] ?? 0);
    if ($entityId !== 1) {
        return;
    }

    global $DB;
    foreach (['users_id_qverificadorid', 'users_id_qtancadorid'] as $field) {
        if (!array_key_exists($field, $ticket->input)) {
            continue;
        }
        $userId = (int) $ticket->input[$field];
        if ($userId === 0) {
            continue;
        }
        $valid = $DB->request([
            'FROM' => 'glpi_profiles_users',
            'WHERE' => ['users_id' => $userId, 'entities_id' => $entityId, 'is_recursive' => 0],
        ]);
        if (count($valid) === 0) {
            Session::addMessageAfterRedirect('El responsable ha de ser un usuari de l’entitat municipal.', false, ERROR);
            $ticket->input = false;
            return;
        }
    }
}
