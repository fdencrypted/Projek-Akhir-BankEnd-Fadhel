import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Izinkan Cross-Origin Resource Sharing

# ==========================================
# HELPER: DATABASE CONNECTION
# ==========================================
def get_db_connection():
    """Membuat koneksi ke database PostgreSQL (Supabase / Neon / Local)"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is missing!")
    
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    return conn

# Helper response
def response_json(data=None, message="", status_code=200, error=None):
    payload = {}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    if error:
        payload["error"] = error
    return jsonify(payload), status_code

# Root Endpoint Check
@app.route("/", methods=["GET"])
def index():
    return response_json(
        message="Tailor Order Management REST API is running!",
        status_code=200
    )

# ==========================================
# 1. MASTER DATA: SERVICE TYPES
# ==========================================
@app.route("/services", methods=["GET"])
def get_all_services():
    """GET /services - Mengambil katalog layanan jahit"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, service_name, price FROM service_types ORDER BY id ASC;")
        services = cur.fetchall()
        cur.close()
        conn.close()
        return response_json(data=services, status_code=200)
    except Exception as e:
        return response_json(error=str(e), status_code=500)

@app.route("/services", methods=["POST"])
def create_service():
    """POST /services - Menambah layanan jahit baru"""
    body = request.get_json() or {}
    service_name = body.get("service_name")
    price = body.get("price")

    if not service_name or price is None:
        return response_json(error="Field service_name dan price wajib diisi", status_code=400)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO service_types (service_name, price) VALUES (%s, %s) RETURNING *;",
            (service_name, price)
        )
        new_service = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return response_json(data=new_service, message="Layanan berhasil ditambahkan", status_code=201)
    except Exception as e:
        return response_json(error=str(e), status_code=500)

# ==========================================
# 2. MASTER DATA: FABRIC TYPES
# ==========================================
@app.route("/fabrics", methods=["GET"])
def get_all_fabrics():
    """GET /fabrics - Mengambil daftar jenis bahan/kain"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, fabric_name FROM fabric_types ORDER BY id ASC;")
        fabrics = cur.fetchall()
        cur.close()
        conn.close()
        return response_json(data=fabrics, status_code=200)
    except Exception as e:
        return response_json(error=str(e), status_code=500)

@app.route("/fabrics", methods=["POST"])
def create_fabric():
    """POST /fabrics - Menambah varian kain baru"""
    body = request.get_json() or {}
    fabric_name = body.get("fabric_name")

    if not fabric_name:
        return response_json(error="Field fabric_name wajib diisi", status_code=400)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO fabric_types (fabric_name) VALUES (%s) RETURNING *;",
            (fabric_name,)
        )
        new_fabric = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return response_json(data=new_fabric, message="Jenis bahan berhasil ditambahkan", status_code=201)
    except Exception as e:
        return response_json(error=str(e), status_code=500)

# ==========================================
# 3. DATA CUSTOMER
# ==========================================
@app.route("/customers", methods=["GET"])
def get_all_customers():
    """GET /customers - Mengambil seluruh data pelanggan"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, phone, address FROM customers ORDER BY id ASC;")
        customers = cur.fetchall()
        cur.close()
        conn.close()
        return response_json(data=customers, status_code=200)
    except Exception as e:
        return response_json(error=str(e), status_code=500)

@app.route("/customers", methods=["POST"])
def create_customer():
    """POST /customers - Mendaftarkan pelanggan baru"""
    body = request.get_json() or {}
    name = body.get("name")
    phone = body.get("phone")
    address = body.get("address")

    if not name or not phone or not address:
        return response_json(error="Field name, phone, dan address wajib diisi", status_code=400)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO customers (name, phone, address) VALUES (%s, %s, %s) RETURNING *;",
            (name, phone, address)
        )
        new_customer = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return response_json(data=new_customer, message="Pelanggan berhasil ditambahkan", status_code=201)
    except Exception as e:
        return response_json(error=str(e), status_code=500)

# ==========================================
# 4. TRANSAKSI ORDERS (CRUD COMPLETE)
# ==========================================
@app.route("/orders", methods=["POST"])
def create_order():
    """POST /orders - Membuat pesanan baru beserta detail ukuran & item"""
    body = request.get_json() or {}
    customer_id = body.get("customer_id")
    items = body.get("items", [])

    if not customer_id or not items or not isinstance(items, list):
        return response_json(error="Field customer_id dan minimal 1 item pesanan wajib diisi", status_code=400)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Cek keberadaan customer
        cur.execute("SELECT id FROM customers WHERE id = %s;", (customer_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return response_json(error=f"Customer dengan ID {customer_id} tidak ditemukan", status_code=404)

        # 2. Buat record di tabel orders
        cur.execute(
            "INSERT INTO orders (customer_id, status) VALUES (%s, 'Pending') RETURNING id, order_date, status;",
            (customer_id,)
        )
        order_res = cur.fetchone()
        order_id = order_res["id"]

        # 3. Insert items ke order_items
        created_items = []
        for item in items:
            service_id = item.get("service_type_id")
            fabric_id = item.get("fabric_type_id")
            chest_size = item.get("chest_size")
            shirt_length = item.get("shirt_length")
            quantity = item.get("quantity", 1)

            # Ambil harga layanan dari database
            cur.execute("SELECT price FROM service_types WHERE id = %s;", (service_id,))
            service_data = cur.fetchone()
            if not service_data:
                conn.rollback()
                cur.close()
                conn.close()
                return response_json(error=f"Service ID {service_id} tidak valid", status_code=400)

            price = service_data["price"]
            subtotal = price * quantity

            cur.execute(
                """
                INSERT INTO order_items 
                (order_id, service_type_id, fabric_type_id, chest_size, shirt_length, quantity, subtotal)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *;
                """,
                (order_id, service_id, fabric_id, chest_size, shirt_length, quantity, subtotal)
            )
            created_items.append(cur.fetchone())

        conn.commit()
        cur.close()
        conn.close()

        result = {
            "order_id": order_id,
            "customer_id": customer_id,
            "status": order_res["status"],
            "order_date": order_res["order_date"].strftime("%Y-%m-%d %H:%M:%S"),
            "items": created_items
        }

        return response_json(data=result, message="Pesanan berhasil dibuat", status_code=201)

    except Exception as e:
        return response_json(error=str(e), status_code=500)


@app.route("/orders", methods=["GET"])
def get_all_orders():
    """GET /orders - Mengambil seluruh daftar pesanan masuk"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
        SELECT 
            o.id AS order_id,
            o.order_date,
            o.status,
            c.id AS customer_id,
            c.name AS customer_name,
            c.phone AS customer_phone,
            c.address AS customer_address
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        ORDER BY o.id DESC;
        """
        cur.execute(query)
        orders = cur.fetchall()

        # Format datetime
        for o in orders:
            o["order_date"] = o["order_date"].strftime("%Y-%m-%d %H:%M:%S")

        cur.close()
        conn.close()
        return response_json(data=orders, status_code=200)
    except Exception as e:
        return response_json(error=str(e), status_code=500)


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order_by_id(order_id):
    """GET /orders/:id - Mengambil detail pesanan spesifik"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Ambil data order & customer
        query_order = """
        SELECT 
            o.id AS order_id,
            o.order_date,
            o.status,
            c.id AS customer_id,
            c.name AS customer_name,
            c.phone AS customer_phone,
            c.address AS customer_address
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        WHERE o.id = %s;
        """
        cur.execute(query_order, (order_id,))
        order = cur.fetchone()

        if not order:
            cur.close()
            conn.close()
            return response_json(error=f"Pesanan dengan ID {order_id} tidak ditemukan", status_code=404)

        # 2. Ambil detail items
        query_items = """
        SELECT 
            oi.id AS item_id,
            st.service_name,
            ft.fabric_name,
            oi.chest_size,
            oi.shirt_length,
            oi.quantity,
            oi.subtotal
        FROM order_items oi
        JOIN service_types st ON oi.service_type_id = st.id
        JOIN fabric_types ft ON oi.fabric_type_id = ft.id
        WHERE oi.order_id = %s;
        """
        cur.execute(query_items, (order_id,))
        items = cur.fetchall()

        cur.close()
        conn.close()

        order["order_date"] = order["order_date"].strftime("%Y-%m-%d %H:%M:%S")
        order["items"] = items

        return response_json(data=order, status_code=200)

    except Exception as e:
        return response_json(error=str(e), status_code=500)


@app.route("/orders/<int:order_id>", methods=["PATCH"])
def update_order_status(order_id):
    """PATCH /orders/:id - Update status pengerjaan pesanan"""
    body = request.get_json() or {}
    new_status = body.get("status")

    if not new_status:
        return response_json(error="Field status wajib diisi", status_code=400)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE orders SET status = %s WHERE id = %s RETURNING id, status;",
            (new_status, order_id)
        )
        updated_order = cur.fetchone()

        if not updated_order:
            cur.close()
            conn.close()
            return response_json(error=f"Pesanan dengan ID {order_id} tidak ditemukan", status_code=404)

        conn.commit()
        cur.close()
        conn.close()

        return response_json(data=updated_order, message="Status pesanan berhasil diperbarui", status_code=200)

    except Exception as e:
        return response_json(error=str(e), status_code=500)


@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    """DELETE /orders/:id - Menghapus/membatalkan pesanan"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM orders WHERE id = %s RETURNING id;", (order_id,))
        deleted_order = cur.fetchone()

        if not deleted_order:
            cur.close()
            conn.close()
            return response_json(error=f"Pesanan dengan ID {order_id} tidak ditemukan", status_code=404)

        conn.commit()
        cur.close()
        conn.close()

        return response_json(message=f"Pesanan dengan ID {order_id} berhasil dihapus", status_code=200)

    except Exception as e:
        return response_json(error=str(e), status_code=500)


# Jalankan server lokal jika di-run secara langsung
if __name__ == "__main__":
    app.run(debug=True, port=5000)