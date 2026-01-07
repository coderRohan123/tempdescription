# Product Description Generator

A full-stack application for generating product descriptions using AI, with user authentication and history tracking.

## Features

- **Guest Access**: Generate product descriptions without registration
- **User Authentication**: JWT-based authentication with refresh tokens
- **History Tracking**: Save and view generation history (requires login)
- **Multi-language Support**: Generate descriptions in multiple languages
- **Modern UI**: Beautiful, responsive React + TypeScript frontend

## Tech Stack

### Backend
- Flask (Python)
- PostgreSQL
- JWT Authentication
- Google Gemini AI
- bcrypt for password hashing

### Frontend
- React 19 + TypeScript
- Vite
- React Router
- Axios

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL database
- Google Gemini API key

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file in the backend directory:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=prody
DB_USER=postgres
DB_PASSWORD=1234

JWT_SECRET=your-secret-key-change-in-production

GOOGLE_API_KEY=your-google-api-key-here
```

6. Make sure your PostgreSQL database is running and the tables are created (see SQL schema in the user's initial message).

7. Run the Flask server:
```bash
python main.py
```

Or alternatively:
```bash
flask run
```

The backend will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd my-app
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file (optional, defaults to `http://localhost:5000`):
```env
VITE_API_URL=http://localhost:5000
```

4. Run the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:5173` (or another port if 5173 is taken)

## Database Schema

The application uses the following PostgreSQL tables:
- `users` - User accounts
- `refresh_tokens` - JWT refresh tokens
- `generations` - Product description generation history

See the SQL schema provided in the initial setup for table definitions.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/me` - Get current user (protected)

### Generation
- `POST /api/generate-description` - Generate product description (public, saves if authenticated)
- `GET /api/generations` - Get user's generation history (protected)

## Usage

1. **As Guest**: Navigate to the home page and start generating descriptions. Your generations won't be saved.

2. **As Registered User**: 
   - Register or login to save your generation history
   - All generations will be automatically saved to your account
   - View your history in the History page

## Notes

- Guest users can access the generation service without authentication
- Registration/login is only required to save generation history
- Access tokens expire after 15 minutes
- Refresh tokens expire after 30 days
- Passwords are hashed using bcrypt



