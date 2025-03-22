# Registraction

A FastAPI-based application for managing VIP membership registrations for local stores and supermarkets.

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd registraction
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Copy the `.env.example` to `.env` and update the values (e.g., DATABASE_URL).

5. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

## Project Structure
- `app/`: Core application files.
- `app/templates/`: Jinja2 templates for the front-end.
- `app/static/`: CSS, JS, and image assets.
- `tests/`: Unit tests.

## Features
- Check if a phone number exists in the VIP database.
- Register new VIP members with a unique membership code and barcode.
- Modern, mobile-friendly UI.

## Requirements
- Python 3.9+
- MySQL database
