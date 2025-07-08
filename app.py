from flask import Flask, jsonify
import psycopg2
import os
import schedule
import threading
import time
import requests

app = Flask(__name__)

# Configuración desde variables de entorno
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
        cur.execute("SELECT ref, color, cantidad FROM inventario")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        data = [
            {
                "sku": f"{row[0]}-{row[1]}".upper().replace(" ", ""),
                "cantidad": row[2]
            }
            for row in rows
        ]
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "✅ API de sincronización activa - Dulce Guadalupe"

# 🔁 Sincronizar stock con WordPress cada minuto
def sync_wordpress_stock():
    try:
        url = "https://dulceguadalupe.com/actualizar-stock-1m-solo-aurora/"
        response = requests.get(url)
        print("✅ Stock sincronizado con WordPress:", response.status_code)
    except Exception as e:
        print("❌ Error sincronizando stock:", str(e))

def scheduler_loop():
    schedule.every(1).minutes.do(sync_wordpress_stock)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Lanzar hilo de sincronización al iniciar
threading.Thread(target=scheduler_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
