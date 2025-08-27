#!/bin/bash

# RetroLens Backend Deployment Script
# This script helps deploy the backend to Railway

echo "🚀 RetroLens Backend Deployment Script"
echo "========================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed."
    echo "Please install it from: https://docs.railway.app/develop/cli"
    exit 1
fi

echo "✅ Railway CLI detected"
echo ""

# Login to Railway
echo "📝 Logging into Railway..."
railway login

# Initialize Railway project
echo ""
echo "🏗️  Initializing Railway project..."
railway init

# Generate secure SECRET_KEY
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null)
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(openssl rand -base64 32 2>/dev/null)
fi
if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  Could not generate SECRET_KEY automatically."
    echo "Please generate one manually and set it as an environment variable."
fi

echo ""
echo "📋 Setting environment variables..."
echo "Please have the following ready from your Supabase and Clerk dashboards:"
echo ""
echo "From Supabase:"
echo "  - Project URL"
echo "  - Anon Key"
echo "  - Service Key"
echo "  - Project ID"
echo ""
echo "From Clerk:"
echo "  - Domain"
echo "  - Secret Key"
echo ""
echo "Press Enter to continue..."
read

# Set Supabase variables
echo ""
read -p "Enter Supabase URL (e.g., https://xxx.supabase.co): " SUPABASE_URL
railway variables set SUPABASE_URL="$SUPABASE_URL"

read -p "Enter Supabase Anon Key: " SUPABASE_ANON_KEY
railway variables set SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY"

read -p "Enter Supabase Service Key: " SUPABASE_SERVICE_KEY
railway variables set SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY"

read -p "Enter Supabase Project ID: " SUPABASE_PROJECT_ID
railway variables set SUPABASE_PROJECT_ID="$SUPABASE_PROJECT_ID"

# Set Clerk variables
echo ""
read -p "Enter Clerk Domain (e.g., xxx.clerk.accounts.dev): " CLERK_DOMAIN
railway variables set CLERK_DOMAIN="$CLERK_DOMAIN"

read -p "Enter Clerk Secret Key: " CLERK_SECRET_KEY
railway variables set CLERK_SECRET_KEY="$CLERK_SECRET_KEY"

# Set other variables
railway variables set SECRET_KEY="$SECRET_KEY"
railway variables set DEBUG="False"
railway variables set BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173"

echo ""
echo "✅ Environment variables set!"
echo ""
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "🌐 Getting deployment URL..."
railway domain

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Copy the deployment URL above"
echo "2. Share it with frontend developers"
echo "3. Update frontend .env.local with:"
echo "   VITE_API_URL=<your-deployment-url>"
echo ""
echo "📚 View your app:"
echo "   railway open"
echo ""
echo "📊 View logs:"
echo "   railway logs"
echo ""
echo "Happy coding! 🎉"
