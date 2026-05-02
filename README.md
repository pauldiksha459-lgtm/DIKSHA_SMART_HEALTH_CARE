##DIKSHA_SMART_HEALTH_CARE
# Smart Healthcare System

Offline-first Smart Healthcare System built with HTML, CSS, JavaScript, Python Flask, and SQLite for secure local patient record management, rule-based health analysis, alerts, graphs, doctor suggestions, and PDF report generation.

## Overview

This project is designed for a college exhibition and demonstrates how a simple healthcare web application can work completely offline. It provides separate login access for Doctors and Patients, stores health records locally, analyzes basic vital values, shows graphs, and generates downloadable PDF reports.

## Features

- Secure signup and login with two roles: `Doctor` and `Patient`
- Password hashing before saving credentials in SQLite
- Offline local database storage using SQLite
- Dashboard with sidebar navigation, metric cards, alerts, and record history
- Health record form for:
  - patient name
  - age
  - gender
  - symptoms
  - body temperature
  - heart rate
  - treatment preference
- Auto-generated date and time for each record
- Rule-based health analysis
- One-word output status: `Normal`, `Warning`, or `Critical`
- Detailed explanation of the detected condition
- Suggestions based on preference:
  - Allopathy
  - Ayurvedic
- Static doctor recommendation list
- Temperature vs time and heart rate vs time graph display
- Critical alert message with simulated SMS notification
- PDF report generation using ReportLab
- Seeded demo users and sample health records

## Tech Stack

- `HTML` for page structure
- `CSS` for styling and layout
- `JavaScript` for frontend interactivity
- `Python` with `Flask` for backend logic
- `SQLite` for local database storage
- `ReportLab` for PDF report generation

## Project Structure

```text
smart-healthcare-system/
|-- app.py
|-- schema.sql
|-- requirements.txt
|-- README.md
|-- instance/
|-- static/
|   |-- css/
|   |   `-- style.css
|   `-- js/
|       |-- chart.umd.js
|       `-- dashboard.js
`-- templates/
    |-- base.html
    |-- dashboard.html
    |-- login.html
    `-- signup.html
```

## How It Works

1. The user signs up or logs in as a Doctor or Patient.
2. After login, the user reaches the dashboard.
3. Health data is entered through the patient record form.
4. The data is saved locally in SQLite.
5. The system analyzes temperature and heart rate values.
6. A status is shown as Normal, Warning, or Critical.
7. Suggestions, alerts, doctor recommendations, and graphs are displayed.
8. A PDF report can be downloaded for any saved record.

## Health Analysis Logic

### Temperature

- Below `97 F` -> Low
- `97 F` to `99.5 F` -> Normal
- `99.6 F` to `102 F` -> High
- Above `102 F` -> Very High

### Heart Rate

- Below `60 bpm` -> Low
- `60 bpm` to `100 bpm` -> Normal
- `101 bpm` to `120 bpm` -> High
- Above `120 bpm` -> Very High

### Output Status

- `Normal`
- `Warning`
- `Critical`

## Demo Credentials

### Doctor

- Username: `doctor_demo`
- Password: `doctor123`

### Patient

- Username: `patient_demo`
- Password: `patient123`

## Setup Instructions

### 1. Open the project folder

```powershell
cd C:\Users\Diksha\Documents\Codex\2026-04-17-build-a-complete-offline-first-smart
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.venv\Scripts\activate
```

### 4. Install required packages

```powershell
pip install -r requirements.txt
```

### 5. Run the application

```powershell
python app.py
```

If `python` is not recognized, you can run:

```powershell
.venv\Scripts\python.exe app.py
```

### 6. Open in browser

Use either of these local addresses:

- [http://127.0.0.1:5000](http://127.0.0.1:5000)
- [http://localhost:5000](http://localhost:5000)

## Offline Notes

- All user and patient data is stored locally in SQLite.
- No internet connection is required for the main system.
- No real SMS API is used.
- Doctor recommendations are static and local.
- Graph rendering uses a local JavaScript file.
- PDF reports are generated locally on the same machine.

## Educational Use

This system is mainly built for:

- college exhibition demonstration
- healthcare awareness projects
- offline web application learning
- beginner-friendly Flask and SQLite practice

## Limitations

- Not intended for real hospital deployment
- No real medical diagnosis
- No real-time IoT sensor integration
- No live SMS or email alert service
- No cloud sync or multi-device access

## Disclaimer

This system is for educational purposes only and not a replacement for professional medical advice.
