import logging

from sankhya_api.utils import execute_query
from umov_api.sender import umov_post_itens_tarefa, umov_post_local_tarefa, umov_post_tarefa
from utils import configure_logging
from sankhya_api.auth import SankhyaClient

def processa_envio_pedido_umov(nunota, client):
    logging.info(f"Processando pedido nro: {nunota}")
    produtos = umov_post_itens_tarefa(nunota, client)
    umov_post_local_tarefa(nunota, client)
    umov_post_tarefa(nunota, client, produtos)

def processa_envio_pedido_periodo_umov(data_inicial, data_final, client):
    sql = f"""
            SELECT CAB.NUNOTA \
            FROM TGFCAB CAB \
            INNER JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
            WHERE CAB.CODTIPOPER IN (1264, 1247, 1280) \
                AND CAB.DTNEG BETWEEN '{data_inicial}' AND '{data_final}' \
                AND ITE.AD_MONTAGEM = 'S' \
          """

    pedidos = execute_query(sql, client)
    logging.info(f"🔍 {len(pedidos)} pedidos encontrados entre {data_inicial} e {data_final}")
    for pedido in pedidos:
        try:
            processa_envio_pedido_umov(pedido[0], client)
        except Exception as e:
            logging.error(f"❌ Erro ao processar pedido {pedido[0]}: {e}")

if __name__ == '__main__':
    configure_logging()
    client_sankhya = SankhyaClient()

    processa_envio_pedido_umov(1377556, client_sankhya)

