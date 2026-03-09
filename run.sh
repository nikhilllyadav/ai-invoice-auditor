#!/bin/bash

# Function to kill background processes when script exits
cleanup() {
    echo "Stopping all processes..."
    kill $(jobs -p)
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT

echo "Starting Monitor Agent..."
python -m agents.monitor_agent &

echo "Starting Streamlit App..."
kill $(lsof -t -i:8080)
python -m streamlit run ui/streamlit_app.py --server.port 8080 &

# echo "Starting Interrupt Streamlit App..."
# kill $(lsof -t -i:8081)
# ./group3-venv/bin/python -m streamlit run ui/interrupt_ui.py --server.port 8081 &

echo "Starting Mock ERP API"
kill $(lsof -t -i:8082)
uvicorn mock_erp.app:app --reload --port 8082 &

# Wait for all background processes to finish
wait
