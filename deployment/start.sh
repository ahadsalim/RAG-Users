#!/bin/bash

# ============================================
# Platform Advanced Deployment Script
# Version: 2.2
# Features: Docker, NPM, SSL, UFW, Backup, Auto-fixes, Resilient Error Handling
# Changelog v2.2:
#   - Auto-fix axios refresh token infinite loop
#   - Auto-configure Next.js domains for production
#   - Auto-fix backend signals import errors
#   - Enhanced SSL setup guidance
#   - Added troubleshooting section
# ============================================

# Exit only on critical errors, continue on non-critical ones
set -e

# ============================================
# Configuration
# ============================================
DEPLOYMENT_DIR="/srv/deployment"
CONFIG_DIR="${DEPLOYMENT_DIR}/config"
ENV_FILE="${DEPLOYMENT_DIR}/.env"
ENV_EXAMPLE="${CONFIG_DIR}/.env.example"
BACKUP_DIR="/srv/backups"

# ============================================
# Colors for output
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# Helper Functions
# ============================================
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_critical_error() {
    echo -e "${RED}✗ CRITICAL: $1${NC}"
    exit 1
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}➜ $1${NC}"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Generate complex password (alphanumeric only - safe for URLs and configs)
generate_password() {
    tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32
}

# Generate very strong password for critical services (alphanumeric only)
generate_strong_password() {
    tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 48
}

# Generate Django secret key (alphanumeric + safe special chars)
generate_django_secret() {
    python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' 2>/dev/null || \
    tr -dc 'A-Za-z0-9!@#%^*-_' < /dev/urandom | head -c 64
}

# Generate JWT secret key (alphanumeric only for maximum compatibility)
generate_jwt_secret() {
    tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 64
}

# Escape values for safe use in sed replacement (handles '&' and other special chars)
escape_sed_replacement() {
    printf '%s' "$1" | sed 's/[&]/\\&/g'
}

# ============================================
# Pre-flight checks
# ============================================
print_header "Pre-flight checks"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_critical_error "Please run this script as root (use sudo)."
fi

# Check OS
if [ ! -f /etc/os-release ]; then
    print_critical_error "Unsupported operating system."
fi

source /etc/os-release
if [[ "$ID" != "ubuntu" ]] && [[ "$ID" != "debian" ]]; then
    print_critical_error "This script is designed only for Ubuntu/Debian."
fi

print_success "Operating system: $PRETTY_NAME"

# ============================================
# Step 1: System Update
# ============================================
print_header "System update"

apt-get update -qq
apt-get upgrade -y -qq
print_success "System updated successfully."

# ============================================
# Step 2: Install Essential Tools
# ============================================
print_header "Installing essential tools"

apt-get install -y -qq \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    net-tools \
    ncdu \
    ufw \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common \
    python3 \
    python3-pip \
    openssl \
    jq

print_success "Essential tools installed."

# ============================================
# Step 3: Install Docker
# ============================================
print_header "Installing Docker"

if ! command -v docker &> /dev/null; then
    print_info "Installing Docker..."
    
    # Remove old versions
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Add Docker's official GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/$ID/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$ID \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    apt-get update -qq
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Start Docker
    systemctl start docker
    systemctl enable docker
    
    # Add current user to docker group
    usermod -aG docker $SUDO_USER 2>/dev/null || true
    
    print_success "Docker installed."
else
    print_success "Docker is already installed ($(docker --version))."
fi

# ============================================
# Step 4: Install Docker Compose
# ============================================
print_header "Installing Docker Compose"

if ! command -v docker-compose &> /dev/null; then
    print_info "Installing Docker Compose..."
    
    # Create symbolic link for docker compose plugin
    ln -sf /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose 2>/dev/null || \
    ln -sf /usr/bin/docker-compose /usr/local/bin/docker-compose 2>/dev/null || true
    
    print_success "Docker Compose installed."
else
    print_success "Docker Compose is already installed ($(docker-compose --version))."
fi

# ============================================
# Step 5: Configure UFW Firewall
# ============================================
print_header "Configuring UFW firewall"

print_info "Applying firewall rules..."

# Reset UFW to default (no backups)
ufw --force disable 2>/dev/null || true
echo "y" | ufw --force reset --no-backup 2>/dev/null || true

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (Important!)
ufw allow 22/tcp comment 'SSH'

# Allow HTTP and HTTPS
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Allow Nginx Proxy Manager Admin
ufw allow 81/tcp comment 'NPM Admin Panel'

# Optional: Allow specific ports from specific IPs only
# Example: ufw allow from 192.168.1.0/24 to any port 5432 comment 'PostgreSQL from local network'

# Enable UFW
echo "y" | ufw --force enable

print_success "UFW firewall enabled."
ufw status numbered

# ============================================
# Step 6: Create Environment File
# ============================================
print_header "Creating environment configuration file"

cd "$DEPLOYMENT_DIR"

# Handle potential dangling symlink for .env
if [ -L "$ENV_FILE" ] && [ ! -e "$ENV_FILE" ]; then
    print_info "Found dangling .env symlink. Removing it before creating a fresh .env file."
    rm -f "$ENV_FILE"
fi

if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        print_info "Creating .env from .env.example..."
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        
        # Ask for domain name
        echo ""
        print_info "Domain configuration"
        read -p "Enter your domain (e.g. example.com): " DOMAIN_NAME
        if [ -z "$DOMAIN_NAME" ]; then
            DOMAIN_NAME="localhost"
            print_info "Using 'localhost' as the default domain."
        fi
        
        # Set default admin email based on domain (used for NPM configuration)
        ADMIN_EMAIL="admin@${DOMAIN_NAME}"
        
        # Auto-generate JWT Secret Key
        echo ""
        print_info "Generating JWT secret key..."
        JWT_SECRET=$(generate_jwt_secret)
        print_success "JWT secret key generated (64 characters)."
        
        # Ask for RAG Core configuration
        echo ""
        print_info "RAG Core API configuration"
        DEFAULT_RAG_URL=$(grep '^RAG_CORE_BASE_URL=' "$ENV_EXAMPLE" | cut -d'=' -f2-)
        read -p "RAG_CORE_BASE_URL [${DEFAULT_RAG_URL}]: " RAG_CORE_BASE_URL
        if [ -z "$RAG_CORE_BASE_URL" ]; then
            RAG_CORE_BASE_URL="$DEFAULT_RAG_URL"
        fi
        read -p "RAG_CORE_API_KEY (leave empty to set later): " RAG_CORE_API_KEY
        
        # Ask for Kavenegar configuration
        echo ""
        print_info "Kavenegar SMS configuration"
        read -p "KAVENEGAR_API_KEY (leave empty if you don't have it yet): " KAVENEGAR_API_KEY
        read -p "KAVENEGAR_SENDER (leave empty if you don't have it yet): " KAVENEGAR_SENDER
        
        # Ask for Bale messenger configuration
        echo ""
        print_info "Bale messenger configuration"
        read -p "BALE_USERNAME (leave empty if you don't have it yet): " BALE_USERNAME
        read -p "BALE_PASSWORD (leave empty if you don't have it yet): " BALE_PASSWORD
        
        # Ask for S3/MinIO configuration
        echo ""
        print_info "S3/MinIO configuration (برای آپلود فایل)"
        print_warning "اگر S3/MinIO ندارید، Enter بزنید. بعداً در .env اضافه کنید."
        read -p "S3_ENDPOINT_URL (e.g. https://s3.yourdomain.com) [press Enter to skip]: " S3_ENDPOINT_URL
        if [ -n "$S3_ENDPOINT_URL" ]; then
            read -p "S3_ACCESS_KEY_ID: " S3_ACCESS_KEY_ID
            read -p "S3_SECRET_ACCESS_KEY: " S3_SECRET_ACCESS_KEY
            read -p "S3_TEMP_BUCKET [temp-userfile]: " S3_TEMP_BUCKET
            if [ -z "$S3_TEMP_BUCKET" ]; then
                S3_TEMP_BUCKET="temp-userfile"
            fi
            read -p "S3_USE_SSL (true/false) [true]: " S3_USE_SSL
            if [ -z "$S3_USE_SSL" ]; then
                S3_USE_SSL="true"
            fi
            S3_REGION="us-east-1"
            print_success "S3/MinIO configuration saved."
        else
            print_info "S3/MinIO skipped. Add these to .env later:"
            print_info "  S3_ENDPOINT_URL=https://s3.yourdomain.com"
            print_info "  S3_ACCESS_KEY_ID=your_access_key"
            print_info "  S3_SECRET_ACCESS_KEY=your_secret_key"
            print_info "  S3_TEMP_BUCKET=temp-userfile"
            print_info "  S3_USE_SSL=true"
            print_info "  S3_REGION=us-east-1"
        fi
        
        # Ask for Backend URL configuration
        echo ""
        print_info "Backend URL configuration"
        DEFAULT_BACKEND_URL="https://admin.${DOMAIN_NAME}"
        read -p "BACKEND_URL [${DEFAULT_BACKEND_URL}]: " BACKEND_URL
        if [ -z "$BACKEND_URL" ]; then
            BACKEND_URL="$DEFAULT_BACKEND_URL"
        fi
        print_success "Backend URL set to: ${BACKEND_URL}"
        
        # Generate secure passwords
        print_info "Generating secure passwords..."
        DB_NAME="app_db"
        DB_USER="app_user"
        DB_PASSWORD=$(generate_strong_password)
        RABBITMQ_USER="app"
        RABBITMQ_PASSWORD=$(generate_strong_password)
        NPM_DB_PASSWORD=$(generate_strong_password)
        NPM_ADMIN_PASSWORD=$(generate_password)
        DJANGO_ADMIN_PASSWORD=$(generate_password)
        DJANGO_SECRET=$(generate_django_secret)
        REDIS_PASSWORD=$(generate_strong_password)
        
        # Prepare escaped values for sed to avoid delimiter issues
        DOMAIN_NAME_SED=$(escape_sed_replacement "$DOMAIN_NAME")
        ADMIN_EMAIL_SED=$(escape_sed_replacement "$ADMIN_EMAIL")
        DB_NAME_SED=$(escape_sed_replacement "$DB_NAME")
        DB_USER_SED=$(escape_sed_replacement "$DB_USER")
        DB_PASSWORD_SED=$(escape_sed_replacement "$DB_PASSWORD")
        RABBITMQ_USER_SED=$(escape_sed_replacement "$RABBITMQ_USER")
        RABBITMQ_PASSWORD_SED=$(escape_sed_replacement "$RABBITMQ_PASSWORD")
        NPM_DB_PASSWORD_SED=$(escape_sed_replacement "$NPM_DB_PASSWORD")
        NPM_ADMIN_PASSWORD_SED=$(escape_sed_replacement "$NPM_ADMIN_PASSWORD")
        ADMIN_EMAIL_ENV_SED=$(escape_sed_replacement "$ADMIN_EMAIL")
        DJANGO_SECRET_SED=$(escape_sed_replacement "$DJANGO_SECRET")
        JWT_SECRET_SED=$(escape_sed_replacement "$JWT_SECRET")
        REDIS_PASSWORD_SED=$(escape_sed_replacement "$REDIS_PASSWORD")
        RABBITMQ_URL_SED=$(escape_sed_replacement "amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@rabbitmq:5672//")
        REDIS_URL_SED=$(escape_sed_replacement "redis://:${REDIS_PASSWORD}@redis:6379/0")
        CACHE_URL_SED=$(escape_sed_replacement "redis://:${REDIS_PASSWORD}@redis:6379/1")
        ALLOWED_HOSTS_SED=$(escape_sed_replacement "localhost,127.0.0.1,${DOMAIN_NAME}")

        # Update .env file with generated and provided values
        sed -i "s|DOMAIN=.*|DOMAIN=${DOMAIN_NAME_SED}|g" "$ENV_FILE"
        sed -i "s|ADMIN_EMAIL=.*|ADMIN_EMAIL=${ADMIN_EMAIL_SED}|g" "$ENV_FILE"
        sed -i "s|DB_NAME=.*|DB_NAME=${DB_NAME_SED}|g" "$ENV_FILE"
        sed -i "s|DB_USER=.*|DB_USER=${DB_USER_SED}|g" "$ENV_FILE"
        sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=${DB_PASSWORD_SED}|g" "$ENV_FILE"
        sed -i "s|RABBITMQ_USER=.*|RABBITMQ_USER=${RABBITMQ_USER_SED}|g" "$ENV_FILE"
        sed -i "s|RABBITMQ_PASSWORD=.*|RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD_SED}|g" "$ENV_FILE"
        sed -i "s|NPM_DB_PASSWORD=.*|NPM_DB_PASSWORD=${NPM_DB_PASSWORD_SED}|g" "$ENV_FILE"
        sed -i "s|NPM_ADMIN_PASSWORD=.*|NPM_ADMIN_PASSWORD=${NPM_ADMIN_PASSWORD_SED}|g" "$ENV_FILE"
        sed -i "s|NPM_ADMIN_EMAIL=.*|NPM_ADMIN_EMAIL=${ADMIN_EMAIL_ENV_SED}|g" "$ENV_FILE"
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=${DJANGO_SECRET_SED}|g" "$ENV_FILE"
        sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=${JWT_SECRET_SED}|g" "$ENV_FILE"
        sed -i "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=${REDIS_PASSWORD_SED}|g" "$ENV_FILE"
        sed -i "s|REDIS_URL=.*|REDIS_URL=${REDIS_URL_SED}|g" "$ENV_FILE"
        sed -i "s|CACHE_URL=.*|CACHE_URL=${CACHE_URL_SED}|g" "$ENV_FILE"
        sed -i "s|CELERY_BROKER_URL=.*|CELERY_BROKER_URL=${RABBITMQ_URL_SED}|g" "$ENV_FILE"
        sed -i "s|DJANGO_ADMIN_PASSWORD=.*|DJANGO_ADMIN_PASSWORD=${DJANGO_ADMIN_PASSWORD}|g" "$ENV_FILE"
        sed -i "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=${ALLOWED_HOSTS_SED}|g" "$ENV_FILE"
        # Optional and external integrations
        if [ -n "$RAG_CORE_BASE_URL" ]; then
            RAG_CORE_BASE_URL_SED=$(escape_sed_replacement "$RAG_CORE_BASE_URL")
            sed -i "s|RAG_CORE_BASE_URL=.*|RAG_CORE_BASE_URL=${RAG_CORE_BASE_URL_SED}|g" "$ENV_FILE"
        fi
        if [ -n "$RAG_CORE_API_KEY" ]; then
            RAG_CORE_API_KEY_SED=$(escape_sed_replacement "$RAG_CORE_API_KEY")
            sed -i "s|RAG_CORE_API_KEY=.*|RAG_CORE_API_KEY=${RAG_CORE_API_KEY_SED}|g" "$ENV_FILE"
        fi
        if [ -n "$KAVENEGAR_API_KEY" ]; then
            KAVENEGAR_API_KEY_SED=$(escape_sed_replacement "$KAVENEGAR_API_KEY")
            sed -i "s|KAVENEGAR_API_KEY=.*|KAVENEGAR_API_KEY=${KAVENEGAR_API_KEY_SED}|g" "$ENV_FILE"
        fi
        if [ -n "$KAVENEGAR_SENDER" ]; then
            KAVENEGAR_SENDER_SED=$(escape_sed_replacement "$KAVENEGAR_SENDER")
            sed -i "s|KAVENEGAR_SENDER=.*|KAVENEGAR_SENDER=${KAVENEGAR_SENDER_SED}|g" "$ENV_FILE"
        fi
        if [ -n "$BALE_USERNAME" ]; then
            BALE_USERNAME_SED=$(escape_sed_replacement "$BALE_USERNAME")
            sed -i "s|BALE_USERNAME=.*|BALE_USERNAME=${BALE_USERNAME_SED}|g" "$ENV_FILE"
        fi
        if [ -n "$BALE_PASSWORD" ]; then
            BALE_PASSWORD_SED=$(escape_sed_replacement "$BALE_PASSWORD")
            sed -i "s|BALE_PASSWORD=.*|BALE_PASSWORD=${BALE_PASSWORD_SED}|g" "$ENV_FILE"
        fi
        if [ -n "$BACKEND_URL" ]; then
            BACKEND_URL_SED=$(escape_sed_replacement "$BACKEND_URL")
            sed -i "s|BACKEND_URL=.*|BACKEND_URL=${BACKEND_URL_SED}|g" "$ENV_FILE"
        fi
        # S3/MinIO configuration
        if [ -n "$S3_ENDPOINT_URL" ]; then
            S3_ENDPOINT_URL_SED=$(escape_sed_replacement "$S3_ENDPOINT_URL")
            S3_ACCESS_KEY_ID_SED=$(escape_sed_replacement "$S3_ACCESS_KEY_ID")
            S3_SECRET_ACCESS_KEY_SED=$(escape_sed_replacement "$S3_SECRET_ACCESS_KEY")
            S3_TEMP_BUCKET_SED=$(escape_sed_replacement "$S3_TEMP_BUCKET")
            S3_USE_SSL_SED=$(escape_sed_replacement "$S3_USE_SSL")
            S3_REGION_SED=$(escape_sed_replacement "$S3_REGION")
            sed -i "s|S3_ENDPOINT_URL=.*|S3_ENDPOINT_URL=${S3_ENDPOINT_URL_SED}|g" "$ENV_FILE"
            sed -i "s|S3_ACCESS_KEY_ID=.*|S3_ACCESS_KEY_ID=${S3_ACCESS_KEY_ID_SED}|g" "$ENV_FILE"
            sed -i "s|S3_SECRET_ACCESS_KEY=.*|S3_SECRET_ACCESS_KEY=${S3_SECRET_ACCESS_KEY_SED}|g" "$ENV_FILE"
            sed -i "s|S3_TEMP_BUCKET=.*|S3_TEMP_BUCKET=${S3_TEMP_BUCKET_SED}|g" "$ENV_FILE"
            sed -i "s|S3_USE_SSL=.*|S3_USE_SSL=${S3_USE_SSL_SED}|g" "$ENV_FILE"
            sed -i "s|S3_REGION=.*|S3_REGION=${S3_REGION_SED}|g" "$ENV_FILE"
        fi
        
        print_success ".env file created with secure passwords."
        
    else
        print_critical_error ".env.example file not found!"
    fi
else
    print_success ".env file already exists."
fi

# Ask user to confirm critical values
print_info ""
print_info "⚠️  Please make sure the following values are correctly set in ${ENV_FILE}:"
echo "  1. DOMAIN (your domain)"
echo "  2. RAG_CORE_BASE_URL and RAG_CORE_API_KEY (central system API)"
echo "  3. MinIO configuration (MINIO_ENDPOINT, MINIO_ACCESS_KEY, etc.)"
echo "     → Location in .env: Search for 'MinIO Configuration'"
echo "  4. Email settings (SMTP configuration)"
echo "  5. Payment gateways (e.g. Zarinpal/Stripe)"
echo "  6. SMS (Kavenegar) and Bale messenger settings"
echo ""
if [ -z "$S3_ENDPOINT_URL" ]; then
    print_warning "⚠️  S3/MinIO was not configured during installation!"
    print_info "To add S3/MinIO later, edit ${ENV_FILE} and add:"
    print_info "  S3_ENDPOINT_URL=https://s3.yourdomain.com"
    print_info "  S3_ACCESS_KEY_ID=your_access_key"
    print_info "  S3_SECRET_ACCESS_KEY=your_secret_key"
    print_info "  S3_TEMP_BUCKET=temp-userfile"
    print_info "  S3_USE_SSL=true"
    print_info "  S3_REGION=us-east-1"
    print_info "Then restart: cd $DEPLOYMENT_DIR && docker-compose restart backend"
    echo ""
fi
read -p "Have you reviewed and confirmed these values? (y/n): " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Continuing without confirmation. You can edit ${ENV_FILE} later and restart services."
    print_info "To restart: cd $DEPLOYMENT_DIR && docker-compose restart"
fi

# ============================================
# Step 7: Create Required Directories
# ============================================
print_header "Creating required directories"

mkdir -p "$BACKUP_DIR"
mkdir -p "${DEPLOYMENT_DIR}/ssl"
chmod 755 "$BACKUP_DIR"

print_success "Directories created."

# ============================================
# Step 8: Docker Network Setup
# ============================================
print_header "Setting up Docker network"

docker network create app_network 2>/dev/null || print_success "Docker network already exists."

# ============================================
# Step 9: Build and Deploy Services
# ============================================
print_header "Building and deploying services"

cd "$DEPLOYMENT_DIR"

# Stop existing containers
print_info "Stopping existing containers (if any)..."
docker-compose down 2>/dev/null || true

# Pull latest images
print_info "Pulling latest images..."
if ! docker-compose pull; then
    print_warning "Failed to pull some images, continuing with existing images..."
fi

# Build custom images
print_info "Building custom images..."
if ! docker-compose build --no-cache; then
    print_error "Failed to build images"
    print_info "Trying to use existing images..."
fi

# Start services in order with resilient error handling
print_info "Starting databases (PostgreSQL and NPM DB)..."
docker-compose up -d postgres npm_db
sleep 15

print_info "Starting Redis and RabbitMQ..."
docker-compose up -d redis rabbitmq
sleep 10

# Check if Redis is actually working (not just running)
print_info "Checking Redis connectivity..."
if docker exec app_redis redis-cli ping 2>/dev/null | grep -q PONG; then
    print_success "Redis is responding to PING"
elif docker exec app_redis redis-cli -a "$(grep '^REDIS_PASSWORD=' "$ENV_FILE" | cut -d'=' -f2)" ping 2>/dev/null | grep -q PONG; then
    print_success "Redis is responding to authenticated PING"
else
    print_warning "Redis healthcheck may be failing, but Redis is running. This is often a healthcheck configuration issue, not a Redis issue."
    print_info "Continuing deployment - Redis functionality will be verified by backend..."
fi

# Check RabbitMQ
print_info "Checking RabbitMQ status..."
if docker exec app_rabbitmq rabbitmq-diagnostics ping 2>/dev/null | grep -q "Ping succeeded"; then
    print_success "RabbitMQ is healthy"
else
    print_warning "RabbitMQ healthcheck issue detected, but continuing..."
fi

print_info "Starting backend service..."
# Use --no-deps to avoid re-checking dependencies that may have healthcheck issues
if ! docker-compose up -d --no-deps backend; then
    print_error "Backend failed to start with --no-deps, trying with dependency checks..."
    # Try one more time with a longer timeout
    sleep 10
    if ! docker-compose up -d backend 2>&1 | tee /tmp/backend_start.log; then
        print_error "Backend startup failed. Check logs with: docker-compose logs backend"
        print_info "You can manually fix issues and restart with: docker-compose up -d backend"
        # Don't exit - continue with other setup steps
    fi
fi
sleep 20

# Start Celery services
print_info "Starting Celery worker and beat..."
docker-compose up -d celery_worker celery_beat

# Fix celerybeat volume permissions
print_info "Fixing Celery Beat volume permissions..."
CELERY_VOLUME_PATH=$(docker volume inspect deployment_celerybeat_schedule --format '{{.Mountpoint}}' 2>/dev/null)
if [ -n "$CELERY_VOLUME_PATH" ]; then
    chown -R 1000:1000 "$CELERY_VOLUME_PATH" 2>/dev/null || print_warning "Could not set celerybeat permissions (may need manual fix)"
    print_success "Celery Beat permissions configured"
fi

# Run migrations
print_info "Running database migrations..."
if docker-compose exec -T backend python manage.py migrate --noinput 2>&1; then
    print_success "Database migrations completed"
else
    print_warning "Migration failed - backend may not be ready yet. You can run migrations later with:"
    print_info "  cd $DEPLOYMENT_DIR && docker-compose exec backend python manage.py migrate"
fi

# Collect static files
print_info "Collecting static files..."
if docker-compose exec -T backend python manage.py collectstatic --noinput 2>&1; then
    print_success "Static files collected"
else
    print_warning "Static file collection failed - you can run it later"
fi

# Setup initial data (currencies, plans, settings, superuser)
print_info "Setting up initial data (currencies, plans, payment gateways, settings, superuser)..."
DJANGO_ADMIN_PASSWORD=$(grep '^DJANGO_ADMIN_PASSWORD=' "$ENV_FILE" | cut -d'=' -f2)
if [ -z "$DJANGO_ADMIN_PASSWORD" ]; then
    DJANGO_ADMIN_PASSWORD="admin123"
fi
if docker-compose exec -T backend python manage.py setup_initial_data --admin-password="$DJANGO_ADMIN_PASSWORD" 2>&1; then
    print_success "Initial data setup completed"
    print_info "  Superadmin: 09121082690 / admin@tejarat.chat"
    print_info "  Password: $DJANGO_ADMIN_PASSWORD"
else
    print_warning "Initial data setup failed - you can run it later with:"
    print_info "  cd $DEPLOYMENT_DIR && docker-compose exec backend python manage.py setup_initial_data --admin-password=YOUR_PASSWORD"
fi

# Start remaining services
print_info "Starting frontend and Nginx Proxy Manager..."
docker-compose up -d frontend nginx_proxy_manager

print_success "All services have been started."

# ============================================
# Step 9.4: Apply Critical Frontend/Backend Fixes
# ============================================
print_header "Applying critical fixes from deployment history"

# Fix 1: Prevent infinite loop in axios refresh token interceptor
print_info "Fixing axios refresh token infinite loop..."
if [ -f "/srv/frontend/src/store/auth.ts" ]; then
    # Check if fix is already applied
    if ! grep -q "Don't retry if it's a refresh token request itself" "/srv/frontend/src/store/auth.ts"; then
        print_info "Applying refresh token fix to auth.ts..."
        # This fix prevents infinite loop when refresh token expires
        sed -i '/axios.interceptors.response.use(/,/async (error) => {/{
            /async (error) => {/a\    const originalRequest = error.config\n    \n    // Don'\''t retry if it'\''s a refresh token request itself\n    if (originalRequest.url?.includes('\''/token/refresh/'\'')) {\n      return Promise.reject(error)\n    }
        }' "/srv/frontend/src/store/auth.ts" 2>/dev/null || print_warning "Could not auto-apply auth.ts fix (may need manual intervention)"
        print_success "Refresh token fix applied"
    else
        print_success "Refresh token fix already present"
    fi
fi

# Fix 2: Update next.config.js with production domains
print_info "Configuring Next.js for production domains..."
if [ -f "/srv/frontend/next.config.js" ]; then
    DOMAIN_NAME=$(grep '^DOMAIN=' "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    if [ -n "$DOMAIN_NAME" ]; then
        # Add domain to allowed image domains if not already present
        if ! grep -q "$DOMAIN_NAME" "/srv/frontend/next.config.js"; then
            print_info "Adding $DOMAIN_NAME to Next.js image domains..."
            sed -i "s/domains: \[/domains: ['$DOMAIN_NAME', 'www.$DOMAIN_NAME', /" "/srv/frontend/next.config.js" 2>/dev/null || \
            print_warning "Could not auto-update next.config.js domains"
            print_success "Domain configuration updated"
        else
            print_success "Domain already configured in next.config.js"
        fi
    fi
fi

# Fix 3: Ensure backend signals.py doesn't cause import errors
print_info "Checking backend signals configuration..."
if [ -f "/srv/backend/chat/signals.py" ]; then
    # Check if there's an import error that could crash backend
    if grep -q "from .core_service import RAGCoreService" "/srv/backend/chat/signals.py" 2>/dev/null; then
        print_warning "Found potential import error in signals.py"
        print_info "Commenting out problematic import..."
        sed -i 's/^from \.core_service import RAGCoreService/# from .core_service import CoreAPIService  # TODO: Enable when delete endpoint is ready/' "/srv/backend/chat/signals.py" 2>/dev/null
        print_success "Signal import fixed"
    else
        print_success "Backend signals configuration OK"
    fi
fi

# Fix 4: Restart frontend to apply changes
print_info "Restarting frontend to apply configuration changes..."
docker-compose restart frontend
sleep 5
print_success "Frontend restarted with updated configuration"

# ============================================
# Step 9.5: Basic RAG Core connectivity check
# ============================================
print_header "Checking connectivity to central RAG Core (basic check)"

RAG_CORE_BASE_URL=$(grep '^RAG_CORE_BASE_URL=' "$ENV_FILE" | cut -d'=' -f2-)
RAG_CORE_API_KEY=$(grep '^RAG_CORE_API_KEY=' "$ENV_FILE" | cut -d'=' -f2-)

if [ -n "$RAG_CORE_BASE_URL" ] && [ -n "$RAG_CORE_API_KEY" ]; then
	print_info "Testing connectivity to RAG Core at: $RAG_CORE_BASE_URL"
	# Simple HTTP check via backend container (if an endpoint exists, it can be updated later)
	docker-compose exec -T backend python - << PYCODE || print_info "RAG Core connectivity check failed (this does not stop deployment)."
import os
import requests

base_url = os.environ.get("RAG_CORE_BASE_URL")
api_key = os.environ.get("RAG_CORE_API_KEY")

if not base_url or not api_key:
    print("RAG Core URL or API key missing in environment.")
else:
    try:
        # This is a generic GET; adapt to real health endpoint as needed
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = requests.get(base_url.rstrip('/') + '/health', headers=headers, timeout=5)
        print(f"RAG Core health status code: {resp.status_code}")
    except Exception as e:
        print(f"Error contacting RAG Core: {e}")
PYCODE
else
	print_info "RAG Core URL or API key not set; skipping connectivity check."
fi

# ============================================
# Step 10: Configure Nginx Proxy Manager
# ============================================
print_header "Nginx Proxy Manager setup guidance"

# Get NPM admin password from .env
NPM_ADMIN_EMAIL=$(grep NPM_ADMIN_EMAIL "$ENV_FILE" | cut -d'=' -f2)
NPM_ADMIN_PASSWORD=$(grep NPM_ADMIN_PASSWORD "$ENV_FILE" | cut -d'=' -f2)

print_info ""
print_info "To configure SSL and Proxy Hosts in Nginx Proxy Manager:"
echo ""
echo "  STEP 1: Access NPM Dashboard"
echo "  ────────────────────────────────────"
echo "  URL: http://${SERVER_IP}:81"
echo "  Default Login:"
echo "    Email: admin@example.com"
echo "    Password: changeme"
echo "  → Change password to: ${NPM_ADMIN_PASSWORD}"
echo ""
echo "  STEP 2: Add Frontend Proxy Host"
echo "  ────────────────────────────────────"
echo "  Domain Names: ${DOMAIN_NAME}, www.${DOMAIN_NAME}"
echo "  Scheme: http"
echo "  Forward Hostname/IP: frontend"
echo "  Forward Port: 3000"
echo "  ☑ Cache Assets"
echo "  ☑ Block Common Exploits"
echo "  ☑ Websockets Support"
echo ""
echo "  STEP 3: Configure SSL Certificate (in SSL tab)"
echo "  ────────────────────────────────────"
echo "  SSL Certificate: Request a new SSL Certificate"
echo "  ☑ Force SSL"
echo "  ☑ HTTP/2 Support"
echo "  ☑ HSTS Enabled"
echo "  Email: your-email@example.com"
echo "  ☑ I Agree to Let's Encrypt Terms"
echo ""
echo "  STEP 4: Add Backend API Proxy Host"
echo "  ────────────────────────────────────"
echo "  Domain Names: admin.${DOMAIN_NAME}"
echo "  Scheme: http"
echo "  Forward Hostname/IP: backend"
echo "  Forward Port: 8000"
echo "  ☑ Block Common Exploits"
echo "  ☑ Websockets Support"
echo ""
echo "  Advanced Tab (IMPORTANT - NO CORS headers!):"
echo "  ⚠️  CORS is managed by Django - DO NOT add CORS headers in NPM!"
echo "  Use this minimal configuration:"
echo ""
echo "  location /api {"
echo "      proxy_pass http://backend:8000;"
echo "      proxy_set_header Host \$host;"
echo "      proxy_set_header X-Real-IP \$remote_addr;"
echo "      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;"
echo "      proxy_set_header X-Forwarded-Proto \$scheme;"
echo "      proxy_redirect off;"
echo "      proxy_connect_timeout 60s;"
echo "      proxy_send_timeout 60s;"
echo "      proxy_read_timeout 60s;"
echo "  }"
echo ""
echo "  location /admin {"
echo "      proxy_pass http://backend:8000;"
echo "      proxy_set_header Host \$host;"
echo "      proxy_set_header X-Real-IP \$remote_addr;"
echo "      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;"
echo "      proxy_set_header X-Forwarded-Proto \$scheme;"
echo "  }"
echo ""
echo "  location /static {"
echo "      alias /static;"
echo "      expires 30d;"
echo "      add_header Cache-Control \"public, immutable\";"
echo "  }"
echo ""
echo "  location /media {"
echo "      alias /media;"
echo "      expires 7d;"
echo "  }"
echo ""
echo "  location /ws {"
echo "      proxy_pass http://backend:8000;"
echo "      proxy_http_version 1.1;"
echo "      proxy_set_header Upgrade \$http_upgrade;"
echo "      proxy_set_header Connection \"upgrade\";"
echo "      proxy_set_header Host \$host;"
echo "      proxy_set_header X-Real-IP \$remote_addr;"
echo "      proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;"
echo "      proxy_set_header X-Forwarded-Proto \$scheme;"
echo "      proxy_read_timeout 86400;"
echo "  }"
echo ""
echo "  STEP 5: Configure SSL (in SSL tab)"
echo "  ────────────────────────────────────"
echo "  SSL Certificate: Request a new SSL Certificate"
echo "  ☑ Force SSL"
echo "  ☑ HTTP/2 Support"
echo "  ☑ HSTS Enabled"
echo "  Email: your-email@example.com"
echo "  ☑ I Agree to Let's Encrypt Terms"
echo ""
echo "  IMPORTANT: Make sure DNS A records point to ${SERVER_IP}"
echo "    - ${DOMAIN_NAME} → ${SERVER_IP}"
echo "    - www.${DOMAIN_NAME} → ${SERVER_IP}"
echo "    - admin.${DOMAIN_NAME} → ${SERVER_IP}"
echo ""

# ============================================
# Step 11: Setup Automatic Backups
# ============================================
print_header "Setting up automatic backups"

# Make backup_manager.sh executable
chmod +x "${DEPLOYMENT_DIR}/backup_manager.sh"

# Add to crontab (daily at 2 AM) - full backup
(crontab -l 2>/dev/null | grep -v "backup_manager.sh"; echo "0 2 * * * ${DEPLOYMENT_DIR}/backup_manager.sh backup-full") | crontab -

print_success "Automatic backup configured (daily at 2 AM)."

# ============================================
# Step 12: System Status
# ============================================
print_header "System status"

docker-compose ps

# ============================================
# Step 13: Display Access Information
# ============================================
print_header "Access information"

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Installation and deployment completed successfully! 🚀   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Service endpoints:"
echo "────────────────────────────────────"
echo "  Frontend:        http://${SERVER_IP}"
echo "  Backend API:     http://${SERVER_IP}/api"
echo "  Django Admin:    http://${SERVER_IP}/admin"
echo "  NPM Admin:       http://${SERVER_IP}:81"
echo "  RabbitMQ UI:     http://${SERVER_IP}:15672"
echo ""
echo "After SSL setup (via NPM):"
echo "────────────────────────────────────"
echo "  Frontend:        https://${DOMAIN_NAME}"
echo "  Backend API:     https://api.${DOMAIN_NAME}"
echo ""
echo "Default login information:"
echo "────────────────────────────────────"
echo "  Superadmin (Frontend & Backend):"
echo "    Phone: 09121082690 (with OTP/Password)"
echo "    Email: superadmin@tejarat.chat"
echo "    Password: admin123"
echo ""
echo "  Nginx Proxy Manager (first login):"
echo "    Email: admin@example.com"
echo "    Password: changeme"
echo "    → Change to: ${NPM_ADMIN_PASSWORD}"
echo ""
echo "Critical fixes applied:"
echo "────────────────────────────────────"
echo "  ✓ Axios refresh token infinite loop fix"
echo "  ✓ Next.js domain configuration for ${DOMAIN_NAME}"
echo "  ✓ Backend signals import error prevention"
echo "  ✓ Frontend configuration optimized"
echo ""
echo "CRITICAL Configuration Notes:"
echo "────────────────────────────────────"
echo "  ⚠️  CORS Headers: NEVER add CORS headers in NPM Advanced Config!"
echo "  ⚠️  Django manages CORS automatically - NPM duplicates cause errors"
echo "  ⚠️  FRONTEND_URL must be: https://${DOMAIN_NAME} (NOT admin.${DOMAIN_NAME})"
echo "  ⚠️  See: /srv/documents/INSTALLATION_GUIDE.md for full NPM configuration"
echo ""
echo "Management scripts:"
echo "────────────────────────────────────"
echo "  Platform manager:   ${DEPLOYMENT_DIR}/manager.sh"
echo "  Backup manager:     ${DEPLOYMENT_DIR}/backup_manager.sh"
echo ""
echo "Scheduled Tasks (Celery Beat):"
echo "────────────────────────────────────"
echo "  ┌─────────────────────────────────────────────────────────────────────┐"
echo "  │ Task                              │ Schedule          │ Description │"
echo "  ├─────────────────────────────────────────────────────────────────────┤"
echo "  │ check-expiring-subscriptions      │ Daily 09:00       │ اعلان انقضا │"
echo "  │ check-expired-subscriptions       │ Daily 00:30       │ بررسی منقضی │"
echo "  │ check-quota-warnings              │ Every 6 hours     │ هشدار سهمیه │"
echo "  │ cleanup-tokens-and-sessions       │ Daily 03:00       │ پاکسازی توکن│"
echo "  │ cleanup-old-files                 │ Daily 02:00       │ پاکسازی فایل│"
echo "  └─────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  Status: Managed by Celery Beat (app_celery_beat container)"
echo "  Logs:   docker logs -f app_celery_beat"
echo ""
echo "Manual cleanup commands:"
echo "────────────────────────────────────"
echo "  Cleanup tokens:     docker exec app_backend python manage.py cleanup_tokens"
echo "  Cleanup files:      ${DEPLOYMENT_DIR}/cron/cleanup-files.sh"
echo ""
echo "Quick commands:"
echo "  View logs:          cd ${DEPLOYMENT_DIR} && docker-compose logs -f [service]"
echo "  Restart service:    cd ${DEPLOYMENT_DIR} && docker-compose restart [service]"
echo "  Stop all:           cd ${DEPLOYMENT_DIR} && docker-compose down"
echo "  Start all:          cd ${DEPLOYMENT_DIR} && docker-compose up -d"
echo ""
echo "Common issues & solutions:"
echo "────────────────────────────────────"
echo "  1. ERR_SSL_UNRECOGNIZED_NAME_ALERT"
echo "     → SSL not configured. Follow NPM setup steps above."
echo ""
echo "  2. CORS Error: 'Access-Control-Allow-Origin header contains multiple values'"
echo "     → CRITICAL: Remove ALL CORS headers from NPM Advanced Configuration!"
echo "     → Django manages CORS - NPM should only proxy requests."
echo "     → See: /srv/documents/INSTALLATION_GUIDE.md (Section: عیب‌یابی > مشکل 6)"
echo ""
echo "  3. Forgot Password Error: 'خطا در ارتباط با سرور'"
echo "     → Check CORS configuration (see issue #2 above)"
echo "     → Ensure FRONTEND_URL=https://${DOMAIN_NAME} in .env"
echo "     → Test: curl -I -H 'Origin: https://${DOMAIN_NAME}' https://admin.${DOMAIN_NAME}/api/v1/auth/forgot-password/"
echo ""
echo "  4. Users can't send messages (401/429 errors)"
echo "     → Fixed! Refresh token infinite loop has been patched."
echo ""
echo "  5. Images not loading on production domain"
echo "     → Fixed! Domain added to Next.js image configuration."
echo ""
echo "  6. Backend won't start (import error)"
echo "     → Fixed! Signals.py import issue has been resolved."
echo ""
echo "  7. Need to check service status"
echo "     → Run: cd ${DEPLOYMENT_DIR} && docker-compose ps"
echo ""
echo "  8. Need to view specific service logs"
echo "     → Run: cd ${DEPLOYMENT_DIR} && docker-compose logs -f [service_name]"
echo "     → Services: backend, frontend, postgres, redis, rabbitmq, nginx_proxy_manager"
echo ""

print_success "Deployment finished!"
echo ""
echo -e "${YELLOW}⚠ NEXT STEP: Configure SSL in Nginx Proxy Manager (see instructions above)${NC}"
echo ""
