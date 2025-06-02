from umov_api.processadores import processa_envio_pedido_umov
from utils import configure_logging
from sankhya_api.auth import SankhyaClient

if __name__ == '__main__':
    configure_logging()
    client_sankhya = SankhyaClient()

    try:
        nunota_input = input("🔢 Informe o número da nota (NUNOTA) a ser enviada: ")
        nunota = int(nunota_input)
    except ValueError:
        print("❌ Valor inválido. Por favor, digite um número inteiro para a nota.")
        exit(1)

    processa_envio_pedido_umov(nunota, client=client_sankhya)
