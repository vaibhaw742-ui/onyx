#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

print_step() {
    echo ""
    echo -e "${BLUE}${BOLD}=== $1 ===${NC}"
    echo ""
}

echo ""
echo -e "${BLUE}${BOLD}"
echo "Onyx Watch Features - Simple Deployment"
echo "========================================"
echo -e "${NC}"
echo ""

# Check if we're in the deployment directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found!"
    print_info "Please run this script from: ~/onyx/deployment/docker_compose/"
    exit 1
fi

print_success "Found docker-compose.yml"

# Determine compose command
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    print_error "Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

COMPOSE_VERSION=$($COMPOSE_CMD version --short 2>/dev/null || echo "unknown")
print_info "Using: $COMPOSE_CMD (version: $COMPOSE_VERSION)"

# Check Docker version
DOCKER_VERSION=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
print_info "Docker version: $DOCKER_VERSION"

# Step 1: Set up .env file
print_step "Step 1: Setting up environment configuration"

if [ -f ".env" ]; then
    print_info "Existing .env file found"
    print_success "Using existing .env file"
else
    print_info "Creating .env file from template..."

    if [ ! -f "env.template" ]; then
        print_error "env.template not found!"
        exit 1
    fi

    cp env.template .env
    print_success "Created .env file"

    # Configure defaults
    print_info "Configuring basic settings..."

    # Set IMAGE_TAG
    if grep -q "^IMAGE_TAG=" .env; then
        sed -i.bak 's/^IMAGE_TAG=.*/IMAGE_TAG=local/' .env
    else
        echo "IMAGE_TAG=local" >> .env
    fi

    # Ask for auth
    echo ""
    print_info "Authentication method:"
    echo "1) Basic - Username/password (recommended)"
    echo "2) Disabled - No authentication"
    echo ""
    read -p "Choose (1-2) [default: 1]: " -r AUTH_CHOICE
    echo ""

    case "${AUTH_CHOICE:-1}" in
        2)
            sed -i.bak 's/^AUTH_TYPE=.*/AUTH_TYPE=disabled/' .env 2>/dev/null || echo "AUTH_TYPE=disabled" >> .env
            print_info "Selected: No authentication"
            ;;
        *)
            sed -i.bak 's/^AUTH_TYPE=.*/AUTH_TYPE=basic/' .env 2>/dev/null || echo "AUTH_TYPE=basic" >> .env
            print_info "Selected: Basic authentication"
            ;;
    esac

    rm -f .env.bak
    print_success "Configuration complete"
fi

# Step 2: Build images using docker build instead of docker compose build
print_step "Step 2: Building Docker images"
print_info "This will take 10-20 minutes..."
echo ""

# Build backend image
print_info "Building backend image..."
cd ../../backend

if docker build -t onyxdotapp/onyx-backend:local . ; then
    print_success "Backend image built successfully"
else
    print_error "Failed to build backend image"
    exit 1
fi

# Build web image if web server exists in docker-compose
cd ../deployment/docker_compose

if grep -q "web_server:" docker-compose.yml; then
    print_info "Building web server image..."
    cd ../../web

    if docker build -t onyxdotapp/onyx-web-server:local . ; then
        print_success "Web server image built successfully"
    else
        print_error "Failed to build web server image"
        exit 1
    fi

    cd ../deployment/docker_compose
fi

print_success "All images built successfully"

# Step 3: Start services
print_step "Step 3: Starting Onyx services"

# Stop any existing containers
print_info "Stopping existing containers..."
$COMPOSE_CMD down 2>/dev/null || true

# Start services
print_info "Starting services..."
$COMPOSE_CMD up -d

if [ $? -eq 0 ]; then
    print_success "Services started successfully"
else
    print_error "Failed to start services"
    print_info "Check logs with: $COMPOSE_CMD logs"
    exit 1
fi

# Step 4: Wait for database
print_step "Step 4: Waiting for services to initialize"
print_info "Waiting for database (30 seconds)..."

for i in {1..30}; do
    printf "\r[%-30s] %d%%" $(printf '#%.0s' $(seq 1 $i)) $((i*100/30))
    sleep 1
done
echo ""

print_success "Services should be ready"

# Step 5: Run migrations
print_step "Step 5: Running database migrations"
print_info "Creating database tables..."

MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if $COMPOSE_CMD exec -T api_server alembic upgrade head 2>/dev/null; then
        print_success "Database migrations completed"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            print_warning "Migration attempt $RETRY_COUNT failed, retrying in 10 seconds..."
            sleep 10
        else
            print_warning "Auto-migration failed. Try manually:"
            echo "  $COMPOSE_CMD exec api_server alembic upgrade head"
        fi
    fi
done

# Step 6: Verify deployment
print_step "Step 6: Verifying deployment"

# Check containers
print_info "Checking container status..."
RUNNING=$($COMPOSE_CMD ps 2>/dev/null | grep -c "Up" || echo "0")
print_success "$RUNNING containers running"

# Show container status
$COMPOSE_CMD ps

# Get port
HOST_PORT=$(grep "HOST_PORT" .env 2>/dev/null | cut -d= -f2 | tr -d ' ' || echo "3000")
if [ -z "$HOST_PORT" ]; then
    HOST_PORT="3000"
fi

# Get EC2 public IP
PUBLIC_IP=$(curl -s --max-time 2 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")

# Final message
echo ""
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}   🎉 Deployment Complete! 🎉${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

print_info "Access Onyx at:"
if [ -n "$PUBLIC_IP" ]; then
    echo -e "   ${BOLD}http://$PUBLIC_IP:$HOST_PORT${NC}"
else
    echo -e "   ${BOLD}http://localhost:$HOST_PORT${NC}"
fi

echo ""
print_info "Watch features should appear in the sidebar:"
echo "   • To Watch"
echo "   • Watch Sources"
echo "   • Add Sources"
echo ""

if grep -q "AUTH_TYPE=basic" .env 2>/dev/null; then
    print_info "Create your admin account at:"
    if [ -n "$PUBLIC_IP" ]; then
        echo "   http://$PUBLIC_IP:$HOST_PORT/auth/signup"
    else
        echo "   http://localhost:$HOST_PORT/auth/signup"
    fi
    echo ""
fi

print_info "Useful commands:"
echo "   Logs:    $COMPOSE_CMD logs -f"
echo "   Status:  $COMPOSE_CMD ps"
echo "   Stop:    $COMPOSE_CMD down"
echo "   Restart: $COMPOSE_CMD restart"
echo ""

print_info "If watch features don't appear:"
echo "   1. Clear browser cache (Ctrl+Shift+R)"
echo "   2. Check: $COMPOSE_CMD exec api_server curl http://localhost:8080/api/watch"
echo "   3. View logs: $COMPOSE_CMD logs api_server"
echo ""
