"""Labelled, idempotent local workflow details for the existing Alella examples."""
from datetime import date, timedelta
import workflow_store as store

store.initialize()
if not store.meta(6):
    store.save_meta(6, {
        'demo_data': True,
        'origin_department': 'Serveis municipals (prova)',
        'target_department': 'Serveis municipals',
        'reporter_name': 'Ajuntament · usuari de prova',
        'reporter_position': 'Gestió municipal',
        'category': 'via_publica', 'priority': 'normal',
        'action_instruction': 'Comprovar l’accés i reposar el fitó practicable. Documentar el resultat amb fotografies.',
        'assignee_id': 4, 'assignee_name': 'Operari Prova', 'assignee_position': 'Operari de brigada',
        'brigade_lead': 'Cap de Brigada (prova)',
        'service_lead': 'Responsable del servei (prova)',
        'validator_id': 5, 'validator_name': 'Validador Prova',
        'due_date': (date.today() + timedelta(days=7)).isoformat(),
    })
    store.add_event(6, 'Escenari de prova', 'Ajuntament · usuari de prova',
                    'Assignació preconfigurada per ensenyar la feina de brigada. No és un esdeveniment històric.')
    store.add_notification(6, 'correu', 'Cap de Brigada (prova)', 'Activació a SSMM',
                           'Mostra de l’avís al cap de Brigada per la incidència #57006.')
    store.add_notification(6, 'WhatsApp', 'Responsable del servei (prova)', 'Activació a SSMM',
                           'Mostra de l’avís al responsable del servei per la incidència #57006.')
    store.add_notification(6, 'WhatsApp', 'Operari Prova', 'Assignació de la feina',
                           'Mostra de l’avís d’execució per la incidència #57006.')
if not store.meta(7):
    store.save_meta(7, {
        'demo_data': True,
        'origin_department': 'Serveis municipals (prova)',
        'target_department': 'Serveis municipals',
        'category': 'via_publica', 'priority': 'normal',
        'action_instruction': 'Revisar la porta del parc i substituir la frontissa trencada.',
        'assignee_id': 4, 'assignee_name': 'Operari Prova', 'assignee_position': 'Operari de brigada',
        'validator_id': 5, 'validator_name': 'Validador Prova',
        'work_done': 'Reparació simulada per la demostració. L’Ajuntament ha de comprovar el resultat.',
        'preclosed_by': 'Operari Prova', 'preclosed_position': 'Operari de brigada',
        'preclosed_at': store.now(),
    })
    store.add_event(7, 'Escenari de prova', 'Operari Prova',
                    'Pretancament simulat per ensenyar la validació municipal. No correspon al registre històric.')
print('Metadades de demostració preparades per a #57006 i #57007.')
