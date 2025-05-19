import logging

from umov_api.sender import umov_post_itens_tarefa, umov_get_from_snk_itens_tarefa, umov_post_local_tarefa, \
    umov_post_tarefa
from utils import configure_logging
from sankhya_api.auth import SankhyaClient

def processa_envio_umov(nunota, client):
    produtos = umov_post_itens_tarefa(nunota, client)
    umov_post_local_tarefa(nunota, client)
    umov_post_tarefa(nunota, client, produtos)

if __name__ == '__main__':
    configure_logging()
    client_sankhya = SankhyaClient()

    pedidos = [1376716]
    for pedido in pedidos:
        try:
            processa_envio_umov(pedido, client_sankhya)
        except Exception as e:
            logging.error(f"❌ Erro ao processar pedido {pedido}: {e}")

    # TODO
    # Criar o cron para enviar todo dia as montagens do dia anterior
    # Notificar via telegram