import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


def enviar_email_brevo(subject, message, recipient):
    api_key = os.getenv('BREVO_API_KEY', '')
    from_email = os.getenv('BREVO_FROM_EMAIL', os.getenv('DEFAULT_FROM_EMAIL', 'josephsebastiannq@gmail.com'))
    from_name = os.getenv('BREVO_FROM_NAME', 'SACARF')

    print(f'[BREVO DEBUG] KEY={repr(api_key[:20])}... FROM={from_email} TO={recipient}')

    if not api_key:
        raise Exception('BREVO_API_KEY no configurada')

    payload = json.dumps({
        'sender': {'email': from_email, 'name': from_name},
        'to': [{'email': recipient}],
        'subject': subject,
        'textContent': message,
    }).encode()

    req = urllib.request.Request(
        'https://api.brevo.com/v3/smtp/email',
        data=payload,
        headers={
            'api-key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            body = resp.read().decode()
    except urllib.error.HTTPError as e:
        print(f'[BREVO ERROR] status={e.code} body={e.read().decode()}')
        raise Exception(f'Brevo error {e.code}: {e.read().decode()}')

    if status not in (200, 201, 202):
        raise Exception(f'Brevo error {status}: {body}')

    logger.info(f'Email enviado a {recipient} via Brevo (status {status})')
