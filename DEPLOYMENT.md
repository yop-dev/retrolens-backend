# RetroLens Backend - Deployment Guide

## 🎉 Local Development Successfully Running!

Your backend is now running locally and connected to Supabase!

### Access Points:
- **API Server**: http://localhost:8000
- **Interactive API Docs (Swagger)**: http://localhost:8000/api/v1/docs
- **ReDoc Documentation**: http://localhost:8000/api/v1/redoc

### ✅ What's Working:
1. FastAPI server is running
2. Successfully connected to Supabase database
3. All API endpoints are functional
4. Discussion categories loaded from database (6 categories)
5. Storage buckets configured for images

## 🚀 Deploy to Railway

### Step 1: Prepare for Deployment

1. **Create a GitHub repository** for your backend code
2. **Important**: Remove `.env` from tracking:
   ```bash
   git rm --cached .env
   git commit -m "Remove .env from tracking"
   ```

### Step 2: Set Up Railway

1. Go to [Railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your backend repository

### Step 3: Configure Environment Variables

In Railway dashboard, add these environment variables:

```
SUPABASE_URL=https://cgckdjxwsctoczhfddxm.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNnY2tkanh3c2N0b2N6aGZkZHhtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYxNzc0MzYsImV4cCI6MjA3MTc1MzQzNn0.twQlE7vZ2G72TncCkvoNqY0u-oQctKFkQHK9c2kGPZU
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNnY2tkanh3c2N0b2N6aGZkZHhtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjE3NzQzNiwiZXhwIjoyMDcxNzUzNDM2fQ.mp3heCldkTpvjFjdjJx7yYgtKNaAoqTi0c70PKntxF8
SUPABASE_PROJECT_ID=cgckdjxwsctoczhfddxm
API_V1_STR=/api/v1
PROJECT_NAME=RetroLens
VERSION=1.0.0
DEBUG=False
BACKEND_CORS_ORIGINS=["https://your-frontend.vercel.app","http://localhost:3000"]
SECRET_KEY=generate-a-secure-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Step 4: Deploy

Railway will automatically:
1. Detect your Python app
2. Install dependencies from `requirements-simple.txt`
3. Start the server using the command in `railway.json`

### Step 5: Get Your API URL

Once deployed, Railway will provide you with a URL like:
```
https://retrolens-backend.up.railway.app
```

Update your frontend to use this URL for API calls.

## 📝 Testing Your Deployed API

Test your deployed API:
```bash
# Health check
curl https://your-app.up.railway.app/health

# View docs
# Open in browser: https://your-app.up.railway.app/api/v1/docs
```

## 🔧 Troubleshooting

### If deployment fails:

1. **Check Railway logs** for error messages
2. **Ensure all environment variables** are set correctly
3. **Update requirements**: Use `requirements-simple.txt` for Railway:
   ```bash
   # In railway.json, you can specify:
   {
     "build": {
       "builder": "NIXPACKS",
       "buildCommand": "pip install -r requirements-simple.txt"
     }
   }
   ```

### Common Issues:

1. **Module not found**: Make sure all dependencies are in requirements-simple.txt
2. **Port binding**: Railway sets PORT automatically, our app reads it
3. **CORS errors**: Update BACKEND_CORS_ORIGINS with your frontend URL

## 🎯 Next Steps

1. **Frontend Development**: Start building your React frontend
2. **Authentication**: Integrate Clerk in frontend
3. **Testing**: Add more comprehensive tests
4. **CI/CD**: Set up GitHub Actions for automated testing

## 📞 Support

- Railway Documentation: https://docs.railway.app
- FastAPI Documentation: https://fastapi.tiangolo.com
- Supabase Documentation: https://supabase.com/docs

---

**Your backend is ready for production deployment! 🚀**
