# Deploying Onyx with Watch Features on EC2

This guide covers deploying Onyx with the watch features on your EC2 instance.

## Prerequisites

- EC2 instance with Docker and Docker Compose installed
- At least 10GB RAM and 20GB+ free disk space
- Git installed
- Port 3000 open in your security group

## Choose Your Deployment Method

Since you have the **main branch cloned with all watch features**, use **Option 1** (recommended).

---

## Option 1: Direct Deployment (Recommended) ⭐

This is the **simplest and fastest** method since you already have the code.

### On Your EC2 Instance:

```bash
# 1. Clone the repository (if not already done)
cd ~
git clone https://github.com/vaibhaw742-ui/onyx.git
cd onyx/deployment/docker_compose

# 2. Run the deployment script
chmod +x deploy_direct.sh
./deploy_direct.sh
```

**That's it!** The script will:
- ✅ Set up your `.env` file
- ✅ Check system resources
- ✅ Build Docker images from your source code (with watch features)
- ✅ Start all services
- ✅ Run database migrations
- ✅ Verify the deployment

**Time:** 10-15 minutes (depending on your system)

### After Deployment

1. Open your browser to: `http://your-ec2-ip:3000`
2. Look for the **"Watch"** section in the sidebar with:
   - 📍 To Watch
   - 🔗 Watch Sources
   - ➕ Add Sources
3. If using Basic auth, create your admin account at `/auth/signup`

---

## Option 2: Using install.sh + Rebuild

Only use this if you want the install.sh setup process.

### On Your EC2 Instance:

```bash
# 1. Clone the repository
cd ~
git clone https://github.com/vaibhaw742-ui/onyx.git

# 2. Run install.sh to set up directory structure
cd onyx/deployment/docker_compose
./install.sh

# 3. Navigate to deployment directory
cd onyx_data/deployment

# 4. Update docker-compose.yml build paths
# Change "context: ../../backend" to "context: ~/onyx/backend"
# Change "context: ../../web" to "context: ~/onyx/web"
# You can use sed or a text editor

# 5. Rebuild from local source
docker compose build

# 6. Restart services
docker compose down
docker compose up -d

# 7. Wait and run migrations
sleep 20
docker compose exec api_server alembic upgrade head
```

**Time:** 15-20 minutes

---

## Quick Comparison

| Method | Steps | Build Time | Complexity | When to Use |
|--------|-------|------------|------------|-------------|
| **Direct Deployment** | 2 commands | 10-15 min | Simple | You have the repo cloned ⭐ |
| **install.sh + Rebuild** | Multiple steps | 15-20 min | Complex | You want install.sh's checks |

---

## Verification

After deployment, verify watch features are working:

### 1. Check the Web Interface

Open `http://your-ec2-ip:3000` and look for the "Watch" section in the sidebar.

### 2. Check Backend API

```bash
cd ~/onyx/deployment/docker_compose
docker compose exec api_server curl http://localhost:8080/api/watch
```

Should return JSON (not a 404 error).

### 3. Check Database Tables

```bash
docker compose exec relational_db psql -U postgres -c "\dt" | grep watch
```

Should show: `watch`, `watch_sources`, `added_sources`

### 4. Check Container Status

```bash
docker compose ps
```

All containers should be "running" or "healthy".

---

## Troubleshooting

### Watch features don't appear in UI?

1. **Clear browser cache**: Hard refresh with `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. **Check logs**:
   ```bash
   docker compose logs api_server --tail=100
   docker compose logs web_server --tail=100
   ```
3. **Verify build**:
   ```bash
   docker compose exec api_server ls /app/onyx/server/features/watch
   docker compose exec web_server ls /app/web/src/app/watch
   ```

### Database migration fails?

```bash
# Wait 30 seconds for DB to be ready
sleep 30

# Try again
docker compose exec api_server alembic upgrade head

# Check migration status
docker compose exec api_server alembic current
```

### Containers keep restarting?

```bash
# Check which container is failing
docker compose ps

# View its logs
docker compose logs <container-name> --tail=50

# Common issues:
# - Database not ready: Wait 1 minute and check again
# - Port already in use: Check .env HOST_PORT setting
# - Out of memory: Check docker stats
```

### Port 3000 not accessible?

1. **Check EC2 Security Group**: Ensure inbound rule allows TCP port 3000
2. **Check service is running**: `docker compose ps`
3. **Check the actual port**: `docker compose ps | grep nginx`
4. **Test locally first**: `curl http://localhost:3000`

---

## Useful Commands

```bash
# View logs
docker compose logs -f api_server
docker compose logs -f web_server

# Check container status
docker compose ps

# Restart a service
docker compose restart api_server

# Stop all services
docker compose down

# Start services again
docker compose up -d

# Rebuild after code changes
docker compose build
docker compose down
docker compose up -d

# Access database
docker compose exec relational_db psql -U postgres

# Run migrations manually
docker compose exec api_server alembic upgrade head

# Check API health
docker compose exec api_server curl http://localhost:8080/api/watch
```

---

## Updating Your Deployment

When you make changes to the code:

```bash
# Pull latest changes
cd ~/onyx
git pull origin main

# Rebuild and restart
cd deployment/docker_compose
docker compose build
docker compose down
docker compose up -d

# Run any new migrations
docker compose exec api_server alembic upgrade head
```

---

## Complete Cleanup

To completely remove everything and start fresh:

```bash
cd ~/onyx/deployment/docker_compose

# Stop and remove all containers, volumes, and networks
docker compose down -v

# Remove built images (optional)
docker images | grep onyx | awk '{print $3}' | xargs docker rmi -f

# Remove the data directory if you used install.sh
rm -rf onyx_data/

# Start fresh with deploy_direct.sh
./deploy_direct.sh
```

---

## Getting Help

If you need help, gather this information:

```bash
# Container status
docker compose ps

# Logs
docker compose logs api_server --tail=100 > api_logs.txt
docker compose logs web_server --tail=100 > web_logs.txt

# Images
docker images | grep onyx

# Git info
cd ~/onyx && git branch && git log --oneline -5

# System resources
df -h
docker stats --no-stream
```

Share these outputs for faster debugging.

---

## Summary

**Recommended approach**: Use `deploy_direct.sh` for the simplest deployment. It builds everything from your local code and sets up all the watch features automatically.

**Access your app**: `http://your-ec2-ip:3000`

**Watch features**: Look for the "Watch" section in the left sidebar!
