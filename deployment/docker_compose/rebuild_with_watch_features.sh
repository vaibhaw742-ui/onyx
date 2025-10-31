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
echo "Onyx Watch Features - Rebuild Script"
echo "======================================"
echo -e "${NC}"
print_info "This script will rebuild Onyx with the watch features enabled"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found in current directory"
    print_info "Please run this script from the onyx_data/deployment directory"
    exit 1
fi

# Determine compose command
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    print_error "Docker Compose not found"
    exit 1
fi

print_info "Using: $COMPOSE_CMD"

# Step 1: Check if the source code exists
print_step "Step 1: Checking for source code"

# Try to find the onyx repository
REPO_PATH=""
if [ -d "../../backend" ] && [ -d "../../web" ]; then
    REPO_PATH="../.."
    print_success "Found Onyx source code at: $REPO_PATH"
elif [ -d "../../../onyx/backend" ] && [ -d "../../../onyx/web" ]; then
    REPO_PATH="../../../onyx"
    print_success "Found Onyx source code at: $REPO_PATH"
else
    print_error "Cannot find Onyx source code!"
    echo ""
    print_info "You need to clone the Onyx repository with the watch features branch first:"
    echo ""
    echo "  cd ~"
    echo "  git clone -b claude/add-watch-features-011CUeo1DNM1muqrQuyAANru https://github.com/vaibhaw742-ui/onyx.git"
    echo ""
    print_info "Then run this script again from: ~/onyx/deployment/docker_compose/onyx_data/deployment/"
    exit 1
fi

# Verify it's the right branch
cd "$REPO_PATH"
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
print_info "Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "claude/add-watch-features-011CUeo1DNM1muqrQuyAANru" ]; then
    print_warning "Not on the watch features branch!"
    echo ""
    read -p "Do you want to switch to the watch features branch? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git fetch origin
        git checkout claude/add-watch-features-011CUeo1DNM1muqrQuyAANru
        git pull origin claude/add-watch-features-011CUeo1DNM1muqrQuyAANru
        print_success "Switched to watch features branch"
    else
        print_error "Cannot proceed without the watch features branch"
        exit 1
    fi
fi

# Return to deployment directory
cd - > /dev/null

# Step 2: Update docker-compose.yml to use local build
print_step "Step 2: Updating Docker Compose configuration"

# Backup the original docker-compose.yml
if [ ! -f "docker-compose.yml.backup" ]; then
    cp docker-compose.yml docker-compose.yml.backup
    print_success "Created backup: docker-compose.yml.backup"
fi

# Update the docker-compose.yml to use local build context
print_info "Updating build context to use local source code..."

# The docker-compose.yml should already have build contexts, we just need to make sure they point to the right place
# Update api_server build context
sed -i.tmp "s|context: .*backend|context: $REPO_PATH/backend|g" docker-compose.yml

# Update background build context (if different)
sed -i.tmp "s|context: .*backend|context: $REPO_PATH/backend|g" docker-compose.yml

# Update web_server build context if it exists
if grep -q "web_server:" docker-compose.yml; then
    sed -i.tmp "s|context: .*web|context: $REPO_PATH/web|g" docker-compose.yml
fi

rm -f docker-compose.yml.tmp
print_success "Docker Compose configuration updated"

# Step 3: Stop running containers
print_step "Step 3: Stopping running containers"
$COMPOSE_CMD -f docker-compose.yml down
print_success "Containers stopped"

# Step 4: Build new images from local source
print_step "Step 4: Building Docker images from local source"
print_info "This may take 5-10 minutes depending on your system..."
echo ""

$COMPOSE_CMD -f docker-compose.yml build

if [ $? -eq 0 ]; then
    print_success "Docker images built successfully"
else
    print_error "Failed to build Docker images"
    exit 1
fi

# Step 5: Start containers with new images
print_step "Step 5: Starting Onyx with watch features"
$COMPOSE_CMD -f docker-compose.yml up -d

if [ $? -eq 0 ]; then
    print_success "Containers started successfully"
else
    print_error "Failed to start containers"
    exit 1
fi

# Step 6: Wait for services to be ready
print_step "Step 6: Waiting for services to initialize"
print_info "Waiting 15 seconds for database to be ready..."
sleep 15

# Step 7: Run database migrations
print_step "Step 7: Running database migrations"
print_info "Creating watch tables in database..."

$COMPOSE_CMD exec -T api_server alembic upgrade head

if [ $? -eq 0 ]; then
    print_success "Database migrations completed successfully"
else
    print_error "Failed to run migrations"
    print_info "You may need to run them manually:"
    echo "  $COMPOSE_CMD exec api_server alembic upgrade head"
fi

# Step 8: Verify watch features
print_step "Step 8: Verifying watch features"

# Check if the watch API is accessible
sleep 5
print_info "Checking watch API endpoints..."

# Get the API server container
API_CONTAINER=$($COMPOSE_CMD ps -q api_server)

if [ -n "$API_CONTAINER" ]; then
    # Test if watch endpoints exist
    if docker exec -i $API_CONTAINER curl -s http://localhost:8080/api/watch > /dev/null 2>&1; then
        print_success "Watch API endpoints are accessible"
    else
        print_warning "Watch API endpoints may not be ready yet (this is normal if services are still starting)"
    fi
fi

# Check if watch files exist in the web container
WEB_CONTAINER=$($COMPOSE_CMD ps -q web_server 2>/dev/null)
if [ -n "$WEB_CONTAINER" ]; then
    if docker exec -i $WEB_CONTAINER test -d /app/web/src/app/watch 2>/dev/null; then
        print_success "Watch frontend files are present"
    else
        print_warning "Watch frontend files not found - check web container build"
    fi
fi

# Final success message
echo ""
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}   🎉 Rebuild Complete! 🎉${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
print_info "Watch features should now be available in your Onyx deployment"
echo ""
print_info "Next steps:"
echo "  1. Open your browser to http://your-ec2-ip:3000"
echo "  2. Look for the 'Watch' section in the left sidebar"
echo "  3. You should see: To Watch, Watch Sources, and Add Sources"
echo ""
print_info "If you don't see the watch features:"
echo "  • Clear your browser cache (Ctrl+Shift+R / Cmd+Shift+R)"
echo "  • Check logs: $COMPOSE_CMD logs -f api_server"
echo "  • Verify containers: $COMPOSE_CMD ps"
echo ""
print_info "To view logs:"
echo "  $COMPOSE_CMD logs -f api_server"
echo "  $COMPOSE_CMD logs -f web_server"
echo ""
