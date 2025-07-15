import psycopg2
import requests
from requests.auth import HTTPBasicAuth
import os

# Credenciales WooCommerce
WOO_URL = "https://dulceguadalupe.com/wp-json/wc/v3/products"
CONSUMER_KEY = os.environ.get("WOO_CK")
CONSUMER_SECRET = os.environ.get("WOO_CS")

# Conexión a PostgreSQL
def get_conn():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        port=os.environ.get("DB_PORT")
    )

# 🔁 Función para actualizar productos con paginación
def actualizar_productos_existentes(offset=0, limit=100):
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT ref, tipo_prenda, color, precio_al_detal, precio_por_mayor
            FROM inventario
            WHERE creado_en_woo = TRUE
            ORDER BY fecha_creacion DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))

        productos = cur.fetchall()

        if not productos:
            print(f"✅ No hay más productos para actualizar desde offset {offset}.")
            return "No hay más productos para actualizar."

        for ref, tipo, color, detal, mayor in productos:
            sku = f"{ref}-{color}".replace(" ", "").upper()
            name = sku  # ⚠️ Nombre será igual al SKU
            payload = {
                "name": name,
                "regular_price": str(int(detal)),
                "sale_price": str(int(mayor)),
            }

            # Buscar el ID del producto por SKU
            r_get = requests.get(
                WOO_URL,
                params={"sku": sku},
                auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET)
            )
            if r_get.status_code == 200 and r_get.json():
                product_id = r_get.json()[0]['id']

                # Actualizar producto
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
                print(f"⚠️ No se encontró el producto con SKU {sku}.")

        cur.close()
        conn.close()
        return f"🛠️ Se actualizaron hasta 100 productos desde offset {offset}."

    except Exception as e:
        return f"❌ Error general: {str(e)}"
