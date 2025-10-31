# Deploy Onyx with Watch Features on EC2

This guide explains how to deploy the watch features branch on EC2 using Docker Compose.

## Prerequisites
- EC2 instance with Docker and Docker Compose installed
- At least 10GB RAM and 32GB disk space
- Git installed

## Deployment Steps

### Step 1: Clone the Repository on EC2

SSH into your EC2 instance and clone your fork with the feature branch:

```bash
# Clone the repository with the feature branch
git clone -b claude/add-watch-features-011CUeo1DNM1muqrQuyAANru https://github.com/vaibhaw742-ui/onyx.git
cd onyx
```

### Step 2: Use the Modified Install Script

The install.sh script has been modified to use your feature branch. Run it:

```bash
cd deployment/docker_compose
chmod +x install.sh
./install.sh
```

**Important**: When prompted:
- Choose the deployment version (press Enter for latest)
- Select authentication method (Basic or No Auth)

### Step 3: Build Local Images

Since the watch features are in your branch (not in the official Docker images), you need to build the images locally:

```bash
# Navigate to the deployment directory
cd ~/onyx/deployment/docker_compose/onyx_data/deployment

# Build the backend image from your local code
docker compose -f docker-compose.yml build

# Or if using standalone docker-compose:
docker-compose -f docker-compose.yml build
```

This will build the Docker images from your local code, including all the watch feature changes.

### Step 4: Start the Services

After building, restart the services to use the newly built images:

```bash
# Stop existing services
docker compose -f docker-compose.yml down

# Start with the new images
docker compose -f docker-compose.yml up -d
```

### Step 5: Run Database Migration

The watch features require new database tables. Run the migration:

```bash
# Get into the api_server container
docker compose exec api_server bash

# Inside the container, run:
alembic upgrade head

# Exit the container
exit
```

### Step 6: Verify Deployment

1. Check that all containers are running:
   ```bash
   docker compose ps
   ```

2. Check logs to ensure no errors:
   ```bash
   docker compose logs -f api_server
   ```

3. Access the application:
   - Open your browser and go to `http://your-ec2-ip:3000`
   - You should see the Onyx interface with the new "Watch" section in the sidebar

## Accessing the Watch Features

Once deployed, you'll find three new menu items in the sidebar:

1. **To Watch** - Add URLs to monitor
2. **Watch Sources** - View detected content from watched URLs
3. **Add Sources** - Manually add sources

## Troubleshooting

### If containers keep restarting:
```bash
docker compose logs api_server
docker compose logs background
```

### If database migration fails:
```bash
docker compose exec api_server alembic current
docker compose exec api_server alembic upgrade head
```

### If watch features don't appear:
1. Verify the frontend was built with the changes:
   ```bash
   docker compose exec web_server ls -la /app/web/src/app/watch
   ```

2. Check API endpoints are available:
   ```bash
   curl http://localhost:8080/api/watch
   ```

### To rebuild from scratch:
```bash
# Stop and remove everything
docker compose down -v

# Rebuild
docker compose build

# Start fresh
docker compose up -d
```

## Alternative: Quick Deployment Method

If you want a faster approach without running install.sh:

```bash
# 1. Clone the repo
git clone -b claude/add-watch-features-011CUeo1DNM1muqrQuyAANru https://github.com/vaibhaw742-ui/onyx.git
cd onyx/deployment/docker_compose

# 2. Copy environment template
cp env.template .env

# 3. Edit .env file (set IMAGE_TAG, AUTH_TYPE, etc.)
nano .env

# 4. Build and start
docker compose build
docker compose up -d

# 5. Run migrations
docker compose exec api_server alembic upgrade head
```

## Notes

- The modified install.sh now downloads configuration files from your fork and feature branch
- Building locally ensures your watch feature code is included in the images
- The database migration creates the three new tables: `watch`, `watch_sources`, and `added_sources`
- Port 3000 is used by default (or the next available port if 3000 is in use)

## Support

If you encounter issues:
1. Check the logs: `docker compose logs -f`
2. Verify all containers are healthy: `docker compose ps`
3. Ensure the EC2 security group allows inbound traffic on port 3000
