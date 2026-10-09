from datetime import datetime, timedelta
import json
import os

import requests
from flask import Blueprint, request, jsonify

from database import redis_client

event_bp = Blueprint("events", __name__)

REDIS_QUEUE = "eventos_watchdog"   # fila FIFO consumida pelo worker

# URL do serviço de IA (data_ia/predictor.py). Opcional — se estiver fora do
# ar, a predição é simplesmente pulada e o evento continua sendo processado.
PREDICTOR_URL = os.getenv("PREDICTOR_URL", "http://data_ia:5001")
PREDICTOR_TIMEOUT = 1.5


def consultar_previsao(usuario: str, tamanho_mb: float) -> dict:
    """Pergunta ao serviço de IA quantos minutos faltam para concluir a edição.

    Best-effort: qualquer falha (serviço fora do ar, timeout, sem dados
    suficientes ainda) apenas resulta em nenhuma previsão, sem quebrar o
    fluxo de ingestão de eventos.
    """
    if not usuario or not tamanho_mb:
        return {}

    try:
        resp = requests.post(
            f"{PREDICTOR_URL}/predict",
            json={"editor": usuario, "tamanho_mb": tamanho_mb},
            timeout=PREDICTOR_TIMEOUT,
        )
        resp.raise_for_status()
        minutos = resp.json().get("minutos")
        if not minutos:
            return {}

        previsao_fim = (datetime.now() + timedelta(minutes=minutos)).strftime("%H:%M")
        return {
            "previsao_restante_min": minutos,
            "previsao_fim": previsao_fim,
        }
    except requests.RequestException:
        return {}


@event_bp.route("/events", methods=["POST"])
def receive_event():
    data = request.get_json()

    if not data:
        return jsonify({"status": "erro", "message": "Payload vazio"}), 400

    # ── 1. Fila para o Worker ETL (persistência no Postgres) ──────────────────
    redis_client.rpush(REDIS_QUEUE, json.dumps(data, ensure_ascii=False))

    # ── 2. Estado em tempo real para o Dashboard (sobrescreve por editor) ─────
    usuario = data.get("usuario", "")
    if usuario:
        tamanho_mb = data.get("tamanho_mb", 0) or 0
        status = data.get("status", "ocupado")

        estado = {
            "status":      status,
            "editor":      usuario,
            "ilha":        data.get("ilha", ""),
            "projeto":     data.get("projeto", ""),
            "arquivo":     data.get("arquivo", ""),
            "ultimo_save": data.get("timestamp", ""),
            "tipo_evento": data.get("tipoEvento", ""),
            "tamanho_mb":  tamanho_mb,
        }

        # Só faz sentido prever ETC para edições ainda em andamento.
        if status == "ocupado":
            estado.update(consultar_previsao(usuario, tamanho_mb))

        chave_estado = f"editor:{usuario.lower().replace(' ', '_')}"
        redis_client.hset(chave_estado, mapping=estado)
        redis_client.expire(chave_estado, 3600)   # expira em 1h sem atividade

    fila_tamanho = redis_client.llen(REDIS_QUEUE)

    print(f"[EVENT] {data.get('tipoEvento','?'):10} | {data.get('arquivo','?')}")
    print(f"        ilha={data.get('ilha','—')} | usuario={usuario or '—'} | projeto={data.get('projeto','—')}")
    print(f"        fila={fila_tamanho} item(s) pendentes")

    return jsonify({
        "status":  "ok",
        "message": "Evento enfileirado com sucesso",
        "fila":    fila_tamanho,
        "data":    data
    }), 200


@event_bp.route("/events/status", methods=["GET"])
def status_editores():
    """Retorna o estado atual de todos os editores (tempo real via Redis)."""
    chaves = redis_client.keys("editor:*")
    editores = []

    for chave in chaves:
        dados = redis_client.hgetall(chave)
        if dados:
            editores.append(dados)

    return jsonify({
        "total":    len(editores),
        "editores": editores
    }), 200


@event_bp.route("/events/fila", methods=["GET"])
def ver_fila():
    """Retorna quantos eventos estão pendentes na fila (sem consumir)."""
    tamanho = redis_client.llen(REDIS_QUEUE)
    return jsonify({
        "fila":    REDIS_QUEUE,
        "tamanho": tamanho
    }), 200
