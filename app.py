from flask import Flask, jsonify
import psycopg2
import os

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT")

@app.route("/sync", methods=["GET"])
def sync():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("SELECT ref, cantidad FROM inventario")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        data = [{"sku": row[0], "cantidad": row[1]} for row in rows]
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "✅ API de sincronización activa - Dulce Guadalupe"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
