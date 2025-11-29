
#!/bin/bash
# Cleanup GCP resources (use with caution!)

PROJECT_ID="${GCP_PROJECT_ID:-technical-analysis-prod}"
REGION="${GCP_REGION:-us-central1}"

echo "⚠️  WARNING: This will delete all GCP resources!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo "🗑️  Cleaning up GCP resources..."
