#!/usr/bin/env python
"""Start the uvicorn server with proper environment setup"""

import os
import sys
import subprocess

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Change to backend directory
os.chdir(backend_dir)

# Run uvicorn
subprocess.run([
    sys.executable, "-m", "uvicorn", 
    "app.api.main:app",
    "--reload",
    "--host", "127.0.0.1",
    "--port", "8000"
])
