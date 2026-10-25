# Dokumentasi API - Sistem Informasi Manajemen Pesanan Jasa Jahit Online

## 1. Deskripsi Singkat Project

**Sistem Informasi Manajemen Pesanan Jasa Jahit Online** adalah layanan RESTful API berbasis **Python Flask** dan **PostgreSQL** (Supabase) yang dirancang khusus untuk operasional usaha penjahit tunggal (*single-tailor*). 

API ini memfasilitasi pencatatan pesanan secara digital dan terstruktur, mengelola katalog jenis layanan jahit, pilihan bahan/kain, pendaftaran data pelanggan, penyimpanan ukuran fisik pakaian (lingkar dada dan panjang baju), hingga pembaruan status pengerjaan busana secara real-time.

---

## 2. ERD / Skema Database

```text
customers (id) ──< orders (customer_id) ──< order_items (order_id) >── service_types (id)
                                                 │
                                                 └──> fabric_types (id)
```

### Penjelasan Relasi:
* **customers ──< orders ($1 : N$)**: Satu pelanggan dapat membuat banyak transaksi pesanan.
* **orders ──< order_items ($1 : N$)**: Satu transaksi pesanan dapat memuat beberapa rincian item/baju yang dijahit.
* **order_items >── service_types ($N : 1$)**: Banyak rincian item pesanan dapat menggunakan jenis layanan jahit yang sama.
* **order_items >── fabric_types ($N : 1$)**: Banyak rincian item pesanan dapat memilih jenis bahan/kain yang sama.

---

## 3. Link URL Deployment

* **Base URL Vercel:** `https://projek-akhir-bank-end-fadhel.vercel.app`

---

## 4. Daftar Seluruh Endpoint

### 1. Menambah Pelanggan Baru
- **Method**       : POST
- **URL**          : https://projek-akhir-bank-end-fadhel.vercel.app/customers
- **Deskripsi**    : Mendaftarkan data pelanggan baru ke dalam sistem
- **Headers**      : Content-Type: application/json
- **Request Body** :
  ```json
  {
    "name": "Budi Santoso",
    "phone": "081234567890",
    "address": "Jl. Mawar No. 12, Surakarta"
  }
  ```
- **Response Sukses (201 Created)**:
  ```json
  {
    "data": {
      "address": "Jl. Mawar No. 12, Surakarta",
      "id": 1,
      "name": "Budi Santoso",
      "phone": "081234567890"
    },
    "message": "Pelanggan berhasil ditambahkan"
  }
  ```
- **Response Error (400 Bad Request)**:
  ```json
  {
    "error": "Field name, phone, dan address wajib diisi"
  }
  ```

---

### 2. Mengambil Katalog Layanan Jahit
- **Method**       : GET
- **URL**          : https://projek-akhir-bank-end-fadhel.vercel.app/services
- **Deskripsi**    : Mengambil seluruh daftar jenis layanan jahit beserta tarif harganya
- **Headers**      : None
- **Request Body** : None
- **Response Sukses (200 OK)**:
  ```json
  {
    "data": [
      {
        "id": 1,
        "price": 150000,
        "service_name": "Jahit Kemeja Pria"
      },
      {
        "id": 2,
        "price": 250000,
        "service_name": "Jahit Gaun Pesta"
      },
      {
        "id": 3,
        "price": 50000,
        "service_name": "Permak Celana Jeans"
      }
    ]
  }
  ```
- **Response Error (500 Internal Server Error)**:
  ```json
  {
    "error": "Database connection error"
  }
  ```

---

### 3. Menambahkan Transaksi Pesanan Baru
- **Method**       : POST
- **URL**          : https://projek-akhir-bank-end-fadhel.vercel.app/orders
- **Deskripsi**    : Membuat pesanan jahit baru lengkap dengan rincian ukuran fisik dan pilihan bahan kain
- **Headers**      : Content-Type: application/json
- **Request Body** :
  ```json
  {
    "customer_id": 1,
    "items": [
      {
        "service_type_id": 1,
        "fabric_type_id": 2,
        "chest_size": 98.5,
        "shirt_length": 72.0,
        "quantity": 1
      }
    ]
  }
  ```
- **Response Sukses (201 Created)**:
  ```json
  {
    "data": {
      "customer_id": 1,
      "items": [
        {
          "chest_size": "98.50",
          "fabric_type_id": 2,
          "id": 3,
          "order_id": 5,
          "quantity": 1,
          "service_type_id": 1,
          "shirt_length": "72.00",
          "subtotal": 150000
        }
      ],
      "order_date": "2026-10-25 11:33:08",
      "order_id": 5,
      "status": "Pending"
    },
    "message": "Pesanan berhasil dibuat"
  }
  ```
- **Response Error (500 Internal Server Error / Foreign Key Error)**:
  ```json
  {
    "error": "insert or update on table \"order_items\" violates foreign key constraint \"fk_fabric_type\"\nDETAIL: Key (fabric_type_id)=(2) is not present in table \"fabric_types\".\n"
  }
  ```

---

### 4. Memperbarui Status Pesanan
- **Method**       : PATCH
- **URL**          : https://projek-akhir-bank-end-fadhel.vercel.app/orders/5
- **Deskripsi**    : Memperbarui status pengerjaan pesanan berdasarkan ID pesanan
- **Headers**      : Content-Type: application/json
- **Request Body** :
  ```json
  {
    "status": "Diproses"
  }
  ```
- **Response Sukses (200 OK)**:
  ```json
  {
    "data": {
      "id": 5,
      "status": "Diproses"
    },
    "message": "Status pesanan berhasil diperbarui"
  }
  ```
- **Response Error (404 Not Found)**:
  ```json
  {
    "error": "Pesanan dengan ID 5 tidak ditemukan"
  }
  ```

---

### 5. Menghapus / Membatalkan Pesanan
- **Method**       : DELETE
- **URL**          : https://projek-akhir-bank-end-fadhel.vercel.app/orders/5
- **Deskripsi**    : Menghapus data transaksi pesanan dari database berdasarkan ID
- **Headers**      : None
- **Request Body** : None
- **Response Sukses (200 OK)**:
  ```json
  {
    "message": "Pesanan dengan ID 5 berhasil dihapus"
  }
  ```
- **Response Error (404 Not Found)**:
  ```json
  {
    "error": "Pesanan dengan ID 5 tidak ditemukan"
  }
  ```

---

## 5. Cara Menjalankan Project secara Lokal

1. **Clone Repositori Git:**
   ```bash
   git clone https://github.com/username/projek-akhir-backend.git
   cd projek-akhir-backend
   ```

2. **Buat Virtual Environment & Install Dependency:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Untuk Linux/Mac
   # atau
   venv\Scripts\activate     # Untuk Windows

   pip install -r requirements.txt
   ```

3. **Konfigurasi Environment Variables:**
   Buat file `.env` di direktori utama proyek dan tambahkan string koneksi PostgreSQL Supabase milikmu:
   ```env
   DATABASE_URL=postgresql://postgres:PASSWORD_DATABASE@db.hqdtzodsxgumdkwmevdx.supabase.co:5432/postgres
   ```

4. **Jalankan Aplikasi Server:**
   ```bash
   python app.py
   ```
   *Aplikasi akan berjalan secara lokal di `http://127.0.0.1:5000`.*
