from flask import Flask, jsonify, request
import sqlite3
import requests
import time

app = Flask(__name__)

DB_NAME = "productos.db"
TOKEN_SECRETO = "pinguino-123"
URL_INVENTARIO = "http://127.0.0.1:5002/stock"

def request_con_retry(url, headers, intentos=3, espera=1):
    for intento in range(intentos):
        try:
            print(f"[INFO] Llamando a inventario (intento {intento + 1})")
            response = requests.get(url, headers=headers, timeout=2)
            return response
        except requests.exceptions.RequestException as e:
            print(f"[WARN] Falló el intento {intento + 1}: {e}")
            time.sleep(espera)

    print("[ERROR] Inventario no responde luego de varios intentos")
    return None


#  Seguridad
def verificar_token():
    auth = request.headers.get("Authorization")
    return auth == f"Bearer {TOKEN_SECRETO}"


#  Base de datos
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            precio INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


#  TODOS LOS PRODUCTOS + STOCK
@app.route("/productos", methods=["GET"])
def obtener_productos():
    if not verificar_token():
        return {"error": "No autorizado"}, 401

    headers = {
        "Authorization": f"Bearer {TOKEN_SECRETO}"
    }

    conn = get_db()
    productos = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()

    resultado = []

    for producto in productos:
        resp = request_con_retry(
            f"{URL_INVENTARIO}/{producto['id']}",
            headers=headers
        )


        stock = resp.json().get("stock", 0) if resp.status_code == 200 else 0

        resultado.append({
            "id": producto["id"],
            "nombre": producto["nombre"],
            "precio": producto["precio"],
            "stock": stock
        })

    return jsonify(resultado)


#  UN PRODUCTO POR ID + STOCK
@app.route("/productos/<int:id_producto>", methods=["GET"])
def obtener_producto(id_producto):
    if not verificar_token():
        return {"error": "No autorizado"}, 401

    headers = {
        "Authorization": f"Bearer {TOKEN_SECRETO}"
    }

    conn = get_db()
    producto = conn.execute(
        "SELECT * FROM productos WHERE id = ?",
        (id_producto,)
    ).fetchone()
    conn.close()

    if not producto:
        return {"error": "Producto no encontrado"}, 404

    resp = requests.get(
        f"{URL_INVENTARIO}/{id_producto}",
        headers=headers
    )

    stock = resp.json().get("stock", 0) if resp.status_code == 200 else 0

    return jsonify({
        "id": producto["id"],
        "nombre": producto["nombre"],
        "precio": producto["precio"],
        "stock": stock
    })



if __name__ == "__main__":
    init_db()
    app.run(port=5001, debug=True)
