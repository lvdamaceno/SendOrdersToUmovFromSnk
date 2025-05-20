import logging

from notifications.telegram import enviar_notificacao_telegram
from sankhya_api.utils import execute_query
from umov_api.sender import umov_post_itens_tarefa, umov_post_local_tarefa, umov_post_tarefa

def processa_envio_pedido_umov(nunota, client):
    logging.info(f"Processando pedido nro: {nunota}")
    produtos = umov_post_itens_tarefa(nunota, client)
    falha_local = umov_post_local_tarefa(nunota, client)

    if falha_local:
        logging.warning(f"⚠️ Falha ao enviar local para NUNOTA {nunota}. Tarefa não será criada.")
        return 0, [], falha_local

    sucesso, falha_tarefa = umov_post_tarefa(nunota, produtos, client)
    return sucesso, falha_tarefa, falha_local


def processa_envio_pedido_periodo_umov(*datas, client):
    sucesso = 0
    falha = []

    if len(datas) == 2:
        data_inicial, data_final = datas
        query = f"AND CAB.DTNEG BETWEEN '{data_inicial}' AND '{data_final}'"
        log_info = f"{data_inicial} e {data_final}"
    elif len(datas) == 1:
        data = datas[0]
        query = f"AND CAB.DTNEG = '{data}'"
        log_info = f"{data}"
    else:
        raise ValueError("Você deve fornecer uma ou duas datas.")

    sql = f"""
            SELECT DISTINCT CAB.NUNOTA \
            FROM TGFCAB CAB \
            INNER JOIN TGFITE ITE ON CAB.NUNOTA = ITE.NUNOTA
            WHERE CAB.CODTIPOPER IN (1264, 1815, 1247, 1280) \
                 {query}\
                AND ITE.AD_MONTAGEM = 'S' \
          """

    pedidos = execute_query(sql, client)
    logging.info(f"🔍 {len(pedidos)} pedidos encontrados em {log_info}")
    for pedido in pedidos:
        try:
            sucesso_tarefa, falha_tarefa, falha_local = processa_envio_pedido_umov(pedido[0], client)
            sucesso += sucesso_tarefa
            falha.extend(falha_tarefa)
            falha.extend(falha_local)
        except Exception as e:
            logging.error(f"❌ Erro ao processar pedido {pedido[0]}: {e}")
            falha.append(pedido[0])

    # Achatar a lista de falhas
    falha_flat = []
    for item in falha:
        if isinstance(item, list):
            falha_flat.extend(item)
        else:
            falha_flat.append(item)

    mensagem = (
        f"🔍 {len(pedidos)} pedidos encontrados em {log_info} para enviar ao UMOV\n"
        f"✅ Total de tarefas criadas com sucesso: {sucesso}\n"
        f"❌ Pedidos com falha: {', '.join(map(str, falha_flat)) if falha_flat else '0'}"
    )
    enviar_notificacao_telegram(mensagem)