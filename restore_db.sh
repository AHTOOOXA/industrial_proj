#!/bin/bash

# Find the latest backup file
LATEST_BACKUP=$(ls -t /Users/anton/Downloads/dbbackup_*.psql 2>/dev/null | head -n 1)

# Check if the latest backup file exists
if [ -z "$LATEST_BACKUP" ]; then
    echo "No backup files found in /Users/anton/Downloads."
    exit 1
fi

# Copy the latest backup file to the container's allowed backup directory
docker cp "$LATEST_BACKUP" django_app:/app/backup/

# Restore the database in the Django container
docker exec -i django_app python manage.py dbrestore --input-file="$(basename "$LATEST_BACKUP")" --noinput

# Check if the restore command was successful
if [ $? -eq 0 ]; then
    echo "Database restored successfully from ${LATEST_BACKUP}."
else
    echo "Failed to restore the database."
fi
