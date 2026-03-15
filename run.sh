#!/bin/bash

# Ensure background processes die if this script exits
trap 'kill $(jobs -p)' EXIT

# Export environment variables for the internal communication
export FLASK_BASE_URL="http://127.0.0.1:5000"
export PORT=5000

echo "Starting Flask Backend on port 5000..."
python main.py &

# Wait a brief moment to ensure backend starts before frontend
sleep 3

echo "Starting Streamlit Frontend on port 7860..."
# Hugging Face Spaces requires the app to listen on port 7860
streamlit run streamlit_app/app.py --server.port 7860 --server.address 0.0.0.0
