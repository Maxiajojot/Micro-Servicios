from flask import Flask, jsonify, request

app = Flask(__name__)

stock = {
    1: 10,
    2: 5
}

@app.route("/stock/<int:id_producto>", methods=["GET"])
def obtener_stock(id_producto):
    return jsonify({
        "id_producto": id_producto,
        "stock": stock.get(id_producto, 0)
    })

@app.route("/stock/descontar", methods=["POST"])
def descontar_stock():
    datos = request.json
    id_producto = datos["id_producto"]
    cantidad = datos["cantidad"]

    if stock.get(id_producto, 0) < cantidad:
        return {"error": "Stock insuficiente"}, 400

    stock[id_producto] -= cantidad
    return {"mensaje": "Stock actualizado"}

if __name__ == "__main__":
    app.run(port=5002, debug=True)
