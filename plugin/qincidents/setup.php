<?php

use Glpi\Plugin\Hooks;

define('PLUGIN_QINCIDENTS_VERSION', '0.1.2');

function plugin_init_qincidents(): void
{
    global $PLUGIN_HOOKS;
    $PLUGIN_HOOKS['csrf_compliant']['qincidents'] = true;
    $PLUGIN_HOOKS[Hooks::POST_ITIL_INFO_SECTION]['qincidents'] = 'plugin_qincidents_ticket_link';
    $PLUGIN_HOOKS[Hooks::ADD_JAVASCRIPT]['qincidents'][] = 'public/default_fiche.js';
    $PLUGIN_HOOKS[Hooks::PRE_ITEM_UPDATE]['qincidents'][Ticket::class] = 'plugin_qincidents_restrict_demo_users';
    $PLUGIN_HOOKS[Hooks::PRE_ITEM_ADD]['qincidents'][Ticket::class] = 'plugin_qincidents_restrict_demo_users';
}

function plugin_version_qincidents(): array
{
    return [
        'name' => 'Fitxa Qualiteasy · prova',
        'version' => PLUGIN_QINCIDENTS_VERSION,
        'author' => 'Qualiteasy Internet Solutions',
        'license' => 'GPLv3+',
        'homepage' => 'https://github.com/Qualiteasy-Internet-Solutions/qualiteasy-incidents',
        'requirements' => ['glpi' => ['min' => '11.0.0', 'max' => '12.0.0']],
    ];
}

function plugin_qincidents_check_prerequisites(): bool
{
    return true;
}

function plugin_qincidents_check_config(bool $verbose = false): bool
{
    return true;
}
