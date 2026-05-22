# Tugas Praktikum Docker Volume, Network, dan Docker Compose

[![Docker](https://img.shields.io/badge/Docker-Containerization-blue)](https://www.docker.com/)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-Orchestration-blue)](https://docs.docker.com/compose/)
[![Python](https://img.shields.io/badge/Python-3.9+-green)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-red)](https://flask.palletsprojects.com/)

## 📋 Daftar Isi

- [Tentang Project](#tentang-project)
- [Arsitektur](#arsitektur)
- [Persyaratan](#persyaratan)
- [Setup & Installation](#setup--installation)
- [Menjalankan Aplikasi](#menjalankan-aplikasi)
- [Testing & Monitoring](#testing--monitoring)
- [Struktur Project](#struktur-project)
- [Load Balancer](#load-balancer)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)
- [Dokumentasi Lengkap](#dokumentasi-lengkap)

---

## Tentang Project

Aplikasi Manajemen Barang adalah project UTS (Ujian Tengah Semester) untuk mata kuliah **Komputasi Awan (Cloud Computing)** yang mendemonstrasikan:

✅ **Containerization** dengan Docker  
✅ **Microservices Architecture** (Web + API separation)  
✅ **Database Persistence** dengan PostgreSQL  
✅ **Orchestration** menggunakan Docker Compose  
✅ **Scaling** dengan multiple container instances  
✅ **Load Balancing** dengan Nginx  
✅ **Networking** antar container  

### Fitur Utama

- 🔄 **REST API**: Backend API untuk mengelola data
- 🎨 **Web Interface**: Frontend untuk interaksi pengguna
- 💾 **Persistent Database**: PostgreSQL untuk data storage
- ⚖️ **Load Balancing**: Nginx untuk distribusi traffic
- 📊 **Scaling**: Kemampuan scale API instances secara horizontal

---

## Arsitektur

### Arsitektur Keseluruhan

```
┌─────────────────────────────────────────────────────────┐
│                   DOCKER COMPOSE NETWORK               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │           FRONTEND LAYER (8000/5000)              │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │  Web App (Flask)                           │ │  │
│  │  │  - Routes: GET /, POST /                    │ │  │
│  │  │  - Template rendering                      │ │  │
│  │  │  - HTTP client untuk API calls              │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                       │
│                 ▼ (requests.get/post)                   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         API LAYER (8080)                         │  │
│  │  ┌──────────────┐      ┌──────────────┐         │  │
│  │  │  API-1       │      │  API-2       │  ...    │  │
│  │  │  (scaled)    │      │  (scaled)    │         │  │
│  │  │              │      │              │         │  │
│  │  │ Routes:      │      │ Routes:      │         │  │
│  │  │ GET /barang  │      │ GET /barang  │         │  │
│  │  │ POST /barang │      │ POST /barang │         │  │
│  │  │ PUT /barang  │      │ PUT /barang  │         │  │
│  │  │ DELETE /...  │      │ DELETE /...  │         │  │
│  │  └──────────────┘      └──────────────┘         │  │
│  └──────────────┬───────────────────────────────────┘  │
│                 │                                       │
│                 ▼ (psycopg2)                            │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         DATABASE LAYER                          │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │  PostgreSQL (Port 5432)                     │ │  │
│  │  │  Database: barangdb                         │ │  │
│  │  │  User: postgres                             │ │  │
│  │  │  Schema: barang table                       │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │    OPTIONAL: LOAD BALANCER (NGINX - Port 80)    │  │
│  │    (untuk intelligent traffic distribution)      │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Container Details

| Container | Port | Peran | Framework |
|-----------|------|-------|-----------|
| **web** | 8000/5000 | Frontend application | Flask + Python |
| **api** | 8080 | Backend REST API | Flask + Python |
| **db** | 5432 | Database | PostgreSQL |
| **nginx** | 80 | Load Balancer (opsional) | Nginx |

---

## Persyaratan

### System Requirements

- **Docker**: v20.10+
- **Docker Compose**: v1.29+
- **RAM**: Minimal 2GB (untuk multiple instances)
- **Disk Space**: Minimal 500MB
- **OS**: Linux, macOS, atau Windows (dengan WSL2)

### Software yang Akan Diinstall Otomatis

- Python 3.9+
- Flask (Web Framework)
- psycopg2 (PostgreSQL adapter)
- requests (HTTP client)
- PostgreSQL 13

---

## Setup & Installation

### 1. Clone/Download Project

```bash
# Jika menggunakan Git
git clone <repository-url>
cd uts-komputasi-awan-docker

# Atau jika sudah punya folder project
cd /path/to/uts-komputasi-awan-docker
```

### 2. Verifikasi struktur folder

```bash
# Pastikan struktur folder seperti ini:
ls -la

# Output yang diharapkan:
# ├── docker-compose.yml
# ├── docker-compose-with-nginx.yml
# ├── nginx.conf
# ├── api/
# │   ├── app.py
# │   ├── Dockerfile
# │   └── requirements.txt
# ├── web/
# │   ├── app.py
# │   ├── Dockerfile
# │   ├── requirements.txt
# │   └── templates/
# │       └── index.html
# └── README.md
```

### 3. Check Docker Installation

```bash
# Verifikasi Docker
docker --version
docker ps

# Verifikasi Docker Compose
docker compose version
```

---

## Menjalankan Aplikasi

### Opsi 1: Tanpa Load Balancer (DEFAULT)

Ini adalah setup yang paling sederhana, cocok untuk development dan testing basic.

```bash
# 1. Navigate ke project directory
cd /path/to/uts-komputasi-awan-docker

# 2. Build dan start services
docker compose up -d

# 3. Check status services
docker compose ps

# Output yang diharapkan:
# NAME                COMMAND                 STATE      PORTS
# uts-komputasi...    "python app.py"         Up         0.0.0.0:8000->8000/tcp
# uts-komputasi...    "python app.py"         Up         0.0.0.0:8080->8080/tcp
# uts-komputasi...    "postgres"              Up         5432/tcp

# 4. Akses aplikasi
# - Web: http://localhost:8000 atau http://localhost:5000
# - API: http://localhost:8080
```

### Opsi 2: Dengan Load Balancer (ADVANCED)

Menggunakan Nginx untuk intelligent traffic distribution (round-robin).

```bash
# 1. Navigate ke project directory
cd /path/to/uts-komputasi-awan-docker

# 2. Gunakan docker-compose-with-nginx.yml
docker compose -f docker-compose-with-nginx.yml up -d

# 3. Check status
docker compose -f docker-compose-with-nginx.yml ps

# 4. Akses aplikasi
# - Web: http://localhost (port 80)
# - API via Load Balancer: http://localhost/api/
# - API direct: http://localhost:8080
```

### Opsi 3: Scaling dengan Multiple API Instances

```bash
# Scale API instances menjadi 3
docker compose up -d --scale api=3

# Atau jika pakai Nginx:
docker compose -f docker-compose-with-nginx.yml up -d --scale api=3

# Verifikasi
docker compose ps
# Akan menampilkan: api-1, api-2, api-3

# Check load distribution
# Buka http://localhost:8000 dan lihat requests yang masuk
```

### Stop & Cleanup

```bash
# Stop services (keep volumes)
docker compose down

# Stop dan hapus semua data (termasuk database)
docker compose down -v

# Remove images juga
docker compose down -v --rmi all
```

---

## Testing & Monitoring

### 1. Health Check Services

```bash
# Cek semua container berjalan
docker compose ps

# Lihat logs web
docker compose logs -f web

# Lihat logs api
docker compose logs -f api

# Lihat logs database
docker compose logs -f db

# Kombinasi: tail last 50 lines
docker compose logs --tail=50
```

### 2. Test API Endpoints

```bash
# GET semua barang
curl http://localhost:8080/barang

# GET barang by ID
curl http://localhost:8080/barang/1

# POST barang baru
curl -X POST http://localhost:8080/barang \
  -H "Content-Type: application/json" \
  -d '{"nama":"Laptop","harga":5000000}'

# PUT update barang
curl -X PUT http://localhost:8080/barang/1 \
  -H "Content-Type: application/json" \
  -d '{"nama":"Laptop Gaming","harga":6000000}'

# DELETE barang
curl -X DELETE http://localhost:8080/barang/1
```

### 3. Test Web Interface

```bash
# Buka di browser
http://localhost:8000
# atau
http://localhost:5000

# Test CRUD melalui web form
```

### 4. Test Load Balancing (Jika Scale > 1)

```bash
# Run dalam loop untuk melihat distribusi traffic
for i in {1..10}; do
  curl http://localhost:8080/barang
  sleep 0.5
done

# Lihat logs dari tiap API instance
docker compose logs api-1 | grep "GET /barang"
docker compose logs api-2 | grep "GET /barang"
docker compose logs api-3 | grep "GET /barang"
```

### 5. Monitor Resource Usage

```bash
# Real-time container statistics
docker stats

# CPU, Memory, Network, Block I/O per container
docker stats --no-stream
```

### 6. Database Inspection

```bash
# Connect ke PostgreSQL
docker compose exec db psql -U postgres -d barangdb

# List tables
\dt

# Show schema barang table
\d barang

# Query data
SELECT * FROM barang;

# Exit psql
\q
```

---

## Struktur Project

### Directory Layout

```
uts-komputasi-awan-docker/
│
├── 📄 README.md                          # Dokumentasi ini
├── 📄 docker-compose.yml                 # Default setup (tanpa nginx)
├── 📄 docker-compose-with-nginx.yml      # Setup dengan load balancer
├── 📄 nginx.conf                         # Konfigurasi Nginx
├── 📄 QUICK_SUMMARY.txt                  # Ringkasan hasil testing
├── 📄 LOAD_BALANCER_IMPLEMENTATION.md    # Penjelasan load balancer
├── 📄 TESTING_RESULTS.md                 # Hasil testing lengkap
├── 📄 LAPORAN_LENGKAP_SEMUA_TUGAS.md    # Laporan komprehensif
│
├── 📁 api/                               # Backend API Service
│   ├── 📄 app.py                         # Flask API application
│   ├── 📄 Dockerfile                     # Docker image untuk API
│   └── 📄 requirements.txt                # Python dependencies
│
└── 📁 web/                               # Frontend Web Service
    ├── 📄 app.py                         # Flask web application
    ├── 📄 Dockerfile                     # Docker image untuk web
    ├── 📄 requirements.txt                # Python dependencies
    └── 📁 templates/
        └── 📄 index.html                 # HTML template
```

### File Descriptions

| File | Deskripsi |
|------|-----------|
| **docker-compose.yml** | Definisi services: web, api, db |
| **docker-compose-with-nginx.yml** | Menambah Nginx sebagai load balancer |
| **nginx.conf** | Konfigurasi Nginx (upstream, round-robin) |
| **api/app.py** | REST API endpoints (CRUD operations) |
| **api/Dockerfile** | Build image untuk API container |
| **web/app.py** | Web application dengan form interaktif |
| **web/Dockerfile** | Build image untuk web container |
| **web/templates/index.html** | Frontend HTML interface |

---

## Load Balancer

### Konsep

**Load Balancer** adalah komponen yang mendistribusikan traffic secara merata ke multiple backend instances.

**Masalah tanpa Load Balancer:**
```
Web → API-1 (80% traffic) ⚠️ OVERLOADED
Web → API-2 (20% traffic) ⚪ UNDERUSED
```

**Solusi dengan Load Balancer (Nginx):**
```
Web → Nginx (Round-Robin)
      ├→ API-1 (50% traffic) ✅
      └→ API-2 (50% traffic) ✅
```

### Implementasi Nginx

File `nginx.conf` mengkonfigurasi:

```nginx
upstream api_backend {
    server api:8080;  # Auto-resolve ke semua API instances
}

server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://api_backend;
    }
}
```

### Menggunakan Load Balancer

```bash
# Start dengan Nginx
docker compose -f docker-compose-with-nginx.yml up -d --scale api=2

# Nginx akan otomatis:
# ✅ Detect API-1 dan API-2
# ✅ Distribute traffic 50-50 (round-robin)
# ✅ Handle failover (jika 1 instance down)
```

---

## Scaling

### Horizontal Scaling (Add More Instances)

```bash
# Scale API menjadi 3 instances
docker compose up -d --scale api=3

# Scale menjadi 5 instances
docker compose up -d --scale api=5

# Kembali ke 1 instance
docker compose up -d --scale api=1
```

### Monitoring Scaled Instances

```bash
# Lihat semua instances
docker compose ps

# Lihat logs semua API instances
docker compose logs api

# Lihat logs specific instance
docker compose logs api-1
docker compose logs api-2

# Monitor real-time
docker stats
```

### Best Practices

1. **Mulai dengan 1 instance** untuk testing
2. **Gunakan load balancer** sebelum scale > 1
3. **Monitor resource usage** (CPU, Memory)
4. **Set resource limits** di docker-compose.yml jika perlu
5. **Test failover** dengan stop satu instance:
   ```bash
   docker compose stop api-1
   # Verifikasi traffic masih lancar via API-2
   ```

---

## Troubleshooting

### Error: "Cannot connect to database"

```bash
# 1. Check database status
docker compose ps db

# 2. Lihat logs database
docker compose logs db

# 3. Tunggu database siap (ada delay pada startup)
docker compose logs web
# Jika ada "retrying..." berarti masih waiting

# 4. Restart services
docker compose restart
```

### Error: "Address already in use"

```bash
# Cek port yang sudah terpakai
netstat -ano | findstr :<PORT>    # Windows
lsof -i :<PORT>                   # Mac/Linux

# Opsi 1: Gunakan port berbeda di docker-compose.yml
# Ubah ports: "8000:8000" → "8001:8000"

# Opsi 2: Stop service yang menggunakan port
docker ps
docker stop <CONTAINER_ID>
```

### Error: "Web tidak bisa koneksi ke API"

```bash
# 1. Pastikan both services running
docker compose ps

# 2. Check network
docker compose exec web curl http://api:8080/barang

# 3. Check Docker network
docker network ls
docker network inspect <network_name>

# 4. Restart services
docker compose restart
```

### Container Stuck/Slow

```bash
# 1. Check resource usage
docker stats

# 2. Lihat logs error
docker compose logs

# 3. Restart problematic container
docker compose restart <service_name>

# 4. Nuclear option: clean restart
docker compose down -v
docker compose up -d
```

### Data Loss

```bash
# Docker Compose menggunakan named volumes
# Data akan persistent selama volume tidak dihapus

# Untuk backup database:
docker compose exec db pg_dump -U postgres barangdb > backup.sql

# Untuk restore:
docker compose exec db psql -U postgres barangdb < backup.sql
```

---

## Dokumentasi Lengkap

Project ini menyediakan dokumentasi detail dalam file-file berikut:

1. **README.md** (file ini)
   - Overview dan quick start

2. **QUICK_SUMMARY.txt**
   - Ringkasan hasil testing dan findings

3. **LOAD_BALANCER_IMPLEMENTATION.md**
   - Penjelasan detail tentang load balancer
   - Perbandingan architecture dengan/tanpa Nginx
   - Implementasi step-by-step

4. **TESTING_RESULTS.md**
   - Hasil test lengkap semua scenarios
   - Metrics dan performance data
   - Test cases dan expected results

5. **LAPORAN_LENGKAP_SEMUA_TUGAS.md**
   - Laporan komprehensif untuk submission
   - Analisis mendalam setiap requirement
   - Screenshots dan detailed findings

---

## Quick Command Reference

```bash
# BUILD & START
docker compose up -d                    # Start all services
docker compose up -d --scale api=3      # Start dengan 3 API instances
docker compose -f docker-compose-with-nginx.yml up -d  # Dengan Nginx

# MONITORING
docker compose ps                       # List all containers
docker compose logs -f                  # Follow logs
docker stats                            # Monitor resources
docker compose exec db psql -U postgres -d barangdb  # Database CLI

# TESTING
curl http://localhost:8080/barang       # Test API
curl http://localhost:8000              # Test Web
docker compose exec api curl http://api:8080/barang  # Internal test

# MAINTENANCE
docker compose restart                  # Restart all services
docker compose restart api-1            # Restart specific service
docker compose down                     # Stop all (keep data)
docker compose down -v                  # Stop all (remove data)
docker compose logs --tail=50 api       # Last 50 lines of logs

# SCALING
docker compose up -d --scale api=5      # Scale to 5 instances
docker compose up -d --scale api=1      # Scale down to 1
```

---

## Author & License

**Project**: UTS Komputasi Awan (Cloud Computing)  
**Course**: Cloud Computing Assignment  
**Technology Stack**: Docker, Docker Compose, Flask, PostgreSQL, Nginx  

---

## Summary

Aplikasi ini mengdemonstrasikan core concepts dari Cloud Computing:

✅ **Containerization** - Encapsulation aplikasi dalam container  
✅ **Microservices** - Separation of concerns (Web ≠ API)  
✅ **Orchestration** - Automated container management  
✅ **Scalability** - Easy horizontal scaling  
✅ **Load Balancing** - Intelligent traffic distribution  
✅ **Resilience** - Automatic failover capabilities  

---

## Perlu Bantuan?

1. **Baca dokumentasi lengkap** di folder project
2. **Check Docker logs** untuk debug informasi
3. **Lihat curl commands** untuk test API endpoints
4. **Experiment** dengan scaling dan failover scenarios

Happy learning! 🚀
