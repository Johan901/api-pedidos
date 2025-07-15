import psycopg2
import requests
from requests.auth import HTTPBasicAuth
import os

# URL y credenciales de WooCommerce
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

def crear_productos_nuevos():
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT ref, tipo_prenda, color, cantidad, precio_al_detal, precio_por_mayor
            FROM inventario
            WHERE creado_en_woo = FALSE
        """)
        productos = cur.fetchall()

        for ref, tipo, color, cantidad, detal, mayor in productos:
            sku = f"{ref}-{color}".replace(" ", "").upper()
            nombre = sku
            descripcion = f"{tipo.title()} color {color.title()} subido automáticamente desde Aurora."

            payload = {
                "name": nombre,
                "type": "simple",
                "regular_price": str(int(detal)),
                "sale_price": str(int(mayor)),
                "stock_quantity": cantidad,
                "manage_stock": True,
                "sku": sku,
                "description": descripcion
            }

            r = requests.post(WOO_URL, json=payload, auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET))

            if r.status_code == 201:
                print(f"✅ Producto {sku} creado en WooCommerce.")
                cur.execute("UPDATE inventario SET creado_en_woo = TRUE WHERE ref = %s AND color = %s", (ref, color))
                conn.commit()

            elif r.status_code == 400 and "SKU already exists" in r.text:
                print(f"🔎 Verificando coincidencia para SKU existente: {sku}")
                r_get = requests.get(WOO_URL + f"?sku={sku}", auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET))
                
                if r_get.status_code == 200 and len(r_get.json()) > 0:
                    p = r_get.json()[0]
                    coincidencias = (
                        p["name"] == nombre and
                        p["regular_price"] == str(int(detal)) and
                        p["sale_price"] == str(int(mayor)) and
                        int(p.get("stock_quantity", 0)) == cantidad and
                        descripcion in p["description"]
                    )
                    if coincidencias:
                        print(f"✅ Producto {sku} ya coincide completamente. Marcado como creado.")
                        cur.execute("UPDATE inventario SET creado_en_woo = TRUE WHERE ref = %s AND color = %s", (ref, color))
                        conn.commit()
                    else:
                        print(f"⚠️ SKU {sku} ya existe pero con diferencias. No se marca como creado.")
                else:
                    print(f"❌ No se pudo obtener el producto {sku} para verificar.")

            else:
                print(f"❌ Error creando producto {sku}: {r.status_code} - {r.text}")

        cur.close()
        conn.close()

    except Exception as e:
        print("❌ Error general en sincronización:", str(e))
