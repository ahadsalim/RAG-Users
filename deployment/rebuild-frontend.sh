#!/bin/bash

# Script to rebuild frontend and clear Next.js cache
# Usage: ./rebuild-frontend.sh

echo "🔄 Stopping frontend..."
cd /srv/deployment
docker-compose stop frontend

echo "🗑️  Clearing Next.js cache..."
rm -rf /srv/frontend/.next

echo "🚀 Starting frontend..."
docker-compose up -d frontend

echo "⏳ Waiting for frontend to be ready..."
sleep 5

echo "📋 Checking logs..."
docker-compose logs frontend --tail=10

echo ""
echo "✅ Frontend rebuilt successfully!"
echo "🌐 Access: http://localhost:3000"
