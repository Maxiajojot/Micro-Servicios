from flask import Flask, jsonify, request
import sqlite3

#Creacion de la APP
app = Flask(__name__)
DB_NAME = "inventario.db"
TOKEN_SECRETO = "pinguino-123"

def verificar_token():
    auth = request.headers.get("Authorization")
    if auth != f"Bearer {TOKEN_SECRETO}": #Convencion, ver significado
        return False
    return True

def get_db():
    conn = sqlite3.connect(DB_NAME) #Abre conexion con la base de datos
    conn.row_factory = sqlite3.Row
    return conn #Devuelve la conexion para poder usar

def init_db():
    conn = get_db() #Crea la tabla
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id_producto INTEGER PRIMARY KEY,
            cantidad INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

#Defino mi endpoint con el Metodo GET
@app.route("/stock/<int:id_producto>", methods=["GET"])
#Funcion que se ejecuta cuando se llama al endpoint

def obtener_stock(id_producto):
    if not verificar_token():
        return {"error": "No autorizado"}, 401
    conn = get_db()
    row = conn.execute(
        "SELECT cantidad FROM stock WHERE id_producto = ?",
        (id_producto,)
    ).fetchone()
    conn.close()

    return jsonify({
        "id_producto": id_producto,
        "stock": row["cantidad"] if row else 0
    })

#Defino mi endpoint con el Metodo 
@app.route("/stock/descontar", methods=["POST"])
def descontar_stock():
    if not verificar_token():
        return {"error": "No autorizado"}, 401
    datos = request.json
    id_producto = datos["id_producto"]
    cantidad = datos["cantidad"]

    conn = get_db()
    row = conn.execute(
        "SELECT cantidad FROM stock WHERE id_producto = ?",
        (id_producto,)
    ).fetchone()

    if not row or row["cantidad"] < cantidad:
        conn.close()
        return {"error": "Stock insuficiente"}, 400

    #Resto la cantidad que se pidio
    conn.execute(
        "UPDATE stock SET cantidad = cantidad - ? WHERE id_producto = ?",
        (cantidad, id_producto)
    )
    conn.commit()
    conn.close()

    return {"mensaje": "Stock actualizado"}

@app.route("/cargar", methods=["POST"])
def cargar_stock():
    auth = request.headers.get("Authorization")
    if auth != f"Bearer {TOKEN_SECRETO}":
        return {"error": "No autorizado"}, 401

    datos = request.json
    id_producto = datos["id_producto"]
    cantidad = datos["cantidad"]

    conn = get_db()

    # Verificar si el producto existe en inventario
    row = conn.execute(
        "SELECT cantidad FROM stock WHERE id_producto = ?",
        (id_producto,)
    ).fetchone()

    if not row:
        conn.close()
        return {
            "error": "No existe ese id"
        }, 404

    # Sumar stock
    conn.execute(
        "UPDATE stock SET cantidad = cantidad + ? WHERE id_producto = ?",
        (cantidad, id_producto)
    )

    conn.commit()
    conn.close()

    return {
        "mensaje": "Stock sumado correctamente",
        "id_producto": id_producto,
        "cantidad_agregada": cantidad
    }, 200


if __name__ == "__main__":
    init_db()
    app.run(port=5002, debug=True)
