import psycopg2
import requests
from requests.auth import HTTPBasicAuth
import os

# URL y credenciales de WooCommerce
WOO_URL = "https://dulceguadalupe.com/wp-json/wc/v3/products"
CONSUMER_KEY = os.environ.get("WOO_CK")
CONSUMER_SECRET = os.environ.get("WOO_CS")

# Conexión a la base de datos
def get_conn():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        port=os.environ.get("DB_PORT")
    )

# Función principal para crear productos nuevos
def crear_productos_nuevos():
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT ref, tipo_prenda, color, cantidad, precio_al_detal
            FROM inventario
            WHERE creado_en_woo = FALSE
        """)
        productos = cur.fetchall()

        for ref, tipo, color, cantidad, detal in productos:
            sku = f"{ref}-{color}".replace(" ", "").upper()
            nombre = f"{tipo.title()} {color.title()}"

            payload = {
                "name": nombre,
                "type": "simple",
                "regular_price": str(int(detal)),
                "stock_quantity": cantidad,
                "manage_stock": True,
                "sku": sku,
                "description": f"{tipo.title()} color {color.title()} subido automáticamente desde Aurora."
            }

            r = requests.post(
                WOO_URL,
                json=payload,
                auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET)
            )

            # Producto creado exitosamente
            if r.status_code == 201:
                print(f"✅ Producto {sku} creado en WooCommerce.")
                cur.execute("""
                    UPDATE inventario SET creado_en_woo = TRUE WHERE ref = %s AND color = %s
                """, (ref, color))
                conn.commit()

            # El SKU ya existe, lo marcamos como creado igual
            elif r.status_code == 400 and "SKU already exists" in r.text:
                print(f"⚠️ SKU {sku} ya existe en WooCommerce. Marcado como creado.")
                cur.execute("""
                    UPDATE inventario SET creado_en_woo = TRUE WHERE ref = %s AND color = %s
                """, (ref, color))
                conn.commit()

            # ❌ Otro tipo de error
            else:
                print(f"❌ Error creando producto {sku}: {r.status_code} - {r.text}")

        cur.close()
        conn.close()

    except Exception as e:
        print("❌ Error general en sincronización:", str(e))
