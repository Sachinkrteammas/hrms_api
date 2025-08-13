# HRMS FastAPI Backend

A comprehensive Human Resource Management System (HRMS) backend built with FastAPI, providing background verification and candidate management functionality.

## Features

- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **Candidate Management**: Add, update, and manage candidate profiles
- **Background Verification**: Multiple verification services (Identity, Employment, Court, AML, Bank)
- **Reference Checks**: Automated reference verification system
- **Company Management**: Multi-tenant company support with credit system
- **Email Notifications**: Automated email sending for candidates and references
- **File Upload**: CSV bulk candidate upload functionality
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## Tech Stack

- **Framework**: FastAPI
- **Database**: MySQL with SQLAlchemy ORM
- **Authentication**: JWT with Python-Jose
- **Password Hashing**: Passlib with bcrypt
- **Email**: SMTP with Python email libraries
- **File Processing**: Pandas for CSV handling
- **Validation**: Pydantic models
- **Documentation**: Auto-generated with FastAPI

## Project Structure

```
hrms-api/
├── models/                 # SQLAlchemy database models
│   ├── __init__.py
│   ├── database.py        # Database configuration
│   ├── user.py           # User-related models
│   ├── company.py        # Company-related models
│   ├── candidate.py      # Candidate-related models
│   ├── verification.py   # Verification-related models
│   └── reference.py      # Reference check models
├── schemas/              # Pydantic request/response models
│   ├── __init__.py
│   ├── auth.py          # Authentication schemas
│   ├── candidate.py     # Candidate schemas
│   ├── company.py       # Company schemas
│   └── common.py        # Common schemas
├── routers/             # FastAPI route handlers
│   ├── __init__.py
│   ├── auth.py          # Authentication routes
│   ├── candidate.py     # Candidate routes
│   ├── company.py       # Company routes
│   ├── admin.py         # Admin routes
│   └── common.py        # Common routes
├── services/            # Business logic services
│   ├── __init__.py
│   ├── candidate_service.py
│   ├── company_service.py
│   ├── email_service.py
│   └── verification_service.py
├── dependencies/        # FastAPI dependencies
│   ├── __init__.py
│   └── auth.py         # Authentication dependencies
├── utils/              # Utility functions
│   ├── __init__.py
│   └── candidate_utils.py
├── main.py             # FastAPI application entry point
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Installation

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- Redis (optional, for caching)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hrms-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```env
   # Database
   DATABASE_URL=mysql+pymysql://username:password@localhost/hrms_db
   
   # JWT
   SECRET_KEY=your-super-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # Email
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   FROM_EMAIL=noreply@hrms.com
   
   # Frontend
   FRONTEND_URL=http://localhost:3000
   
   # Verification APIs
   VERIFICATION_API_BASE_URL=https://api.verification.com
   VERIFICATION_API_KEY=your-api-key
   
   # AWS (optional)
   AWS_ACCESS_KEY_ID=your-aws-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret
   AWS_REGION=us-east-1
   AWS_S3_BUCKET=hrms-uploads
   
   # Redis (optional)
   REDIS_URL=redis://localhost:6379
   ```

5. **Database Setup**
   ```bash
   # Create MySQL database
   mysql -u root -p
   CREATE DATABASE hrms_db;
   CREATE USER 'hrms_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON hrms_db.* TO 'hrms_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once the application is running, you can access:

- **Interactive API Docs (Swagger UI)**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Authentication (`/accounts`)
- `POST /accounts/signup` - User registration
- `POST /accounts/login` - User login
- `POST /accounts/otp/request` - Request OTP
- `POST /accounts/otp/verify` - Verify OTP
- `GET /accounts/me` - Get current user info

### Candidates (`/candidate`)
- `POST /candidate` - Add new candidate
- `POST /candidate/upload` - Upload candidates via CSV
- `GET /candidate` - Get candidates list (admin only)
- `GET /candidate/details/{slug}` - Get candidate details by slug
- `POST /candidate/login` - Candidate login
- `PUT /candidate` - Update candidate (candidate only)
- `POST /candidate/sendEmail` - Resend email to candidate
- `POST /candidate/reject` - Reject candidate
- `POST /candidate/aadhar/otp` - Send Aadhar OTP
- `POST /candidate/aadhar/verify` - Verify Aadhar OTP

### Reference Checks (`/candidate/reference`)
- `GET /candidate/reference` - Get reference data (admin only)
- `POST /candidate/reference/login` - Reference login
- `POST /candidate/reference/sendEmail` - Send reference email
- `PUT /candidate/reference/update` - Update reference info
- `GET /candidate/reference/{slug}` - Get reference details by slug

### Company (`/company`)
- `GET /company/profile` - Get company profile
- `PUT /company/profile` - Update company profile
- `GET /company/credits` - Get company credits
- `POST /company/credits/add` - Add company credits

### Admin (`/admin`)
- `GET /admin/dashboard` - Get admin dashboard data
- `GET /admin/reports` - Get admin reports

### Common (`/common`)
- `GET /common/verification-statuses` - Get verification statuses
- `GET /common/health` - Health check

## Database Schema

The application uses the following main entities:

- **User**: System users (HR, HR_HEAD)
- **Company**: Organizations using the system
- **Candidate**: People undergoing background verification
- **VerificationStatus**: Status tracking for verifications
- **CandidateReferenceCheck**: Reference verification records
- **Reports**: Various verification reports (Identity, Employment, Court, AML, Bank)

## Development

### Running in Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Formatting
```bash
pip install black isort
black .
isort .
```

## Deployment

### Production Setup

1. **Update environment variables** for production settings
2. **Set up a production database** (MySQL/PostgreSQL)
3. **Configure reverse proxy** (Nginx/Apache)
4. **Set up SSL certificates**
5. **Configure logging and monitoring**

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Security Considerations

- All passwords are hashed using bcrypt
- JWT tokens are used for authentication
- Input validation using Pydantic models
- CORS is configured for frontend integration
- Rate limiting can be implemented using FastAPI middleware
- Environment variables for sensitive configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team or create an issue in the repository. 