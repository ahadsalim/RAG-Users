#!/bin/bash

# ============================================
# Platform Manager
# System Management & Maintenance
# ============================================

set -e

DEPLOYMENT_DIR="/srv/deployment"
ENV_FILE="${DEPLOYMENT_DIR}/.env"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper Functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

print_info() {
    echo -e "${YELLOW}➜ $1${NC}"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# ============================================
# SERVICE MANAGEMENT
# ============================================

start_services() {
    print_header "Starting All Services"
    cd "$DEPLOYMENT_DIR"
    docker-compose up -d
    print_success "All services started"
    docker-compose ps
}

stop_services() {
    print_header "Stopping All Services"
    cd "$DEPLOYMENT_DIR"
    docker-compose down
    print_success "All services stopped"
}

restart_services() {
    print_header "Restarting All Services"
    cd "$DEPLOYMENT_DIR"
    docker-compose restart
    print_success "All services restarted"
    docker-compose ps
}

restart_service() {
    print_info "Available services:"
    echo "  - backend"
    echo "  - frontend"
    echo "  - postgres"
    echo "  - redis"
    echo "  - rabbitmq"
    echo "  - celery_worker"
    echo "  - celery_beat"
    echo "  - nginx_proxy_manager"
    echo ""
    read -p "Enter service name: " SERVICE_NAME
    
    cd "$DEPLOYMENT_DIR"
    docker-compose restart "$SERVICE_NAME"
    print_success "Service $SERVICE_NAME restarted"
}

status_services() {
    print_header "Services Status"
    cd "$DEPLOYMENT_DIR"
    docker-compose ps
}

# ============================================
# LOGS MANAGEMENT
# ============================================

view_logs() {
    print_info "Available services:"
    echo "  - backend"
    echo "  - frontend"
    echo "  - postgres"
    echo "  - redis"
    echo "  - rabbitmq"
    echo "  - celery_worker"
    echo "  - celery_beat"
    echo "  - nginx_proxy_manager"
    echo "  - all (all services)"
    echo ""
    read -p "Enter service name: " SERVICE_NAME
    read -p "Number of lines (default: 100): " LINES
    LINES=${LINES:-100}
    
    cd "$DEPLOYMENT_DIR"
    if [ "$SERVICE_NAME" == "all" ]; then
        docker-compose logs --tail=$LINES -f
    else
        docker-compose logs --tail=$LINES -f "$SERVICE_NAME"
    fi
}

# ============================================
# DATABASE MANAGEMENT
# ============================================

run_migrations() {
    print_header "Running Database Migrations"
    cd "$DEPLOYMENT_DIR"
    docker-compose exec backend python manage.py migrate --noinput
    print_success "Migrations completed"
}

create_superuser() {
    print_header "Create Django Superuser"
    cd "$DEPLOYMENT_DIR"
    docker-compose exec backend python manage.py createsuperuser
}

django_shell() {
    print_header "Django Shell"
    cd "$DEPLOYMENT_DIR"
    docker-compose exec backend python manage.py shell
}

database_shell() {
    print_header "PostgreSQL Shell"
    cd "$DEPLOYMENT_DIR"
    
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
    fi
    
    docker-compose exec postgres psql -U "${DB_USER:-app_user}" -d "${DB_NAME:-app_db}"
}

# ============================================
# MAINTENANCE
# ============================================

clear_cache() {
    print_header "Clearing Cache"
    cd "$DEPLOYMENT_DIR"
    
    print_info "Clearing Django cache (OTP, sessions, etc)..."
    docker-compose exec -T backend python manage.py shell << 'PYEOF'
from django.core.cache import cache
cache.clear()
print("✅ Django cache cleared successfully!")
PYEOF
    
    print_info "Flushing Redis..."
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
        if [ -n "$REDIS_PASSWORD" ]; then
            docker-compose exec redis redis-cli -a "$REDIS_PASSWORD" FLUSHALL
        else
            docker-compose exec redis redis-cli FLUSHALL
        fi
    else
        docker-compose exec redis redis-cli FLUSHALL
    fi
    
    print_success "All caches cleared (OTP rate limits reset)"
}

collect_static() {
    print_header "Collecting Static Files"
    cd "$DEPLOYMENT_DIR"
    docker-compose exec backend python manage.py collectstatic --noinput
    print_success "Static files collected"
}

update_system() {
    print_header "Updating System"
    
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run as root"
    fi
    
    print_info "Pulling latest images..."
    cd "$DEPLOYMENT_DIR"
    docker-compose pull
    
    print_info "Rebuilding services..."
    docker-compose build --no-cache
    
    print_info "Restarting services..."
    docker-compose down
    docker-compose up -d
    
    print_info "Running migrations..."
    sleep 20
    docker-compose exec backend python manage.py migrate --noinput
    
    print_info "Collecting static files..."
    docker-compose exec backend python manage.py collectstatic --noinput
    
    print_success "System updated successfully"
    docker-compose ps
}

cleanup_docker() {
    print_header "Docker Cleanup"
    
    print_info "Removing unused containers..."
    docker container prune -f
    
    print_info "Removing unused images..."
    docker image prune -a -f
    
    print_info "Removing unused volumes..."
    docker volume prune -f
    
    print_info "Removing unused networks..."
    docker network prune -f
    
    print_success "Docker cleanup completed"
}

# ============================================
# MONITORING
# ============================================

system_info() {
    print_header "System Information"
    
    echo "Disk Usage:"
    df -h | grep -E '^/dev|Filesystem'
    echo ""
    
    echo "Memory Usage:"
    free -h
    echo ""
    
    echo "Docker Disk Usage:"
    docker system df
    echo ""
    
    echo "Container Resource Usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

health_check() {
    print_header "Health Check"
    
    cd "$DEPLOYMENT_DIR"
    
    print_info "Checking services..."
    docker-compose ps
    echo ""
    
    print_info "Checking PostgreSQL..."
    docker-compose exec postgres pg_isready -U "${DB_USER:-app_user}" && print_success "PostgreSQL: OK" || print_error "PostgreSQL: FAILED"
    
    print_info "Checking Redis..."
    docker-compose exec redis redis-cli ping > /dev/null && print_success "Redis: OK" || print_error "Redis: FAILED"
    
    print_info "Checking RabbitMQ..."
    docker-compose exec rabbitmq rabbitmq-diagnostics ping > /dev/null && print_success "RabbitMQ: OK" || print_error "RabbitMQ: FAILED"
    
    print_info "Checking Backend..."
    docker-compose exec backend python manage.py check && print_success "Backend: OK" || print_error "Backend: FAILED"
}

# ============================================
# TROUBLESHOOTING
# ============================================

fix_otp_issues() {
    print_header "Fix OTP Issues"
    
    cd "$DEPLOYMENT_DIR"
    
    print_info "Cleaning database..."
    docker-compose exec backend python manage.py shell -c "
from accounts.models import User, UserSession
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute('''UPDATE accounts_user SET username = NULL WHERE username = '' OR username IS NULL''')
    print(f'Fixed usernames: {cursor.rowcount}')
    
    cursor.execute('''UPDATE accounts_user SET email = NULL WHERE email = '' OR email IS NULL''')
    print(f'Fixed emails: {cursor.rowcount}')

from django.db.models import Q
deleted = UserSession.objects.filter(Q(session_key='') | Q(session_key__isnull=True)).delete()
print(f'Deleted invalid sessions: {deleted[0]}')
"
    
    print_info "Clearing cache..."
    docker-compose exec backend python manage.py shell -c "
from django.core.cache import cache
cache.clear()
print('Cache cleared')
"
    
    print_success "OTP issues fixed"
}

fix_permissions() {
    print_header "Fix File Permissions"
    
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run as root"
    fi
    
    print_info "Fixing permissions..."
    chown -R $SUDO_USER:$SUDO_USER /srv
    chmod -R 755 /srv/deployment
    chmod 600 /srv/deployment/.env 2>/dev/null || true
    
    print_success "Permissions fixed"
}

# ============================================
# MAIN MENU
# ============================================

show_menu() {
    print_header "Platform Manager"
    echo ""
    echo "Service Management:"
    echo "  1)  Start All Services"
    echo "  2)  Stop All Services"
    echo "  3)  Restart All Services"
    echo "  4)  Restart Single Service"
    echo "  5)  View Services Status"
    echo ""
    echo "Logs:"
    echo "  6)  View Logs"
    echo ""
    echo "Database:"
    echo "  7)  Run Migrations"
    echo "  8)  Create Superuser"
    echo "  9)  Django Shell"
    echo "  10) Database Shell"
    echo ""
    echo "Maintenance:"
    echo "  11) Clear Cache"
    echo "  12) Collect Static Files"
    echo "  13) Update System"
    echo "  14) Docker Cleanup"
    echo ""
    echo "Monitoring:"
    echo "  15) System Information"
    echo "  16) Health Check"
    echo ""
    echo "Troubleshooting:"
    echo "  17) Fix OTP Issues"
    echo "  18) Fix Permissions"
    echo ""
    echo "  19) Exit"
    echo ""
}

# Main execution
if [ $# -eq 0 ]; then
    # Interactive mode
    while true; do
        show_menu
        read -p "Select option: " choice
        
        case $choice in
            1) start_services ;;
            2) stop_services ;;
            3) restart_services ;;
            4) restart_service ;;
            5) status_services ;;
            6) view_logs ;;
            7) run_migrations ;;
            8) create_superuser ;;
            9) django_shell ;;
            10) database_shell ;;
            11) clear_cache ;;
            12) collect_static ;;
            13) update_system ;;
            14) cleanup_docker ;;
            15) system_info ;;
            16) health_check ;;
            17) fix_otp_issues ;;
            18) fix_permissions ;;
            19)
                echo "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option"
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
else
    # Command line mode
    case "$1" in
        start) start_services ;;
        stop) stop_services ;;
        restart) restart_services ;;
        status) status_services ;;
        logs) view_logs ;;
        migrate) run_migrations ;;
        shell) django_shell ;;
        dbshell) database_shell ;;
        cache) clear_cache ;;
        static) collect_static ;;
        update) update_system ;;
        cleanup) cleanup_docker ;;
        info) system_info ;;
        health) health_check ;;
        fix-otp) fix_otp_issues ;;
        fix-perms) fix_permissions ;;
        *)
            echo "Usage: $0 {start|stop|restart|status|logs|migrate|shell|dbshell|cache|static|update|cleanup|info|health|fix-otp|fix-perms}"
            exit 1
            ;;
    esac
fi
