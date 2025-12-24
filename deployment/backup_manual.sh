#!/bin/bash

# ============================================
# Manual Backup & Restore Script
# Supports: Full backup, Database-only backup
#          Full restore, Database-only restore
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; exit 1; }
print_info() { echo -e "${YELLOW}ℹ${NC} $1"; }
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Load environment variables
if [ ! -f "$ENV_FILE" ]; then
    print_error ".env file not found at $ENV_FILE"
fi

source "$ENV_FILE"

# Configuration
BACKUP_DIR="/srv/backups/manual"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# ============================================
# BACKUP FUNCTIONS
# ============================================

backup_full() {
    print_header "Full System Backup"
    
    BACKUP_NAME="full_backup_${DATE}"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
    
    print_info "Creating backup: ${BACKUP_NAME}"
    mkdir -p "$BACKUP_PATH"
    
    # 1. PostgreSQL Backup
    print_info "Backing up PostgreSQL database..."
    cd "$SCRIPT_DIR"
    
    docker exec app_postgres pg_dump \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=custom \
        --blobs \
        --compress=9 \
        > "${BACKUP_PATH}/postgres.dump" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "PostgreSQL backup completed"
    else
        print_error "PostgreSQL backup failed"
    fi
    
    # 2. Redis Backup
    print_info "Backing up Redis data..."
    
    if [ -n "$REDIS_PASSWORD" ]; then
        docker exec app_redis redis-cli -a "$REDIS_PASSWORD" BGSAVE > /dev/null 2>&1
    else
        docker exec app_redis redis-cli BGSAVE > /dev/null 2>&1
    fi
    
    sleep 5
    docker cp app_redis:/data/dump.rdb "${BACKUP_PATH}/redis.rdb" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Redis backup completed"
    fi
    
    # 3. Media Files (if not using S3)
    if [ "${USE_S3:-true}" != "true" ]; then
        print_info "Backing up media files..."
        docker run --rm \
            -v app_media_files:/data \
            -v ${BACKUP_PATH}:/backup \
            alpine \
            tar czf /backup/media_files.tar.gz -C /data . 2>/dev/null
        
        if [ $? -eq 0 ]; then
            print_success "Media files backup completed"
        fi
    else
        print_info "Skipping media files (using S3/MinIO)"
    fi
    
    # 4. Static Files
    print_info "Backing up static files..."
    docker run --rm \
        -v app_static_files:/data \
        -v ${BACKUP_PATH}:/backup \
        alpine \
        tar czf /backup/static_files.tar.gz -C /data . 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Static files backup completed"
    fi
    
    # 5. Nginx Proxy Manager Data
    print_info "Backing up Nginx Proxy Manager data..."
    docker run --rm \
        -v app_npm_data:/data \
        -v ${BACKUP_PATH}:/backup \
        alpine \
        tar czf /backup/npm_data.tar.gz -C /data . 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "NPM data backup completed"
    fi
    
    # 6. Environment file
    print_info "Backing up .env file..."
    cp "$ENV_FILE" "${BACKUP_PATH}/env" 2>/dev/null
    print_success ".env backup completed"
    
    # 7. Create final compressed archive
    print_info "Creating compressed archive..."
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        rm -rf "${BACKUP_NAME}/"
        BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
        print_success "Full backup completed!"
        echo ""
        print_info "Backup file: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
        print_info "Size: ${BACKUP_SIZE}"
        echo ""
    else
        print_error "Archive creation failed"
    fi
}

backup_database_only() {
    print_header "Database-Only Backup"
    
    BACKUP_NAME="db_backup_${DATE}"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
    
    print_info "Creating backup: ${BACKUP_NAME}"
    mkdir -p "$BACKUP_PATH"
    
    # 1. PostgreSQL Backup
    print_info "Backing up PostgreSQL database..."
    cd "$SCRIPT_DIR"
    
    docker exec app_postgres pg_dump \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=custom \
        --blobs \
        --compress=9 \
        > "${BACKUP_PATH}/postgres.dump" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "PostgreSQL backup completed"
    else
        print_error "PostgreSQL backup failed"
    fi
    
    # 2. Redis Backup
    print_info "Backing up Redis data..."
    
    if [ -n "$REDIS_PASSWORD" ]; then
        docker exec app_redis redis-cli -a "$REDIS_PASSWORD" BGSAVE > /dev/null 2>&1
    else
        docker exec app_redis redis-cli BGSAVE > /dev/null 2>&1
    fi
    
    sleep 5
    docker cp app_redis:/data/dump.rdb "${BACKUP_PATH}/redis.rdb" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Redis backup completed"
    fi
    
    # 3. Environment file
    print_info "Backing up .env file..."
    cp "$ENV_FILE" "${BACKUP_PATH}/env" 2>/dev/null
    print_success ".env backup completed"
    
    # 4. Create compressed archive
    print_info "Creating compressed archive..."
    cd "$BACKUP_DIR"
    tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        rm -rf "${BACKUP_NAME}/"
        BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
        print_success "Database backup completed!"
        echo ""
        print_info "Backup file: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
        print_info "Size: ${BACKUP_SIZE}"
        echo ""
    else
        print_error "Archive creation failed"
    fi
}

# ============================================
# RESTORE FUNCTIONS
# ============================================

restore_full() {
    print_header "Full System Restore"
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run as root (sudo)"
    fi
    
    # List available backups
    print_info "Available full backups:"
    echo ""
    ls -lh "${BACKUP_DIR}"/full_backup_*.tar.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    echo ""
    
    # Get backup file path
    read -p "Enter full path to backup file: " BACKUP_FILE
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
    fi
    
    # Confirmation
    echo ""
    print_info "⚠️  WARNING: This will replace ALL current data!"
    read -p "Type 'yes' to continue: " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        print_info "Restore cancelled"
        exit 0
    fi
    
    # Extract backup
    RESTORE_DIR="/tmp/restore_$(date +%s)"
    mkdir -p "$RESTORE_DIR"
    
    print_info "Extracting backup..."
    tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR" 2>/dev/null
    
    # Find extracted directory
    BACKUP_NAME=$(basename "$BACKUP_FILE" .tar.gz)
    RESTORE_PATH="${RESTORE_DIR}/${BACKUP_NAME}"
    
    if [ ! -d "$RESTORE_PATH" ]; then
        print_error "Invalid backup structure"
    fi
    
    # Stop services
    print_info "Stopping all services..."
    cd "$SCRIPT_DIR"
    docker-compose down
    
    # Restore PostgreSQL
    if [ -f "${RESTORE_PATH}/postgres.dump" ]; then
        print_info "Restoring PostgreSQL database..."
        docker-compose up -d postgres
        sleep 15
        
        docker exec app_postgres psql -U "${DB_USER}" postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true
        docker exec app_postgres psql -U "${DB_USER}" postgres -c "CREATE DATABASE ${DB_NAME};"
        
        docker exec -i app_postgres pg_restore \
            -U "${DB_USER}" \
            -d "${DB_NAME}" \
            --verbose \
            --clean \
            --if-exists \
            < "${RESTORE_PATH}/postgres.dump" 2>/dev/null
        
        print_success "PostgreSQL restored"
    fi
    
    # Restore Redis
    if [ -f "${RESTORE_PATH}/redis.rdb" ]; then
        print_info "Restoring Redis data..."
        docker-compose up -d redis
        sleep 5
        
        docker cp "${RESTORE_PATH}/redis.rdb" app_redis:/data/dump.rdb
        docker-compose restart redis
        sleep 5
        
        print_success "Redis restored"
    fi
    
    # Restore Media Files
    if [ -f "${RESTORE_PATH}/media_files.tar.gz" ]; then
        print_info "Restoring media files..."
        docker run --rm \
            -v app_media_files:/data \
            -v ${RESTORE_PATH}:/backup \
            alpine \
            sh -c "rm -rf /data/* && tar xzf /backup/media_files.tar.gz -C /data"
        
        print_success "Media files restored"
    fi
    
    # Restore Static Files
    if [ -f "${RESTORE_PATH}/static_files.tar.gz" ]; then
        print_info "Restoring static files..."
        docker run --rm \
            -v app_static_files:/data \
            -v ${RESTORE_PATH}:/backup \
            alpine \
            sh -c "rm -rf /data/* && tar xzf /backup/static_files.tar.gz -C /data"
        
        print_success "Static files restored"
    fi
    
    # Restore NPM Data
    if [ -f "${RESTORE_PATH}/npm_data.tar.gz" ]; then
        print_info "Restoring Nginx Proxy Manager data..."
        docker run --rm \
            -v app_npm_data:/data \
            -v ${RESTORE_PATH}:/backup \
            alpine \
            sh -c "rm -rf /data/* && tar xzf /backup/npm_data.tar.gz -C /data"
        
        print_success "NPM data restored"
    fi
    
    # Start all services
    print_info "Starting all services..."
    docker-compose up -d
    
    # Cleanup
    rm -rf "$RESTORE_DIR"
    
    print_success "Full restore completed successfully!"
    echo ""
    print_info "Please verify all services are running:"
    print_info "  cd $SCRIPT_DIR && docker-compose ps"
}

restore_database_only() {
    print_header "Database-Only Restore"
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run as root (sudo)"
    fi
    
    # List available backups
    print_info "Available database backups:"
    echo ""
    ls -lh "${BACKUP_DIR}"/db_backup_*.tar.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    echo ""
    
    # Get backup file path
    read -p "Enter full path to backup file: " BACKUP_FILE
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
    fi
    
    # Confirmation
    echo ""
    print_info "⚠️  WARNING: This will replace current database data!"
    read -p "Type 'yes' to continue: " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        print_info "Restore cancelled"
        exit 0
    fi
    
    # Extract backup
    RESTORE_DIR="/tmp/restore_$(date +%s)"
    mkdir -p "$RESTORE_DIR"
    
    print_info "Extracting backup..."
    tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR" 2>/dev/null
    
    # Find extracted directory
    BACKUP_NAME=$(basename "$BACKUP_FILE" .tar.gz)
    RESTORE_PATH="${RESTORE_DIR}/${BACKUP_NAME}"
    
    if [ ! -d "$RESTORE_PATH" ]; then
        print_error "Invalid backup structure"
    fi
    
    cd "$SCRIPT_DIR"
    
    # Restore PostgreSQL
    if [ -f "${RESTORE_PATH}/postgres.dump" ]; then
        print_info "Restoring PostgreSQL database..."
        
        # Ensure postgres is running
        docker-compose up -d postgres
        sleep 10
        
        # Drop and recreate database
        docker exec app_postgres psql -U "${DB_USER}" postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true
        docker exec app_postgres psql -U "${DB_USER}" postgres -c "CREATE DATABASE ${DB_NAME};"
        
        # Restore
        docker exec -i app_postgres pg_restore \
            -U "${DB_USER}" \
            -d "${DB_NAME}" \
            --verbose \
            --clean \
            --if-exists \
            < "${RESTORE_PATH}/postgres.dump" 2>/dev/null
        
        print_success "PostgreSQL restored"
    fi
    
    # Restore Redis
    if [ -f "${RESTORE_PATH}/redis.rdb" ]; then
        print_info "Restoring Redis data..."
        
        docker-compose up -d redis
        sleep 5
        
        docker cp "${RESTORE_PATH}/redis.rdb" app_redis:/data/dump.rdb
        docker-compose restart redis
        sleep 5
        
        print_success "Redis restored"
    fi
    
    # Restart backend services
    print_info "Restarting backend services..."
    docker-compose restart backend celery_worker celery_beat
    
    # Cleanup
    rm -rf "$RESTORE_DIR"
    
    print_success "Database restore completed successfully!"
}

# ============================================
# MAIN MENU
# ============================================

show_menu() {
    print_header "Manual Backup & Restore"
    echo ""
    echo "Backup Options:"
    echo "  1) Full Backup (Database + Files + Settings)"
    echo "  2) Database-Only Backup (PostgreSQL + Redis + .env)"
    echo ""
    echo "Restore Options:"
    echo "  3) Full Restore (Database + Files + Settings)"
    echo "  4) Database-Only Restore (PostgreSQL + Redis)"
    echo ""
    echo "  5) Exit"
    echo ""
}

# Main execution
if [ $# -eq 0 ]; then
    # Interactive mode
    while true; do
        show_menu
        read -p "Select option: " choice
        
        case $choice in
            1)
                backup_full
                ;;
            2)
                backup_database_only
                ;;
            3)
                restore_full
                ;;
            4)
                restore_database_only
                ;;
            5)
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
        backup-full)
            backup_full
            ;;
        backup-db)
            backup_database_only
            ;;
        restore-full)
            restore_full
            ;;
        restore-db)
            restore_database_only
            ;;
        *)
            echo "Usage: $0 {backup-full|backup-db|restore-full|restore-db}"
            echo ""
            echo "  backup-full    - Full system backup"
            echo "  backup-db      - Database-only backup"
            echo "  restore-full   - Full system restore"
            echo "  restore-db     - Database-only restore"
            exit 1
            ;;
    esac
fi
