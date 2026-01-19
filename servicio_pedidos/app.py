from flask import Flask, request
import sqlite3
import requests
import time

app = Flask(__name__)

DB_NAME = "pedidos.db"
TOKEN_SECRETO = "pinguino-123"
URL_INVENTARIO = "http://127.0.0.1:5002/stock/descontar"

def request_con_retry(url, headers, json_data, intentos=3, espera=1):
    for intento in range(intentos):
        try:
            print(f"[INFO] Intento {intento + 1} de descontar stock")
            resp = requests.post(
                url,
                headers=headers,
                json=json_data,
                timeout=2
            )
            return resp
        except requests.exceptions.RequestException as e:
            print(f"[WARN] Falló intento {intento + 1}: {e}")
            time.sleep(espera)

    print("[ERROR] Inventario no responde luego de varios intentos")
    return None


def verificar_token():
    auth = request.headers.get("Authorization")
    if auth != f"Bearer {TOKEN_SECRETO}":
        return False
    return True


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_producto INTEGER,
            cantidad INTEGER
        )
    """)
    conn.commit()
    conn.close()


@app.route("/pedidos", methods=["POST"])
def crear_pedido():
    if not verificar_token():
        return {"error": "No autorizado"}, 401

    datos = request.json

    headers = {
        "Authorization": f"Bearer {TOKEN_SECRETO}"
    }

    respuesta = request_con_retry(
        URL_INVENTARIO,
        headers,
        {
            "id_producto": datos["id_producto"],
            "cantidad": datos["cantidad"]
        }
    )

    if respuesta.status_code != 200:
        return {
            "error": "No se pudo crear el pedido",
            "detalle": respuesta.text
        }, 400

    conn = get_db()
    conn.execute(
        "INSERT INTO pedidos (id_producto, cantidad) VALUES (?, ?)",
        (datos["id_producto"], datos["cantidad"])
    )
    conn.commit()
    conn.close()

    return {"mensaje": "Pedido creado"}, 201


if __name__ == "__main__":
    init_db()
    app.run(port=5003, debug=True)
