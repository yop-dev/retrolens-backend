#!/usr/bin/env python
"""Start script for Railway deployment."""
import os
import uvicorn

if __name__ == "__main__":
    # Get port from Railway environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Start the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
