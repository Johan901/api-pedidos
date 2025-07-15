import psycopg2
import requests
from requests.auth import HTTPBasicAuth
import os

WOO_URL = "https://dulceguadalupe.com/wp-json/wc/v3/products"
CONSUMER_KEY = os.environ.get("WOO_CK")
CONSUMER_SECRET = os.environ.get("WOO_CS")

def get_conn():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        port=os.environ.get("DB_PORT")
    )

def actualizar_productos_existentes():
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT ref, color, precio_al_detal, precio_por_mayor
            FROM inventario
            WHERE creado_en_woo = TRUE
        """)
        productos = cur.fetchall()

        for ref, color, detal, mayor in productos:
            sku = f"{ref}-{color}".replace(" ", "").upper()
            nombre = sku

            # Buscar el producto en WooCommerce por SKU
            r = requests.get(
                WOO_URL,
                params={"sku": sku},
                auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET)
            )

            if r.status_code == 200:
                resultados = r.json()
                if resultados:
                    product_id = resultados[0]["id"]

                    # Actualizar nombre y precios
                    payload = {
                        "name": nombre,
                        "regular_price": str(int(detal)),
                        "sale_price": str(int(mayor))
                    }

                    r_update = requests.put(
                        f"{WOO_URL}/{product_id}",
                        json=payload,
                        auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET)
                    )

                    if r_update.status_code == 200:
                        print(f"✅ Producto {sku} actualizado correctamente.")
                    else:
                        print(f"❌ Error actualizando {sku}: {r_update.status_code} - {r_update.text}")
                else:
                    print(f"⚠️ Producto con SKU {sku} no encontrado en WooCommerce.")
            else:
                print(f"❌ Error buscando producto {sku}: {r.status_code}")

        cur.close()
        conn.close()

    except Exception as e:
        print("❌ Error general:", str(e))
