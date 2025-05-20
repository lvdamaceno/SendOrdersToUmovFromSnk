from umov_api.processadores import processa_envio_pedido_periodo_umov
from utils import configure_logging
from sankhya_api.auth import SankhyaClient
from datetime import datetime, timedelta


if __name__ == '__main__':
    configure_logging()
    client_sankhya = SankhyaClient()
    ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    processa_envio_pedido_periodo_umov(ontem,client=client_sankhya)