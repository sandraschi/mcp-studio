#!/usr/bin/env python3
import requests

try:
    response = requests.get('http://localhost:7787/api/v1/clients/', timeout=5)
    data = response.json()
    clients = data.get('clients', [])
    total = data.get('total', 0)
    print(f'Total clients: {total}')
    print(f'Clients in response: {len(clients)}')

    zed_found = False
    antigravity_found = False

    for client in clients:
        client_id = client.get('id', 'unknown')
        name = client.get('name', 'unknown')
        platform = client.get('platform', 'unknown')
        print(f'- {client_id}: {name} ({platform})')

        if client_id == 'zed-editor':
            zed_found = True
        if client_id == 'antigravity':
            antigravity_found = True

    print(f'\nZed found: {zed_found}')
    print(f'Antigravity found: {antigravity_found}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
