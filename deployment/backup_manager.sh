#!/bin/bash

# ============================================
# Backup & Restore Manager
# Platform Management System
# ============================================

set -e

# Configuration
BACKUP_DIR="/srv/backups"
DEPLOYMENT_DIR="/srv/deployment"
ENV_FILE="${DEPLOYMENT_DIR}/.env"

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

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
# BACKUP FUNCTIONS
# ============================================

backup_full() {
    print_header "Full Backup (Database + Files)"
    
    mkdir -p "$BACKUP_DIR"
    
    DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_NAME="full_backup_${DATE}"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
    
    print_info "Creating backup: ${BACKUP_NAME}"
    mkdir -p "$BACKUP_PATH"
    
    # Database Backup
    print_info "Backing up PostgreSQL database..."
    docker exec app_postgres pg_dump \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=custom \
        --blobs \
        --compress=9 \
        > "${BACKUP_PATH}/postgres_backup.dump" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Database backup completed"
    else
        print_error "Database backup failed"
    fi
    
    # Redis Backup
    print_info "Backing up Redis data..."
    docker exec app_redis redis-cli BGSAVE > /dev/null 2>&1
    sleep 3
    docker cp app_redis:/data/dump.rdb "${BACKUP_PATH}/redis_backup.rdb" 2>/dev/null || true
    print_success "Redis backup completed"
    
    # Media Files
    print_info "Backing up media files..."
    docker run --rm \
        -v app_media_files:/data \
        -v ${BACKUP_PATH}:/backup \
        alpine \
        tar czf /backup/media_files.tar.gz -C /data . 2>/dev/null
    print_success "Media files backup completed"
    
    # Static Files
    print_info "Backing up static files..."
    docker run --rm \
        -v app_static_files:/data \
        -v ${BACKUP_PATH}:/backup \
        alpine \
        tar czf /backup/static_files.tar.gz -C /data . 2>/dev/null || true
    print_success "Static files backup completed"
    
    # NPM Data
    print_info "Backing up NPM data..."
    docker run --rm \
        -v app_npm_data:/data \
        -v ${BACKUP_PATH}:/backup \
        alpine \
        tar czf /backup/npm_data.tar.gz -C /data . 2>/dev/null || true
    print_success "NPM data backup completed"
    
    # Configuration Files
    print_info "Backing up configuration..."
    cp "$ENV_FILE" "${BACKUP_PATH}/.env" 2>/dev/null || true
    print_success "Configuration backup completed"
    
    # Compress backup
    print_info "Compressing backup..."
    cd "${BACKUP_DIR}"
    tar czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
    BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    rm -rf "${BACKUP_NAME}"
    print_success "Compression completed (Size: ${BACKUP_SIZE})"
    
    # Apply retention policy
    print_info "Applying retention policy (${RETENTION_DAYS} days)..."
    find "${BACKUP_DIR}" -name "full_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    find "${BACKUP_DIR}" -name "db_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    
    print_success "Backup completed: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"
}

backup_database_only() {
    print_header "Database-Only Backup"
    
    mkdir -p "$BACKUP_DIR"
    
    DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_NAME="db_backup_${DATE}"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
    
    print_info "Creating database backup: ${BACKUP_NAME}"
    mkdir -p "$BACKUP_PATH"
    
    # PostgreSQL Backup
    print_info "Backing up PostgreSQL database..."
    docker exec app_postgres pg_dump \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=custom \
        --blobs \
        --compress=9 \
        > "${BACKUP_PATH}/postgres_backup.dump" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Database backup completed"
    else
        print_error "Database backup failed"
    fi
    
    # Redis Backup
    print_info "Backing up Redis data..."
    docker exec app_redis redis-cli BGSAVE > /dev/null 2>&1
    sleep 3
    docker cp app_redis:/data/dump.rdb "${BACKUP_PATH}/redis_backup.rdb" 2>/dev/null || true
    print_success "Redis backup completed"
    
    # Compress
    print_info "Compressing backup..."
    cd "${BACKUP_DIR}"
    tar czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
    BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    rm -rf "${BACKUP_NAME}"
    print_success "Compression completed (Size: ${BACKUP_SIZE})"
    
    # Apply retention policy
    print_info "Applying retention policy (${RETENTION_DAYS} days)..."
    find "${BACKUP_DIR}" -name "db_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    
    print_success "Database backup completed: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"
}

# ============================================
# RESTORE FUNCTIONS
# ============================================

restore_full() {
    print_header "Full Restore (Database + Files)"
    
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run as root"
    fi
    
    # List available backups
    print_info "Available full backups:"
    echo ""
    ls -lht ${BACKUP_DIR}/full_backup_*.tar.gz 2>/dev/null | head -20 | awk '{print NR". "$9" ("$5", "$6" "$7")"}'
    echo ""
    
    read -p "Enter backup number or full path: " BACKUP_CHOICE
    
    if [[ "$BACKUP_CHOICE" =~ ^[0-9]+$ ]]; then
        BACKUP_FILE=$(ls -t ${BACKUP_DIR}/full_backup_*.tar.gz 2>/dev/null | sed -n "${BACKUP_CHOICE}p")
    else
        BACKUP_FILE="$BACKUP_CHOICE"
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
    fi
    
    print_info "Selected: $(basename $BACKUP_FILE)"
    
    echo ""
    print_info "⚠️  WARNING: This will REPLACE ALL current data!"
    echo ""
    read -p "Type 'yes' to confirm restore: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        print_info "Restore cancelled"
        exit 0
    fi
    
    # Create temp directory
    RESTORE_DIR="/tmp/restore_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$RESTORE_DIR"
    
    # Extract
    print_info "Extracting backup..."
    cd "$RESTORE_DIR"
    tar xzf "$BACKUP_FILE"
    BACKUP_NAME=$(ls -d full_backup_* 2>/dev/null | head -1)
    
    if [ ! -d "$BACKUP_NAME" ]; then
        rm -rf "$RESTORE_DIR"
        print_error "Invalid backup structure"
    fi
    
    cd "$BACKUP_NAME"
    
    # Stop services
    print_info "Stopping all services..."
    cd "$DEPLOYMENT_DIR"
    docker-compose down
    print_success "Services stopped"
    
    # Restore PostgreSQL
    if [ -f "${RESTORE_DIR}/${BACKUP_NAME}/postgres_backup.dump" ]; then
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
            < "${RESTORE_DIR}/${BACKUP_NAME}/postgres_backup.dump" 2>/dev/null
        
        print_success "Database restored"
    fi
    
    # Restore Redis
    if [ -f "${RESTORE_DIR}/${BACKUP_NAME}/redis_backup.rdb" ]; then
        print_info "Restoring Redis..."
        docker-compose up -d redis
        sleep 5
        
        docker exec app_redis redis-cli SHUTDOWN 2>/dev/null || true
        sleep 2
        docker cp "${RESTORE_DIR}/${BACKUP_NAME}/redis_backup.rdb" app_redis:/data/dump.rdb
        docker-compose restart redis
        
        print_success "Redis restored"
    fi
    
    # Restore Media Files
    if [ -f "${RESTORE_DIR}/${BACKUP_NAME}/media_files.tar.gz" ]; then
        print_info "Restoring media files..."
        docker run --rm \
            -v app_media_files:/data \
            -v ${RESTORE_DIR}/${BACKUP_NAME}:/backup \
            alpine \
            sh -c "rm -rf /data/* && tar xzf /backup/media_files.tar.gz -C /data"
        
        print_success "Media files restored"
    fi
    
    # Restore Static Files
    if [ -f "${RESTORE_DIR}/${BACKUP_NAME}/static_files.tar.gz" ]; then
        print_info "Restoring static files..."
        docker run --rm \
            -v app_static_files:/data \
            -v ${RESTORE_DIR}/${BACKUP_NAME}:/backup \
            alpine \
            sh -c "rm -rf /data/* && tar xzf /backup/static_files.tar.gz -C /data"
        
        print_success "Static files restored"
    fi
    
    # Restore NPM Data
    if [ -f "${RESTORE_DIR}/${BACKUP_NAME}/npm_data.tar.gz" ]; then
        print_info "Restoring NPM data..."
        docker run --rm \
            -v app_npm_data:/data \
            -v ${RESTORE_DIR}/${BACKUP_NAME}:/backup \
            alpine \
            sh -c "rm -rf /data/* && tar xzf /backup/npm_data.tar.gz -C /data"
        
        print_success "NPM data restored"
    fi
    
    # Start services
    print_info "Starting all services..."
    cd "$DEPLOYMENT_DIR"
    docker-compose up -d
    
    # Cleanup
    rm -rf "$RESTORE_DIR"
    
    print_success "Full restore completed successfully!"
    echo ""
    docker-compose ps
}

restore_database_only() {
    print_header "Database-Only Restore"
    
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run as root"
    fi
    
    # List available backups
    print_info "Available database backups:"
    echo ""
    ls -lht ${BACKUP_DIR}/db_backup_*.tar.gz 2>/dev/null | head -20 | awk '{print NR". "$9" ("$5", "$6" "$7")"}'
    echo ""
    
    read -p "Enter backup number or full path: " BACKUP_CHOICE
    
    if [[ "$BACKUP_CHOICE" =~ ^[0-9]+$ ]]; then
        BACKUP_FILE=$(ls -t ${BACKUP_DIR}/db_backup_*.tar.gz 2>/dev/null | sed -n "${BACKUP_CHOICE}p")
    else
        BACKUP_FILE="$BACKUP_CHOICE"
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
    fi
    
    print_info "Selected: $(basename $BACKUP_FILE)"
    
    echo ""
    print_info "⚠️  WARNING: This will REPLACE current database!"
    echo ""
    read -p "Type 'yes' to confirm restore: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        print_info "Restore cancelled"
        exit 0
    fi
    
    # Create temp directory
    RESTORE_DIR="/tmp/restore_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$RESTORE_DIR"
    
    # Extract
    print_info "Extracting backup..."
    cd "$RESTORE_DIR"
    tar xzf "$BACKUP_FILE"
    BACKUP_NAME=$(ls -d db_backup_* 2>/dev/null | head -1)
    
    if [ ! -d "$BACKUP_NAME" ]; then
        rm -rf "$RESTORE_DIR"
        print_error "Invalid backup structure"
    fi
    
    cd "$BACKUP_NAME"
    
    # Stop backend services
    print_info "Stopping backend services..."
    cd "$DEPLOYMENT_DIR"
    docker-compose stop backend celery_worker celery_beat
    print_success "Backend services stopped"
    
    # Restore PostgreSQL
    if [ -f "${RESTORE_DIR}/${BACKUP_NAME}/postgres_backup.dump" ]; then
        print_info "Restoring PostgreSQL database..."
        
        docker exec app_postgres psql -U "${DB_USER}" postgres -c "DROP DATABASE IF EXISTS ${DB_NAME};" 2>/dev/null || true
        docker exec app_postgres psql -U "${DB_USER}" postgres -c "CREATE DATABASE ${DB_NAME};"
        
        docker exec -i app_postgres pg_restore \
            -U "${DB_USER}" \
            -d "${DB_NAME}" \
            --verbose \
            --clean \
            --if-exists \
            < "${RESTORE_DIR}/${BACKUP_NAME}/postgres_backup.dump" 2>/dev/null
        
        print_success "Database restored"
    fi
    
    # Restore Redis
    if [ -f "${RESTORE_DIR}/${BACKUP_NAME}/redis_backup.rdb" ]; then
        print_info "Restoring Redis..."
        
        docker exec app_redis redis-cli SHUTDOWN 2>/dev/null || true
        sleep 2
        docker cp "${RESTORE_DIR}/${BACKUP_NAME}/redis_backup.rdb" app_redis:/data/dump.rdb
        docker-compose restart redis
        
        print_success "Redis restored"
    fi
    
    # Start backend services
    print_info "Starting backend services..."
    docker-compose up -d backend celery_worker celery_beat
    
    # Cleanup
    rm -rf "$RESTORE_DIR"
    
    print_success "Database restore completed successfully!"
    echo ""
    docker-compose ps
}

list_backups() {
    print_header "Available Backups"
    echo ""
    echo "Full Backups:"
    ls -lht ${BACKUP_DIR}/full_backup_*.tar.gz 2>/dev/null | awk '{print "  "$9, "("$5", "$6" "$7")"}' || echo "  No full backups found"
    echo ""
    echo "Database-Only Backups:"
    ls -lht ${BACKUP_DIR}/db_backup_*.tar.gz 2>/dev/null | awk '{print "  "$9, "("$5", "$6" "$7")"}' || echo "  No database backups found"
    echo ""
    
    TOTAL_SIZE=$(du -sh ${BACKUP_DIR} 2>/dev/null | cut -f1)
    echo "Total backup size: ${TOTAL_SIZE}"
}

# ============================================
# MAIN MENU
# ============================================

show_menu() {
    print_header "Backup & Restore Manager"
    echo ""
    echo "Backup Options:"
    echo "  1) Full Backup (Database + Files)"
    echo "  2) Database-Only Backup"
    echo ""
    echo "Restore Options:"
    echo "  3) Full Restore (Database + Files)"
    echo "  4) Database-Only Restore"
    echo ""
    echo "Other:"
    echo "  5) List All Backups"
    echo "  6) Exit"
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
                list_backups
                ;;
            6)
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
        list)
            list_backups
            ;;
        *)
            echo "Usage: $0 {backup-full|backup-db|restore-full|restore-db|list}"
            exit 1
            ;;
    esac
fi
