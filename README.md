# RetroLens Backend API

FastAPI backend for the RetroLens vintage camera community platform.

## Tech Stack

- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Storage**: Supabase Storage
- **Authentication**: Clerk (via frontend) + Supabase Auth
- **Deployment**: Railway

## Setup Instructions

### 1. Install Python Dependencies

First, create a virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Set Up Supabase

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the SQL scripts in order:
   - `app/db/schema.sql` - Creates all database tables
   - `app/db/storage_buckets.sql` - Sets up storage buckets

### 3. Configure Environment Variables

The `.env` file is already configured with your Supabase credentials. 
**Important**: Never commit the `.env` file to version control!

### 4. Run the Development Server

```bash
# From the backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the provided run script:

```bash
python run.py
```

The API will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## API Endpoints

### Core Endpoints

#### Users
- `GET /api/v1/users` - List all users
- `GET /api/v1/users/{user_id}` - Get user by ID
- `GET /api/v1/users/username/{username}` - Get user by username
- `POST /api/v1/users` - Create new user
- `PATCH /api/v1/users/{user_id}` - Update user
- `POST /api/v1/users/{user_id}/follow` - Follow user
- `DELETE /api/v1/users/{user_id}/unfollow` - Unfollow user

#### Cameras
- `GET /api/v1/cameras` - List all public cameras
- `GET /api/v1/cameras/{camera_id}` - Get camera details
- `POST /api/v1/cameras` - Create new camera

#### Discussions
- `GET /api/v1/discussions` - List all discussions
- `GET /api/v1/discussions/{discussion_id}` - Get discussion details
- `POST /api/v1/discussions` - Create new discussion

#### Categories
- `GET /api/v1/categories` - List all discussion categories

#### Upload
- `POST /api/v1/upload/camera-image` - Upload camera image
- `POST /api/v1/upload/avatar` - Upload user avatar

## Testing the API

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Get categories
curl http://localhost:8000/api/v1/categories

# List cameras
curl http://localhost:8000/api/v1/cameras
```

### Using the Interactive Docs

Navigate to http://localhost:8000/api/v1/docs to use the interactive Swagger UI.

## Deployment to Railway

1. Create a new project on Railway
2. Connect your GitHub repository
3. Add environment variables from `.env`
4. Deploy!

Railway will automatically detect the FastAPI app and deploy it.

### Railway Configuration

Create a `railway.json` file in the backend directory:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── api_v1/
│   │       ├── endpoints/      # API endpoints
│   │       └── api.py          # Main router
│   ├── core/
│   │   └── config.py          # Settings and configuration
│   ├── db/
│   │   ├── schema.sql         # Database schema
│   │   └── supabase.py        # Supabase client
│   ├── schemas/               # Pydantic models
│   └── main.py               # FastAPI application
├── tests/                     # Test files
├── .env                      # Environment variables (don't commit!)
├── .gitignore               # Git ignore file
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Common Issues

### ModuleNotFoundError
Make sure you're running the server from the backend directory and have activated the virtual environment.

### Supabase Connection Error
Check that your Supabase project is active and the credentials in `.env` are correct.

### CORS Issues
The CORS settings in `app/core/config.py` should include your frontend URL. Update `BACKEND_CORS_ORIGINS` as needed.

## Next Steps

1. Test all endpoints using the interactive docs
2. Set up proper authentication with Clerk
3. Add more comprehensive error handling
4. Implement remaining endpoints (comments, likes, etc.)
5. Add input validation and sanitization
6. Set up automated tests
7. Configure CI/CD pipeline
