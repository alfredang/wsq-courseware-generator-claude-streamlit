# Troubleshooting

Solutions to common issues you might encounter.

## Import Errors
If you see `ModuleNotFoundError`:
- Ensure you have activated your virtual environment: `source .venv/bin/activate`
- Re-install dependencies: `uv pip install -r requirements.txt`

## API Key Issues
- **Empty Key**: Check that your `.env` or `.streamlit/secrets.toml` contains the correct variable names.
- **Authentication Error**: Verify the key is valid on the provider's dashboard (OpenAI, OpenRouter, or Google).
- **Settings UI**: We recommend using the **Settings → API Keys** tab in the app for the most reliable configuration.

## Document Processing
- **File Format**: Ensure you are uploading `.docx` files for TSC documents.
- **Parsing Errors**: Check that your TSC document follows the required LU/Topic format (e.g., `LU1: Title (K1, A1)`).

## Still need help?
If your issue isn't covered here, please review the logs in your terminal or contact the development team at Tertiary Infotech.
