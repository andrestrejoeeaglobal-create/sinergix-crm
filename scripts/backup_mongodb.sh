#!/usr/bin/env bash
# ==============================================================================
# Script de Respaldo Automatizado de MongoDB — Sinergix CRM (ENMIENDA 8 - F1)
# Rotación GFS: 7 diarios, 4 semanales, 3 mensuales.
# ==============================================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/mongodb_sinergix}"
DATE=$(date +%Y%m%d_%H%M%S)
DAY_OF_WEEK=$(date +%u)
DAY_OF_MONTH=$(date +%d)
DB_NAME="sinergix_crm"
MONGO_URI="${MONGODB_URI:-mongodb://localhost:27017}"

mkdir -p "$BACKUP_DIR/daily" "$BACKUP_DIR/weekly" "$BACKUP_DIR/monthly"

DEST_FILE="$BACKUP_DIR/daily/sinergix_crm_$DATE.gz"

echo "=== Inicio de respaldos MongoDB ($DATE) ==="

# 1. Crear respaldo comprimido con mongodump
mongodump --uri="$MONGO_URI" --db="$DB_NAME" --archive="$DEST_FILE" --gzip

echo "Respaldo diario creado en: $DEST_FILE"

# 2. Copia semanal (los domingos - día 7)
if [ "$DAY_OF_WEEK" -eq 7 ]; then
    cp "$DEST_FILE" "$BACKUP_DIR/weekly/sinergix_crm_weekly_$DATE.gz"
    echo "Copia semanal archivada."
fi

# 3. Copia mensual (primer día del mes)
if [ "$DAY_OF_MONTH" -eq 01 ]; then
    cp "$DEST_FILE" "$BACKUP_DIR/monthly/sinergix_crm_monthly_$DATE.gz"
    echo "Copia mensual archivada."
fi

# 4. Rotación GFS (Eliminar respaldos antiguos)
# Mantener 7 diarios
find "$BACKUP_DIR/daily" -type f -name "*.gz" -mtime +7 -delete
# Mantener 4 semanales
find "$BACKUP_DIR/weekly" -type f -name "*.gz" -mtime +28 -delete
# Mantener 3 mensuales
find "$BACKUP_DIR/monthly" -type f -name "*.gz" -mtime +90 -delete

echo "=== Respaldo completado exitosamente ==="
