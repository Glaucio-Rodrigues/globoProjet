"""
agent/monitor.py — Watchdog do Agente de Coleta.

Monitora a pasta `arquivos_teste` (ou o storage real do Avid Media Composer)
e envia cada evento do sistema de arquivos para o backend via HTTP POST /events.

Convenção de nome de pasta monitorada:

    <PROJETO> <CODIGO> <ILHA>
    ex: "ANIVERSARIO RECIFE LUC I9"
        projeto = "ANIVERSARIO RECIFE"
        codigo  = "LUC"   -> resolvido via usuario_map.USUARIO_MAP
        ilha    = "I9"    -> "ILHA-09"

Conclusão do projeto: quando existe pelo menos um arquivo dentro da
subpasta `timeline/` do projeto (padrão real de export do Avid).
"""

import time
import os
import requests

from watchdog.observers.polling import PollingObserver as Observer  # inotify nao funciona de forma confiavel em /mnt/c (WSL)
from watchdog.events import FileSystemEventHandler

from usuario_map import resolver_usuario

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000/events")

PASTA_MONITORADA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "arquivos_teste"
)


def extrair_info_pasta(caminho_arquivo: str) -> dict:
    """
    Estrutura esperada:

    ANIVERSARIO RECIFE LUC I9
    ├── arquivo.mp4
    └── timeline/
        └── render.avb

    projeto = ANIVERSARIO RECIFE
    codigo  = LUC
    ilha    = I9 -> ILHA-09
    """

    abs_monitorada = os.path.abspath(PASTA_MONITORADA)
    abs_arquivo = os.path.abspath(caminho_arquivo)

    try:
        rel = os.path.relpath(abs_arquivo, abs_monitorada)
        partes = rel.split(os.sep)

    except ValueError:
        return {}

    if len(partes) < 2:
        return {
            "ilha": "",
            "usuario": "",
            "projeto": "",
            "pasta": "",
            "concluido": False,
        }

    pasta_nome = partes[0]

    tokens = pasta_nome.split()

    if len(tokens) < 3:
        return {
            "ilha": "",
            "usuario": "",
            "projeto": "",
            "pasta": pasta_nome,
            "concluido": False,
        }

    codigo = tokens[-2].upper()
    ilha_raw = tokens[-1].upper()

    projeto = " ".join(tokens[:-2])

    usuario = resolver_usuario(codigo)

    # I9 -> ILHA-09
    if ilha_raw.startswith("I"):
        numero = ilha_raw[1:]

        if numero.isdigit():
            ilha = f"ILHA-{numero.zfill(2)}"
        else:
            ilha = ilha_raw
    else:
        ilha = ilha_raw

    # Verifica se existe algo na pasta timeline para considerar como concluído
    pasta_timeline = os.path.join(
        abs_monitorada,
        pasta_nome,
        "timeline"
    )

    concluido = False

    if os.path.isdir(pasta_timeline):
        try:
            arquivos_timeline = [
                arquivo
                for arquivo in os.listdir(pasta_timeline)
                if os.path.isfile(
                    os.path.join(pasta_timeline, arquivo)
                )
            ]

            # tem arquivo na pasta timeline = concluido
            concluido = len(arquivos_timeline) > 0

        except Exception:
            concluido = False

    # Tamanho do arquivo (MB) — usado pela camada de IA para prever o ETC
    tamanho_mb = 0.0
    try:
        if os.path.isfile(abs_arquivo):
            tamanho_mb = round(os.path.getsize(abs_arquivo) / (1024 * 1024), 2)
    except OSError:
        tamanho_mb = 0.0

    return {
        "pasta": pasta_nome,
        "ilha": ilha,
        "usuario": usuario,
        "projeto": projeto,
        "concluido": concluido,
        "tamanho_mb": tamanho_mb,
    }


class MonitorHandler(FileSystemEventHandler):

    def __init__(self):
        self.ultimos_eventos = {}
        self.intervalo = 1

    def evento_duplicado(self, event):

        chave = (
            event.event_type,
            getattr(event, "dest_path", None) or event.src_path
        )

        agora = time.time()

        if chave in self.ultimos_eventos:
            if agora - self.ultimos_eventos[chave] < self.intervalo:
                return True

        self.ultimos_eventos[chave] = agora
        return False

    def processar_evento(self, event):

        if not event.src_path:
            return

        caminho_evento = (
            getattr(event, "dest_path", None)
            or event.src_path
        )

        # Permite eventos da pasta timeline, mas ignora eventos de outras pastas ocultas
        if event.is_directory:

            nome_dir = os.path.basename(
                caminho_evento
            ).lower()

            if nome_dir != "timeline":
                return

        # Se houve evento dentro da pasta timeline,
        # força recálculo do status do projeto

        caminho_normalizado = caminho_evento.replace(
            "\\",
            "/"
        )

        if "/timeline/" in caminho_normalizado:

            pasta_final = os.path.dirname(
                caminho_evento
            )

            if os.path.basename(
                pasta_final
            ).lower() == "timeline":

                pasta_projeto = os.path.dirname(
                    pasta_final
                )

                caminho_evento = os.path.join(
                    pasta_projeto,
                    "__status_check__"
                )

                # Aguarda o SO atualizar o disco antes de ler a pasta
                time.sleep(0.3)

        abs_monitorada = os.path.abspath(
            PASTA_MONITORADA
        )

        abs_evento = os.path.abspath(
            caminho_evento
        )

        if not abs_evento.startswith(
            abs_monitorada
        ):
            return

        if self.evento_duplicado(event):
            return

        info = extrair_info_pasta(
            caminho_evento
        )

        status = (
            "concluido"
            if info.get("concluido")
            else "ocupado"
        )

        payload = {
            "tipoEvento": event.event_type,
            "arquivo": os.path.basename(
                getattr(event, "dest_path", None)
                or event.src_path
            ),
            "caminho": abs_evento,
            "diretorio": event.is_directory,
            "timestamp": time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "pasta": info.get("pasta", ""),
            "ilha": info.get("ilha", ""),
            "usuario": info.get("usuario", ""),
            "projeto": info.get("projeto", ""),
            "status": status,
            "tamanho_mb": info.get("tamanho_mb", 0),
        }

        try:

            response = requests.post(
                BACKEND_URL,
                json=payload,
                timeout=5
            )

            print(
                f"[OK] {payload['tipoEvento'].upper():10} | "
                f"{payload['arquivo']}"
            )

            print(
                f"     ilha={payload['ilha']} | "
                f"usuario={payload['usuario']} | "
                f"projeto={payload['projeto']} | "
                f"status={payload['status']}"
            )

            print(
                f"     backend={response.status_code}"
            )

        except requests.RequestException as e:
            print(f"[ERRO] {e}")

    def on_any_event(self, event):
        self.processar_evento(event)


if __name__ == "__main__":

    os.makedirs(
        PASTA_MONITORADA,
        exist_ok=True
    )

    handler = MonitorHandler()

    observer = Observer()

    observer.schedule(
        handler,
        PASTA_MONITORADA,
        recursive=True
    )

    observer.start()

    print(
        f"[WATCHDOG] Monitorando: "
        f"{os.path.abspath(PASTA_MONITORADA)}"
    )

    print(
        f"[WATCHDOG] Backend: {BACKEND_URL}\n"
    )

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        observer.stop()

        print(
            "\n[WATCHDOG] Encerrado."
        )

    observer.join()
