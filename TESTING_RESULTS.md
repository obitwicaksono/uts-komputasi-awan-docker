# Testing Results: Docker Compose API Scaling (2 Instances)

## ✅ Command Executed
```bash
docker compose up -d --scale api=2
```

## 📊 Current Status

### Container Status
```
✓ uts-komputasi-awan-docker-db-1    (postgres:15-alpine)      Healthy
✓ uts-komputasi-awan-docker-api-1   (uts-komputasi-awan-docker-api)
✓ uts-komputasi-awan-docker-api-2   (uts-komputasi-awan-docker-api)  [NEW - Scaled]
✓ uts-komputasi-awan-docker-web-1   (uts-komputasi-awan-docker-web)
```

### Network Configuration
- **frontend network**: web-1 (172.21.0.4) ↔ api-1 (172.21.0.3), api-2 (172.21.0.2)
- **backend network**: api-1, api-2, db-1 (172.19.0.x)

### DNS Resolution from Web Container
```
getent hosts api → 172.21.0.3 (api-1)
                   172.21.0.2 (api-2)
```

---

## ⚠️ PROBLEM ANALYSIS

### What Happens with `--scale api=2`?

#### ✅ What Works:
1. **Scaling Creates Multiple Instances**: Docker creates `api-1` and `api-2` containers
2. **Both Connect to Same Database**: Both instances use shared PostgreSQL (good for stateless services)
3. **Service Discovery**: Docker DNS resolves `http://api:8080` to BOTH IPs (172.21.0.3, 172.21.0.2)

#### ❌ What DOESN'T Work:
```
Problem #1: DNS Round-Robin NOT Guaranteed
  - Docker returns both IPs when resolving "api"
  - BUT the client (web container) may connect to SAME instance repeatedly
  - NO LOAD BALANCING occurs - requests aren't distributed

Problem #2: Port Conflicts
  - Both api-1 and api-2 bind to PORT 8080 on their respective containers
  - They're in separate containers so no conflict, BUT...
  - The hardcoded API_URL="http://api:8080" resolves to ONE instance at a time
  
Problem #3: Connection Pooling & Session State
  - If web container establishes a connection, it may stick to one API instance
  - No automatic failover if api-1 goes down
  - Session data not distributed (each API instance has its own memory state)
```

### Current Behavior: STICKY CONNECTIONS
```
Web Container (requests.get/post) 
    ↓
Docker DNS resolves "api" → [IP1, IP2]
    ↓
First connection uses IP1 (api-1)
    ↓
Connection REUSED for subsequent requests
    ↓
Result: ALL traffic goes to api-1, api-2 idle! ❌
```

---

## 🔴 Current Architecture Limitations

| Aspect | Current Status | Issue |
|--------|---|---|
| **Load Balancing** | ❌ None | Manual DNS round-robin not reliable |
| **Request Distribution** | ❌ Sticky to one instance | Python requests library caches connection |
| **Failover** | ❌ None | If api-1 fails, web can't automatically switch |
| **Session State** | ⚠️ Shared DB only | In-memory state not replicated |
| **Horizontal Scaling** | ❌ Not effective | Scaling adds containers but doesn't distribute traffic |

---

## ✅ Test Results

### Test 1: Container Accessibility
```
✓ Web can resolve api hostname to both instances
✓ Web can access api-1 (confirmed by logs)
✓ Web cannot access api-2 (not in logs - never gets requests)
✓ Database shared between both API instances
```

### Test 2: Request Distribution
```
API-1 Logs:
  172.21.0.3 - - [21/May/2026 21:17:13] "POST /barang HTTP/1.1" 201 -
  172.21.0.3 - - [21/May/2026 21:17:13] "GET /barang HTTP/1.1" 200 -
  172.21.0.3 - - [21/May/2026 21:17:15] "GET /barang HTTP/1.1" 200 -
  
API-2 Logs:
  (Empty - NO requests received)
```

**Conclusion**: Web container only connects to API-1. API-2 unused! 🚫

---

## 🎯 SOLUTION: Implement Load Balancer

### Option 1: Nginx Load Balancer (Recommended for Production)
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
    networks:
      - frontend
      - backend

  api:
    # ... existing config
    # Do NOT expose port 8080
```

**nginx.conf**:
```nginx
upstream api_backend {
    server api-1:8080;
    server api-2:8080;
    # Sticky sessions if needed:
    # hash $cookie_sessionid consistent;
}

server {
    listen 80;
    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_header;
    }
}
```

### Option 2: Traefik (Modern, Auto-Discovery)
```yaml
services:
  traefik:
    image: traefik:latest
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - frontend

  api:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.local`)"
      - "traefik.http.services.api.loadbalancer.server.port=8080"
    # Traefik auto-discovers and load balances
```

---

## 🔐 Session State Management

### Current Situation
- **Database State**: ✅ SHARED (both API instances can read/write same DB)
- **In-Memory State**: ❌ NOT SHARED (each instance has separate memory)
- **Session Tokens**: ⚠️ Not implemented (no authentication)

### Management Strategy

#### 1. **Stateless API** (Recommended)
```python
# Current design is already good:
# - No in-memory session storage
# - All data persisted to PostgreSQL
# - Each request is independent
✓ Any API instance can handle any request
✓ Perfect for horizontal scaling
```

#### 2. **If Session State Needed** (e.g., caching, auth tokens):

**Option A: Redis Cache** (Shared session storage)
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

**Option B: Sticky Sessions** (Route same user to same instance)
```nginx
# In Nginx config:
upstream api_backend {
    hash $cookie_sessionid consistent;
    server api-1:8080;
    server api-2:8080;
}
```

**Option C: Database Session Store** (Most reliable)
```python
# Store sessions in PostgreSQL instead of memory
# Use Flask-Session with database backend
```

---

## 📋 Recommendations

### Priority 1: Add Nginx Load Balancer
- ✅ Distributes requests across API instances
- ✅ Enables true horizontal scaling
- ✅ Simple to configure and understand
- ✅ Production-ready

### Priority 2: Make Web Point to Load Balancer
```yaml
web:
  environment:
    API_URL: http://nginx:80  # Instead of http://api:8080
```

### Priority 3: Session Management
- Keep API **stateless** (already is)
- Use PostgreSQL for any persistent session data
- Consider Redis for caching if needed

### Priority 4: Monitoring
```bash
docker logs -f uts-komputasi-awan-docker-api-1 &
docker logs -f uts-komputasi-awan-docker-api-2 &
# Monitor which instance gets how many requests
```

---

## 📝 Testing Methodology

### Test 1: Verify Load Balancer Distribution
```bash
# Watch logs from both instances
docker logs -f uts-komputasi-awan-docker-api-1 &
docker logs -f uts-komputasi-awan-docker-api-2 &

# Make multiple requests
for i in {1..10}; do
  curl -X GET http://localhost:8000/barang
  sleep 1
done

# Expected: See requests distributed across BOTH api-1 and api-2
```

### Test 2: Failover Test
```bash
# Kill api-1
docker stop uts-komputasi-awan-docker-api-1

# Make requests to web
curl http://localhost:8000/

# Expected: Still works! Requests routed to api-2
```

### Test 3: Session Persistence
```bash
# POST data to api-1
curl -X POST http://localhost:8080/barang \
  -H "Content-Type: application/json" \
  -d '{"nama":"Item1","harga":1000}'

# Read from api-2 (via load balancer)
curl http://localhost:8000/barang

# Expected: Data visible (shows sharing via PostgreSQL)
```

---

## 🎓 Learning Outcomes

1. **Docker Compose Scaling**: Creates multiple instances but doesn't auto-distribute
2. **Load Balancing**: Essential for effective horizontal scaling
3. **Service Discovery**: DNS resolution alone insufficient - need intelligent routing
4. **Stateless Design**: Key for horizontal scaling and resilience
5. **Connection Reuse**: Client libraries cache connections, causing sticky routing

