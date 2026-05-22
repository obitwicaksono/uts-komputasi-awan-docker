# Load Balancer Implementation Guide

## Current Architecture (WITHOUT Load Balancer)

```
┌─────────────────────────────────────────────────────────┐
│                FRONTEND NETWORK                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌──────────────┐          Docker DNS Service         │
│   │  Web App     │          Resolves "api" to:         │
│   │ :8000/5000   │          └─ [172.21.0.3, 172.21.0.2]│
│   └──────┬───────┘                                      │
│          │                                              │
│          │ requests.get("http://api:8080/barang")      │
│          │                                              │
│          ▼                                              │
│   ┌─────────────────────────────────────────────────┐  │
│   │  PROBLEM: Sticky Routing (First connection)    │  │
│   │  • Connect to 172.21.0.3 (API-1)               │  │
│   │  • Cache connection                            │  │
│   │  • Reuse for all subsequent requests           │  │
│   └──────────────┬─────────────────────────────────┘  │
│                  │                                      │
│                  ▼                                      │
│   ┌──────────────────────────┐  ┌──────────────────┐  │
│   │   API-1: 172.21.0.3      │  │  API-2: 172.21.0.2│ │
│   │   RECEIVING 80% TRAFFIC  │  │  IDLE/UNDERUSED   │  │
│   │   🔴 OVERLOADED          │  │  ⚪ WASTED        │  │
│   └──────────────┬───────────┘  └──────────────────┘  │
│                  │                                      │
└──────────────────┼──────────────────────────────────────┘
                   │
    BACKEND NETWORK│ Connection Pooling
┌──────────────────┼──────────────────────────────────────┐
│                  ▼                                       │
│   ┌──────────────────────────────────────────────────┐ │
│   │        PostgreSQL Database                       │ │
│   │        (Shared between API-1 and API-2)          │ │
│   │                                                  │ │
│   │   ✓ Data consistent                             │ │
│   │   ✓ Both instances can read/write               │ │
│   └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

ISSUES:
❌ Uneven distribution (80% vs 20%)
❌ No failover (if API-1 down → all requests fail)
❌ Can't scale effectively
```

---

## Improved Architecture (WITH Nginx Load Balancer)

```
┌──────────────────────────────────────────────────────────┐
│                 FRONTEND NETWORK                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   ┌──────────────────┐                                  │
│   │    Web App       │                                  │
│   │  :8000/5000      │                                  │
│   └────────┬─────────┘                                  │
│            │                                            │
│            │ API_URL = http://nginx:80                 │
│            ▼                                            │
│   ┌──────────────────────────────────────────────────┐ │
│   │    NGINX LOAD BALANCER                          │ │
│   │    Port: 8080 → 80 (internal)                   │ │
│   │                                                  │ │
│   │    Upstream Configuration:                      │ │
│   │    upstream api_backend {                       │ │
│   │        server api:8080;  # All instances        │ │
│   │    }                                            │ │
│   │                                                  │ │
│   │    ✓ Round-robin distribution                  │ │
│   │    ✓ Connection pooling to all upstreams       │ │
│   │    ✓ Automatic failover                        │ │
│   │    ✓ Health check support                      │ │
│   └──────────────────────────────────────────────────┘ │
│            │                                            │
│       ┌────┴─────┬─────────┐                            │
│       │           │         │                            │
│       ▼           ▼         ▼                            │
│   ┌────────┐ ┌────────┐ ┌────────┐                     │
│   │API-1   │ │API-2   │ │API-3   │                     │
│   │:8080   │ │:8080   │ │:8080   │                     │
│   │50 req/s│ │50 req/s│ │50 req/s│                     │
│   │🟢 OK   │ │🟢 OK   │ │🟢 OK   │                     │
│   └────┬───┘ └────┬───┘ └────┬───┘                     │
│        │          │          │                          │
└────────┼──────────┼──────────┼──────────────────────────┘
         │          │          │
BACKEND │          │          │ Database Connection Pool
┌───────┼──────────┼──────────┼──────────────────────────┐
│       │          │          │                          │
│       └──────────┼──────────┘                          │
│                  ▼                                      │
│   ┌─────────────────────────────────────────────────┐ │
│   │     PostgreSQL Database (Shared)                │ │
│   │                                                 │ │
│   │   ✓ Single source of truth                     │ │
│   │   ✓ Consistent data across all instances      │ │
│   │   ✓ Transaction support                       │ │
│   │   ✓ ACID compliance                           │ │
│   └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

BENEFITS:
✅ Balanced distribution (50-50-50 for 3 instances)
✅ Automatic failover (if API-1 down → route to API-2,3)
✅ Scales linearly (add more instances = more capacity)
✅ Better resource utilization
```

---

## Step-by-Step Implementation

### Step 1: Create nginx.conf

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    '[upstream: $upstream_addr]';

    access_log /var/log/nginx/access.log main;
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Upstream backend configuration
    upstream api_backend {
        # Server name, Docker will resolve to all API instances
        server api:8080;
        
        # Load balancing method
        # Default: round_robin
        # Alternative: least_conn, ip_hash, etc.
        
        # Keep connections alive
        keepalive 32;
    }

    server {
        listen 80;
        server_name _;

        # Proxy requests to API
        location / {
            proxy_pass http://api_backend;
            
            # Set headers for upstream
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Connection settings
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            
            # Timeouts
            proxy_connect_timeout 5s;
            proxy_send_timeout 10s;
            proxy_read_timeout 10s;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "Nginx LB OK\n";
            add_header Content-Type text/plain;
        }
    }
}
```

### Step 2: Update docker-compose.yml

```yaml
version: "3.9"

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: pass123
      POSTGRES_DB: barangdb
    volumes:
      - db-data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  # NGINX Load Balancer - NEW SERVICE
  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"  # External port 8080 mapped to nginx port 80
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
    networks:
      - backend
      - frontend
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  # API Instances - NOT directly exposed
  api:
    build: ./api
    environment:
      DB_HOST: db
      DB_NAME: barangdb
      DB_USER: postgres
      DB_PASSWORD: pass123
    depends_on:
      db:
        condition: service_healthy
    networks:
      - backend
      - frontend
    # NOTE: Port 8080 not exposed, only accessible via nginx

  # Web Frontend - Updated API_URL
  web:
    build: ./web
    ports:
      - "8000:5000"
    environment:
      API_URL: http://nginx:80  # CHANGED from http://api:8080
    depends_on:
      nginx:
        condition: service_healthy
    networks:
      - frontend

networks:
  backend:
    driver: bridge
  frontend:
    driver: bridge

volumes:
  db-data:
```

### Step 3: Deploy

```bash
# Stop current setup
docker compose down

# Start with load balancer
docker compose up -d --scale api=2

# Verify
docker compose ps

# Check Nginx is healthy
curl http://localhost:8080/health

# Test web interface
curl http://localhost:8000/
```

### Step 4: Testing

```bash
# Monitor API-1 requests
docker logs -f api-1 2>&1 | grep "HTTP/1.1"

# Monitor API-2 requests
docker logs -f api-2 2>&1 | grep "HTTP/1.1"

# Make requests
for i in {1..10}; do
  curl -s http://localhost:8000/ > /dev/null
  echo "Request $i sent"
  sleep 1
done

# Expected: Roughly equal distribution
# API-1: ~5 requests
# API-2: ~5 requests
```

---

## Testing Scenarios

### Scenario 1: Load Distribution
```bash
# Make 100 requests
for i in {1..100}; do
  curl -s http://localhost:8000/barang > /dev/null
done

# Check logs
docker logs api-1 | grep -c "GET /barang"  # Should be ~50
docker logs api-2 | grep -c "GET /barang"  # Should be ~50
```

### Scenario 2: Failover
```bash
# Kill one instance
docker stop api-1

# Make requests - should still work!
curl http://localhost:8000/

# Verify routed to api-2
docker logs api-2 | tail -1

# Restart api-1
docker start api-1

# Now both instances available again
```

### Scenario 3: Data Consistency
```bash
# Add data
curl -X POST http://localhost:8080/barang \
  -H "Content-Type: application/json" \
  -d '{"nama":"Test","harga":5000}'

# Read from any instance (through LB)
curl http://localhost:8080/barang

# Data should be visible - proves DB sharing
```

---

## Session State Management with Load Balancer

### Current (Recommended) - Stateless API

```python
# app.py
@app.route("/barang", methods=["GET"])
def list_barang():
    # No in-memory caching
    # Direct DB query
    conn = get_db_connection()
    rows = cur.execute("SELECT * FROM barang").fetchall()
    return jsonify(rows)

# Any instance can handle any request
# No synchronization needed
# Perfect for load balancer + horizontal scaling
```

### Optional - Sticky Sessions (if needed)

```nginx
# In nginx.conf, if you need to stick sessions:
upstream api_backend {
    hash $cookie_sessionid consistent;
    server api:8080;
}
# This ensures same user always goes to same instance
# Trade-off: Can't distribute as evenly
```

### Optional - Redis Caching

```yaml
services:
  redis:
    image: redis:alpine
    networks:
      - backend

  api:
    environment:
      REDIS_URL: redis://redis:6379
```

```python
import redis

cache = redis.Redis(host='redis', port=6379)

@app.route("/barang")
def list_barang():
    cached = cache.get('barang_list')
    if cached:
        return json.loads(cached)
    
    conn = get_db_connection()
    rows = cur.execute("SELECT * FROM barang").fetchall()
    
    cache.setex('barang_list', 300, json.dumps(rows))
    return jsonify(rows)
```

---

## Monitoring & Metrics

### Nginx Metrics
```bash
# Check Nginx status page
location /nginx_status {
    stub_status on;
    access_log off;
    allow all;
}

# Access via:
curl http://localhost:8080/nginx_status
```

### Log Analysis
```bash
# Monitor real-time distribution
docker logs -f nginx 2>&1 | grep "upstream:"

# Count requests per instance
docker logs api-1 | grep -c "GET"
docker logs api-2 | grep -c "GET"
docker logs api-3 | grep -c "GET"
```

---

## Performance Comparison

### Without Load Balancer
```
100 requests/second to 2 instances:
├─ API-1: 80 req/s (overload) 🔴
├─ API-2: 20 req/s (underutilized) 🟡
└─ Effective capacity: ~80 req/s
```

### With Nginx Load Balancer
```
100 requests/second to 2 instances:
├─ API-1: 50 req/s (balanced) 🟢
├─ API-2: 50 req/s (balanced) 🟢
└─ Effective capacity: ~100 req/s
```

---

## Scaling to 3+ Instances

```bash
# Simply scale up
docker compose up -d --scale api=5

# Nginx automatically includes all new instances
# No configuration change needed!

# Verify all instances receiving traffic
docker logs api-1 | wc -l
docker logs api-2 | wc -l
docker logs api-3 | wc -l
docker logs api-4 | wc -l
docker logs api-5 | wc -l
```

---

## Troubleshooting

### Issue: Nginx can't resolve 'api'
```
Solution: Ensure api service is on same network
└─ Both api and nginx should be on "backend" or "frontend" network
```

### Issue: Requests go only to one instance
```
Solution: Verify Nginx upstream configuration
└─ Check that server api:8080 is defined
└─ Docker will resolve to all instances automatically
```

### Issue: Health checks failing
```
Solution: Ensure API responds to GET /
└─ Or configure correct health check endpoint
└─ docker logs nginx to check errors
```

### Issue: Connection refused to api:8080
```
Solution: API might not be on same network
└─ Check docker-compose.yml network configuration
└─ Both services need matching network entry
```

---

## Conclusion

With Nginx load balancer:
- ✅ Traffic distributed evenly
- ✅ Automatic failover support
- ✅ Linear scaling
- ✅ Better resource utilization
- ✅ Production-ready setup

No changes needed to application code - just configuration!

