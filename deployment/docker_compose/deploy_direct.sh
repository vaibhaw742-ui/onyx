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
echo "Onyx Watch Features - Direct Deployment"
echo "========================================="
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

print_info "Using: $COMPOSE_CMD"

# Step 1: Set up .env file
print_step "Step 1: Setting up environment configuration"

if [ -f ".env" ]; then
    print_info "Existing .env file found"
    read -p "Do you want to keep the existing .env file? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Creating new .env file from template..."
        cp env.template .env
        print_success "Created .env file from template"

        # Set some defaults
        print_info "Configuring .env file..."
        sed -i.bak 's/^IMAGE_TAG=.*/IMAGE_TAG=local/' .env
        sed -i.bak 's/^AUTH_TYPE=.*/AUTH_TYPE=basic/' .env
        rm -f .env.bak
        print_success "Configured .env with defaults"

        echo ""
        print_warning "IMPORTANT: Review and customize your .env file if needed:"
        echo "  - AUTH_TYPE: Set authentication method (basic, disabled, oauth, etc.)"
        echo "  - LLM settings: Configure your AI model preferences"
        echo "  - Other customizations as needed"
        echo ""
        read -p "Press Enter to continue with current settings..."
        echo ""
    else
        print_success "Keeping existing .env file"
    fi
else
    print_info "No .env file found. Creating from template..."

    if [ ! -f "env.template" ]; then
        print_error "env.template not found!"
        print_info "Make sure you're in the correct directory: ~/onyx/deployment/docker_compose/"
        exit 1
    fi

    cp env.template .env
    print_success "Created .env file from template"

    # Ask for authentication preference
    echo ""
    print_info "Which authentication method would you like?"
    echo "1) Basic - Username/password authentication (recommended)"
    echo "2) Disabled - No authentication (development only)"
    echo ""
    read -p "Choose (1-2) [default: 1]: " -r AUTH_CHOICE
    echo ""

    case "${AUTH_CHOICE:-1}" in
        1)
            sed -i.bak 's/^AUTH_TYPE=.*/AUTH_TYPE=basic/' .env
            print_info "Selected: Basic authentication"
            ;;
        2)
            sed -i.bak 's/^AUTH_TYPE=.*/AUTH_TYPE=disabled/' .env
            print_info "Selected: No authentication"
            ;;
        *)
            sed -i.bak 's/^AUTH_TYPE=.*/AUTH_TYPE=basic/' .env
            print_info "Invalid choice, using: Basic authentication"
            ;;
    esac

    # Set IMAGE_TAG to local since we're building
    sed -i.bak 's/^IMAGE_TAG=.*/IMAGE_TAG=local/' .env
    rm -f .env.bak

    print_success "Environment configured"
fi

# Step 2: Check system resources
print_step "Step 2: Checking system resources"

# Check Docker
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker."
    exit 1
fi
print_success "Docker is running"

# Check available disk space
DISK_AVAILABLE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$DISK_AVAILABLE" -lt 20 ]; then
    print_warning "Low disk space: ${DISK_AVAILABLE}GB available"
    print_info "Recommended: at least 20GB free"
    echo ""
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled. Please free up disk space."
        exit 1
    fi
else
    print_success "Disk space: ${DISK_AVAILABLE}GB available"
fi

# Step 3: Build Docker images
print_step "Step 3: Building Docker images from source"
print_info "This will take 5-15 minutes depending on your system..."
echo ""

$COMPOSE_CMD build

if [ $? -eq 0 ]; then
    print_success "Docker images built successfully"
else
    print_error "Failed to build Docker images"
    print_info "Check the error messages above and try again"
    exit 1
fi

# Step 4: Start services
print_step "Step 4: Starting Onyx services"

$COMPOSE_CMD up -d

if [ $? -eq 0 ]; then
    print_success "Services started successfully"
else
    print_error "Failed to start services"
    print_info "Run: $COMPOSE_CMD logs"
    exit 1
fi

# Step 5: Wait for database
print_step "Step 5: Waiting for services to initialize"
print_info "Waiting for database to be ready (20 seconds)..."

for i in {1..20}; do
    printf "\r[%-20s] %d%%" $(printf '#%.0s' $(seq 1 $i)) $((i*100/20))
    sleep 1
done
echo ""

print_success "Initial startup complete"

# Step 6: Run migrations
print_step "Step 6: Running database migrations"
print_info "Creating database tables (including watch tables)..."

MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if $COMPOSE_CMD exec -T api_server alembic upgrade head 2>/dev/null; then
        print_success "Database migrations completed successfully"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            print_warning "Migration attempt $RETRY_COUNT failed, retrying in 10 seconds..."
            sleep 10
        else
            print_error "Failed to run migrations after $MAX_RETRIES attempts"
            print_info "The database might still be initializing. Try manually later:"
            echo "  $COMPOSE_CMD exec api_server alembic upgrade head"
        fi
    fi
done

# Step 7: Check service health
print_step "Step 7: Verifying deployment"

# Check container status
print_info "Checking container status..."
RUNNING_CONTAINERS=$($COMPOSE_CMD ps -q 2>/dev/null | wc -l)
print_success "$RUNNING_CONTAINERS containers running"

# Verify watch features in backend
API_CONTAINER=$($COMPOSE_CMD ps -q api_server 2>/dev/null)
if [ -n "$API_CONTAINER" ]; then
    if docker exec $API_CONTAINER test -f /app/onyx/server/features/watch/api.py 2>/dev/null; then
        print_success "Watch API backend files present"
    else
        print_warning "Watch API files not found in container"
    fi
fi

# Verify watch features in frontend
WEB_CONTAINER=$($COMPOSE_CMD ps -q web_server 2>/dev/null)
if [ -n "$WEB_CONTAINER" ]; then
    if docker exec $WEB_CONTAINER test -d /app/web/src/app/watch 2>/dev/null; then
        print_success "Watch frontend files present"
    else
        print_warning "Watch frontend files not found in container"
    fi
fi

# Get the port
HOST_PORT=$(grep -E "^HOST_PORT=" .env 2>/dev/null | cut -d= -f2 || echo "3000")
if [ -z "$HOST_PORT" ]; then
    HOST_PORT="3000"
fi

# Try to determine actual port from docker-compose
ACTUAL_PORT=$($COMPOSE_CMD ps | grep nginx | grep -oE '0.0.0.0:[0-9]+' | cut -d: -f2 | head -1)
if [ -n "$ACTUAL_PORT" ]; then
    HOST_PORT=$ACTUAL_PORT
fi

# Wait for web service to be ready
print_info "Checking web service health..."
MAX_WAIT=60
WAIT_COUNT=0
WEB_READY=false

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$HOST_PORT" 2>/dev/null || echo "000")
    if echo "$HTTP_CODE" | grep -qE "^(200|301|302|303|307|308)$"; then
        WEB_READY=true
        break
    fi
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 2))
    printf "\r\033[KWaiting for web service... (%d/%d seconds)" "$WAIT_COUNT" "$MAX_WAIT"
done
echo ""

if [ "$WEB_READY" = true ]; then
    print_success "Web service is responding"
else
    print_warning "Web service not responding yet (may still be starting up)"
fi

# Final success message
echo ""
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}   🎉 Onyx Deployment Complete! 🎉${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get EC2 public IP if available
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")

print_info "Access Onyx at:"
if [ -n "$PUBLIC_IP" ]; then
    echo -e "   ${BOLD}http://$PUBLIC_IP:$HOST_PORT${NC}"
else
    echo -e "   ${BOLD}http://localhost:$HOST_PORT${NC}"
fi

echo ""
print_info "Watch features are available in the sidebar:"
echo "   • To Watch - Add URLs to monitor"
echo "   • Watch Sources - View detected content"
echo "   • Add Sources - Manually add sources"
echo ""

if grep -q "AUTH_TYPE=basic" .env 2>/dev/null; then
    print_info "Authentication is enabled (Basic):"
    if [ -n "$PUBLIC_IP" ]; then
        echo "   Visit http://$PUBLIC_IP:$HOST_PORT/auth/signup to create your admin account"
    else
        echo "   Visit http://localhost:$HOST_PORT/auth/signup to create your admin account"
    fi
    echo "   The first user created will have admin privileges"
    echo ""
fi

print_info "Useful commands:"
echo "   View logs:      $COMPOSE_CMD logs -f"
echo "   Stop services:  $COMPOSE_CMD down"
echo "   Restart:        $COMPOSE_CMD restart"
echo "   Check status:   $COMPOSE_CMD ps"
echo ""

print_info "If watch features don't appear:"
echo "   • Clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R)"
echo "   • Check logs: $COMPOSE_CMD logs api_server"
echo "   • Verify: $COMPOSE_CMD exec api_server curl http://localhost:8080/api/watch"
echo ""
