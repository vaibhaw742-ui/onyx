# Quick Fix: Watch Features Not Showing

## The Problem

You ran `install.sh` which pulled **pre-built Docker images** from Docker Hub. These images don't contain your watch features because they're from the official Onyx repository, not your feature branch.

## The Solution

You need to **rebuild the Docker images** from your feature branch source code.

## Option 1: Automated Rebuild Script (Recommended)

If you're on your EC2 instance in the directory where you ran install.sh:

```bash
# 1. First, clone the feature branch repository
cd ~
git clone -b claude/add-watch-features-011CUeo1DNM1muqrQuyAANru https://github.com/vaibhaw742-ui/onyx.git

# 2. Go to your deployment directory (where install.sh created onyx_data)
cd ~/onyx/deployment/docker_compose/onyx_data/deployment

# 3. Download and run the rebuild script
curl -fsSL https://raw.githubusercontent.com/vaibhaw742-ui/onyx/claude/add-watch-features-011CUeo1DNM1muqrQuyAANru/deployment/docker_compose/rebuild_with_watch_features.sh -o rebuild.sh
chmod +x rebuild.sh
./rebuild.sh
```

## Option 2: Manual Steps

If you prefer to do it manually:

```bash
# 1. Clone the feature branch if you haven't already
cd ~
git clone -b claude/add-watch-features-011CUeo1DNM1muqrQuyAANru https://github.com/vaibhaw742-ui/onyx.git

# 2. Navigate to your deployment directory
cd ~/onyx/deployment/docker_compose/onyx_data/deployment

# 3. Update docker-compose.yml to point to your local code
# Edit the file and change the build context paths:
#   From: context: ../../backend
#   To:   context: ~/onyx/backend

# 4. Stop current containers
docker compose down
# OR if using standalone:
docker-compose down

# 5. Build new images from your feature branch code
docker compose build
# OR:
docker-compose build

# 6. Start containers with the new images
docker compose up -d
# OR:
docker-compose up -d

# 7. Wait for services to start (about 15-20 seconds)
sleep 20

# 8. Run database migrations to create watch tables
docker compose exec api_server alembic upgrade head
# OR:
docker-compose exec api_server alembic upgrade head
```

## Option 3: Start Fresh

If the above doesn't work, start completely fresh:

```bash
# 1. Go to where you originally ran install.sh
cd ~/deployment/docker_compose  # Or wherever you ran it

# 2. Stop and remove everything
./install.sh --delete-data
# Type 'DELETE' when prompted

# 3. Clone the feature branch
cd ~
git clone -b claude/add-watch-features-011CUeo1DNM1muqrQuyAANru https://github.com/vaibhaw742-ui/onyx.git
cd onyx/deployment/docker_compose

# 4. Run install.sh to set up the structure
./install.sh

# 5. Navigate to the deployment directory
cd onyx_data/deployment

# 6. Update docker-compose.yml build paths to point to ~/onyx/backend and ~/onyx/web

# 7. Build from local source
docker compose build

# 8. Restart
docker compose down
docker compose up -d

# 9. Run migrations
sleep 20
docker compose exec api_server alembic upgrade head
```

## Verification

After rebuilding, verify the watch features are present:

### 1. Check the Web Interface
- Open `http://your-ec2-ip:3000` in your browser
- Look at the left sidebar
- You should see a **"Watch"** section with:
  - To Watch
  - Watch Sources
  - Add Sources

### 2. Check Backend API
```bash
# From your deployment directory
docker compose exec api_server curl -s http://localhost:8080/api/watch
```

If successful, you should see a JSON response (not a 404 error).

### 3. Check Container Logs
```bash
docker compose logs -f api_server | grep -i watch
```

You should see logs indicating the watch endpoints are registered.

### 4. Verify Frontend Files
```bash
docker compose exec web_server ls -la /app/web/src/app/watch
```

You should see the watch directories: `to-watch`, `watch-sources`, `added-sources`.

## Troubleshooting

### Still don't see watch features?

1. **Clear browser cache**: Hard refresh with Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

2. **Check if images were built locally**:
   ```bash
   docker images | grep onyx
   ```
   Look for images without the `onyxdotapp/` prefix - these are locally built.

3. **Verify the source code has watch features**:
   ```bash
   cd ~/onyx
   git branch
   ls -la backend/onyx/server/features/
   ```
   You should see a `watch` directory.

4. **Check database tables exist**:
   ```bash
   docker compose exec relational_db psql -U postgres -c "\dt" | grep watch
   ```
   You should see `watch`, `watch_sources`, and `added_sources` tables.

5. **View detailed logs**:
   ```bash
   docker compose logs api_server --tail=100
   docker compose logs web_server --tail=100
   ```

### Database migration fails?

```bash
# Check current migration status
docker compose exec api_server alembic current

# Try upgrading again
docker compose exec api_server alembic upgrade head

# If it says "already at head", the migration is complete
```

### Containers keep restarting?

```bash
# Check what's wrong
docker compose ps
docker compose logs api_server --tail=50
docker compose logs background --tail=50

# Common issues:
# - Database not ready: wait 30 seconds and check again
# - Port conflicts: check .env file for PORT settings
```

## Getting Help

If you're still having issues, gather this information:

```bash
# Container status
docker compose ps

# Recent logs
docker compose logs api_server --tail=100 > api_logs.txt
docker compose logs web_server --tail=100 > web_logs.txt

# Docker images
docker images | grep onyx

# Git status
cd ~/onyx && git status && git branch
```

Share these outputs for debugging assistance.
