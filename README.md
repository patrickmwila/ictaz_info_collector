# ICTAZ Member Information System

A Flask-based web application for managing member information for ICTAZ.

## Features

- Query member information using ID numbers
- One-time data entry for members
- Mobile number validation (must start with 260)
- Data export to CSV
- Pre-loaded ID numbers
- Responsive Bootstrap UI

## Requirements

- Python 3.x
- Flask
- Flask-SQLAlchemy
- WTForms
- Flask-WTF
- email-validator

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Make sure your virtual environment is activated
2. Run the Flask application:
   ```bash
   python app.py
   ```
3. Open a web browser and navigate to `http://localhost:5000`

## Usage

1. Enter an ID number on the home page
2. If the ID exists:
   - If no details are present, you'll be taken to a form to enter your information
   - If details exist, you'll see your stored information (read-only)
3. If the ID doesn't exist, you'll receive an error message

## Exporting Data

1. Click the "Export Data" link in the navigation bar
2. The system will generate and download a CSV file containing all member information

## Database

The application uses SQLite as the database. The database file (`members.db`) will be created automatically when you first run the application.

## ID Numbers

Pre-loaded ID numbers are stored in `idnumbers.json`. These are loaded into the database when the application starts.
