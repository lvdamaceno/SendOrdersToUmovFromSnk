import json
import logging
import os
from datetime import datetime

import requests


from sankhya_api.fetch import snk_fetch_itens_tarefa, snk_fetch_local_tarefa, snk_fetch_tarefa

# ============================
# Utils
# ============================
UMOV_BASE_URL = "https://api.umov.me/v2"

def build_headers():
    return {
        "AppId": os.getenv("UMOV_APP_ID"),
        "AppKey": os.getenv("UMOV_APP_KEY"),
        "Content-Type": "application/json"
    }

def log_request_error(contexto, response):
    try:
        erro = response.json()
        logging.error(f"❌ Erro ao enviar {contexto}:\n{json.dumps(erro, indent=2, ensure_ascii=False)}")
    except Exception:
        logging.error(f"❌ Erro ao enviar {contexto}: código {response.status_code} - {response.text}")

# ============================
# Fetch info
# ============================
def umov_get_info_from_snk(tipo, nunota, client):
    fetch_map = {
        'itens_tarefa': (snk_fetch_itens_tarefa, "📦 Itens tarefa"),
        'local_tarefa': (snk_fetch_local_tarefa, "📍 Local tarefa"),
        'tarefa': (snk_fetch_tarefa, "🛠️ Tarefa"),
    }

    if tipo not in fetch_map:
        raise ValueError(f"Tipo inválido: {tipo}")

    fetch_func, log_msg = fetch_map[tipo]

    try:
        info = fetch_func(nunota, client)
        logging.debug(f"{log_msg}: {info}")
        return info
    except Exception as e:
        logging.error(f"❌ Erro ao buscar dados de '{tipo}' para NUNOTA {nunota}: {e}")
        return None


# ============================
# Itens da tarefa
# ============================
def montar_payload_item(item):
    alt_id, desc, ativo, subgrupo, qtd, pedido = item
    return {
        "active": ativo,
        "alternativeIdentifier": alt_id,
        "description": desc,
        "showInCenterWeb": True,
        "subGroup": {"alternativeIdentifier": subgrupo},
        "customFields": [
            {"alternativeIdentifier": "qtd_item", "value": str(qtd)},
            {"alternativeIdentifier": "num_pedido", "value": str(pedido)}
        ]
    }

def umov_post_itens_tarefa(nunota, client):
    logging.debug(f"🚀 Iniciando post itens tarefa: {nunota}")
    url = f"{UMOV_BASE_URL}/item"
    headers = build_headers()
    itens = umov_get_info_from_snk('itens_tarefa', nunota, client)
    produtos = []

    for item in itens:
        produtos.append(item[0])
        payload = montar_payload_item(item)

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logging.info(f"✅ Item '{payload['alternativeIdentifier']}' enviado com sucesso.")
        except requests.RequestException as e:
            logging.error(f"❌ Erro ao enviar item '{payload['alternativeIdentifier']}': {e}")

    return produtos

# ============================
# Local da tarefa
# ============================
def umov_post_local_tarefa(nunota, client):
    logging.debug(f"🚀 Iniciando post local tarefa: {nunota}")
    url = f"{UMOV_BASE_URL}/local"
    headers = build_headers()
    locais = umov_get_info_from_snk('local_tarefa', nunota, client)
    falha = []

    for local in locais:
        (
            alternativeIdentifier, description, corporateName, active, email, celular,
            country, state, city, neighborhood, endereco_completo, zipcode
        ) = local

        if not celular or len(celular) < 3:
            logging.warning(f"⚠️ Celular inválido para local: {alternativeIdentifier}")
            falha.append(nunota)
            continue

        ddd, numero = celular[0:2], celular[2:]
        endereco_split = endereco_completo.split(",")
        rua = endereco_split[0]
        numero_rua = endereco_split[1].strip() if len(endereco_split) > 1 else ""

        payload = {
            "alternativeIdentifier": alternativeIdentifier,
            "description": description,
            "corporateName": corporateName,
            "active": bool(active),
            "email": email,
            "contactDTO": {
                "cellphone": {"ddd": ddd, "ddi": "55", "number": numero},
                "email": email,
                "phone": {"number": numero}
            },
            "address": {
                "processGeocoordinate": True,
                "country": country,
                "state": state,
                "city": city,
                "neighborhood": neighborhood,
                "street": rua,
                "streetNumber": numero_rua,
                "streetType": "Rua",
                "streetComplement": "",
                "zipcode": zipcode
            }
        }

        logging.debug(json.dumps(payload, indent=2, ensure_ascii=False))

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                logging.info(f"✅ Local enviado com sucesso: {alternativeIdentifier} - ID: {response.json().get('id')}")
            else:
                log_request_error(f"local '{alternativeIdentifier}'", response)
                falha.append(nunota)
        except Exception as e:
            logging.error(f"❌ Erro na requisição para local {alternativeIdentifier}: {e}")
            falha.append(nunota)

    return falha



# ============================
# Tarefa
# ============================
def umov_post_tarefa(nunota, itens, client):
    logging.debug(f"🚀 Iniciando post tarefa: {nunota}")
    url = f"{UMOV_BASE_URL}/newTask"
    headers = build_headers()
    tarefas = umov_get_info_from_snk('tarefa', nunota, client)
    dict_produtos = [{"alternativeIdentifier": item} for item in itens]
    sucesso = 0
    falha = []

    if not tarefas:
        logging.warning(f"⚠️ Nenhuma tarefa retornada para NUNOTA {nunota}")
        falha.append(nunota)
        return 0, falha

    for tarefa in tarefas:
        (
            alternativeidentifier, serviceLocal, agent, scheduleType,
            date_str, activitiesOrigin, hora, observation,
            N_pedido, tipo_servico
        ) = tarefa

        try:
            date_iso = datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError as e:
            logging.error(f"❌ Data inválida '{date_str}' para NUNOTA {nunota}: {e}")
            falha.append(nunota)
            continue

        body = {
            "active": True,
            "activityOrigin": [str(activitiesOrigin)],
            "alternativeIdentifier": alternativeidentifier,
            "taskType": {"alternativeIdentifier": scheduleType},
            "agent": {"alternativeIdentifier": agent},
            "serviceLocal": {"alternativeIdentifier": serviceLocal},
            "customFields": [
                {"alternativeIdentifier": "N_pedido", "value": N_pedido},
                {"alternativeIdentifier": "tipo_servico", "value": tipo_servico}
            ],
            "initialDate": date_iso,
            "initialHour": hora or "00:00",
            "situationId": 30,
            "observation": observation,
            "taskItems": dict_produtos
        }

        logging.debug(
            f"📦 Payload montado para envio da tarefa NUNOTA {nunota}:\n{json.dumps(body, indent=2, ensure_ascii=False)}")

        try:
            response = requests.post(url, headers=headers, json=body)
            if response.status_code == 200:
                logging.info(f"✅ Tarefa criada com sucesso para NUNOTA {nunota} - ID: {response.json().get('id')}")
                sucesso += 1
            else:
                log_request_error(f"tarefa para NUNOTA {nunota}", response)
                falha.append(nunota)
        except Exception as e:
            logging.error(f"❌ Erro de conexão ao criar tarefa para NUNOTA {nunota}: {e}")
            falha.append(nunota)

    return sucesso, falha

