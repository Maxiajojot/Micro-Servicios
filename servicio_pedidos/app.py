from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

URL_INVENTARIO = "http://127.0.0.1:5002/stock/descontar"

@app.route("/pedidos", methods=["POST"])
def crear_pedido():
    datos = request.json

    # 1️⃣ pedir al inventario que descuente stock
    respuesta = requests.post(
        URL_INVENTARIO,
        json={
            "id_producto": datos["id_producto"],
            "cantidad": datos["cantidad"]
        }
    )

    # 2️⃣ si inventario dice que NO
    if respuesta.status_code != 200:
        return {
            "error": "No hay stock suficiente",
            "detalle": respuesta.json()
        }, 400

    # 3️⃣ si inventario dice que SÍ
    return jsonify({
        "mensaje": "Pedido creado correctamente",
        "pedido": datos
    }), 201


if __name__ == "__main__":
    app.run(port=5003, debug=True)
