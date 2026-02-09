Clear all Streamlit cache, kill any running Streamlit process, and start a fresh Streamlit instance using the uv .venv environment.

Steps:
1. Clear Streamlit cache by removing the `.streamlit/cache` directory if it exists
2. Kill any running `streamlit` processes
3. Start `uv run streamlit run app.py` in the background (this ensures the .venv environment and all dependencies are used)
4. Confirm the app is running and show the URL (default: http://localhost:8501)
