import json
import logging
import os
from datetime import datetime

import requests

from sankhya_api.fetch import snk_fetch_itens_tarefa, snk_fetch_local_tarefa, snk_fetch_tarefa

def umov_get_info_from_snk(tipo, nunota, client):
    fetch_map = {
        'itens_tarefa': (snk_fetch_itens_tarefa, "📦 Itens tarefa"),
        'local_tarefa': (snk_fetch_local_tarefa, "📍 Local tarefa"),
        'tarefa': (snk_fetch_tarefa, "🛠️ Tarefa"),
    }

    if tipo not in fetch_map:
        raise ValueError(f"Tipo inválido: {tipo}")

    fetch_func, log_msg = fetch_map[tipo]
    info = fetch_func(nunota, client)
    logging.debug(f"{log_msg}: {info}")
    return info


# ============================================================
# ITENS DA TAREFA                                            =
# ============================================================
def umov_post_itens_tarefa(nunota, client):
    url = "https://api.umov.me/v2/item"

    app_id = os.getenv("UMOV_APP_ID")
    app_key = os.getenv("UMOV_APP_KEY")

    itens = umov_get_info_from_snk('itens_tarefa', nunota, client)
    produtos = []

    headers = {
        "AppId": app_id,
        "AppKey": app_key,
        "Content-Type": "application/json"
    }

    for item in itens:
        produtos.append(item[0])
        body = {
            "alternativeIdentifier": item[0],
            "description": item[1],
            "active": item[2],
            "subgroup": item[3],
            "qtd_item": item[4],
            "num_pedido": item[5]
        }

        payload = {
            "active": body["active"],
            "alternativeIdentifier": body["alternativeIdentifier"],
            "description": body["description"],
            "showInCenterWeb": True,
            "subGroup": {
                "alternativeIdentifier": body["subgroup"]
            },
            "customFields": [
                {
                    "alternativeIdentifier": "qtd_item",
                    "value": str(body["qtd_item"])
                },
                {
                    "alternativeIdentifier": "num_pedido",
                    "value": str(body["num_pedido"])
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logging.info(f"✅ Item '{body['alternativeIdentifier']}' enviado com sucesso.")
        except requests.RequestException as e:
            logging.error(f"❌ Erro ao enviar item '{body['alternativeIdentifier']}': {e}")

    return produtos


# ============================================================
# LOCAL DA TAREFA                                            =
# ============================================================
def umov_post_local_tarefa(nunota, client):
    url = "https://api.umov.me/v2/local"
    app_id = os.getenv("UMOV_APP_ID")
    app_key = os.getenv("UMOV_APP_KEY")

    headers = {
        "AppId": app_id,
        "AppKey": app_key,
        "Content-Type": "application/json"
    }

    locais = umov_get_info_from_snk('local_tarefa', nunota, client)

    for local in locais:
        (
            alternativeIdentifier,
            description,
            corporateName,
            active,
            email,
            celular,
            country,
            state,
            city,
            neighborhood,
            endereco_completo,
            zipcode
        ) = local

        ddd = celular[0:2]
        numero = celular[2:]

        payload = {
            "alternativeIdentifier": alternativeIdentifier,
            "description": description,
            "corporateName": corporateName,
            "active": bool(active),
            "email": email,
            "contactDTO": {
                "cellphone": {
                    "ddd": ddd,
                    "ddi": "55",
                    "number": numero
                },
                "email": email,
                "phone": {
                    "number": numero
                }
            },
            "address": {
                "processGeocoordinate": True,
                "country": country,
                "state": state,
                "city": city,
                "neighborhood": neighborhood,
                "street": endereco_completo.split(",")[0],
                "streetNumber": endereco_completo.split(",")[1].strip() if "," in endereco_completo else "",
                "streetType": "Rua",
                "streetComplement": "",
                "zipcode": zipcode
            }
        }

        logging.debug(json.dumps(payload, indent=2, ensure_ascii=False))

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                try:
                    erro = response.json()
                    logging.error(
                        f"❌ Erro ao enviar local '{local[0]}':\n{json.dumps(erro, indent=2, ensure_ascii=False)}")
                except Exception:
                    logging.error(
                        f"❌ Erro ao enviar local '{local[0]}': código {response.status_code} - {response.text}")
            else:
                logging.info(f"✅ Local enviado com sucesso: {local[0]} - ID: {response.json().get('id')}")
        except Exception as e:
            logging.error(f"❌ Erro na requisição para local {local[0]}: {e}")


# ============================================================
# TAREFA                                                     =
# ============================================================
def umov_post_tarefa(nunota, client, itens):
    url = "https://api.umov.me/v2/newTask"
    app_id = os.getenv("UMOV_APP_ID")
    app_key = os.getenv("UMOV_APP_KEY")

    tarefas = umov_get_info_from_snk('tarefa', nunota, client)
    dict_produtos = [{"alternativeIdentifier": item} for item in itens]

    if not tarefas:
        logging.warning(f"⚠️ Nenhuma tarefa retornada para NUNOTA {nunota}")
        return None

    for tarefa in tarefas:
        (
            alternativeidentifier,  # "44556-65135"
            serviceLocal,  # "254335-1369067-44556"
            agent,  # "master"
            scheduleType,  # "Montagem Internos"
            date_str,  # "20/05/2025"
            activitiesOrigin,  # 7
            hora,  # null
            observation,  # texto
            N_pedido,  # 1369067
            tipo_servico  # "montagem"
        ) = tarefa

        try:
            # Conversão da data
            date_iso = datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError as e:
            logging.error(f"❌ Data inválida '{date_str}' para NUNOTA {nunota}: {e}")
            continue

        body = {
            "active": True,
            "activityOrigin": [str(activitiesOrigin)],
            "alternativeIdentifier": alternativeidentifier,
            "taskType": {
                "alternativeIdentifier": scheduleType
            },
            "agent": {
                "alternativeIdentifier": agent
            },
            "serviceLocal": {
                "alternativeIdentifier": serviceLocal
            },
            "customFields": [
                {
                    "alternativeIdentifier": "N_pedido",
                    "value": N_pedido
                },
                {
                    "alternativeIdentifier": "tipo_servico",
                    "value": tipo_servico
                }
            ],
            "initialDate": date_iso,
            "initialHour": hora or "00:00",
            "situationId": 30,
            "observation": observation,
            "taskItems": dict_produtos
        }

        headers = {
            "AppId": app_id,
            "AppKey": app_key,
            "Content-Type": "application/json"
        }

        logging.debug(
            f"📦 Payload montado para envio da tarefa NUNOTA {nunota}:\n{json.dumps(body, indent=2, ensure_ascii=False)}")

        try:
            response = requests.post(url, headers=headers, json=body)
            if response.status_code == 200:
                logging.info(f"✅ Tarefa criada com sucesso para NUNOTA {nunota} - ID: {response.json().get('id')}")
                return None
            else:
                logging.error(
                    f"❌ Erro ao criar tarefa para NUNOTA {nunota}: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
                return None
        except Exception as e:
            logging.error(f"❌ Erro de conexão ao criar tarefa para NUNOTA {nunota}: {e}")
            return None
    return None
