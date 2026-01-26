# Helpuvio - B2B Lead Data Marketplace

A production-ready B2B lead dataset marketplace. Sell downloadable CSV files containing company emails and phone numbers.

## Business Model

**Two Dataset Types:**
- **Phone Only** - Companies with verified phone numbers (lower price)
- **Email + Phone** - Companies with both email AND phone (premium price)

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 15+
- **ORM:** SQLAlchemy
- **Auth:** JWT + Google OAuth
- **Payments:** Paystack
- **Storage:** Cloudflare R2 / AWS S3

### Frontend
- **Framework:** React 18 + TypeScript
- **Styling:** TailwindCSS
- **Routing:** React Router 6
- **State:** Zustand
- **HTTP:** Axios

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
cd helpuvio

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit .env files with your credentials
# - Add Paystack keys
# - Add R2/S3 credentials (optional for local dev)

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access the app
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
# Database: postgresql://postgres:postgres@localhost:5432/helpuvio
```

### Option 2: Manual Setup

#### Database Setup

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE helpuvio;

# Connect to database
\c helpuvio

# Run schema
\i database/schema.sql
```

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations (if using Alembic)
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy and configure environment
cp .env.example .env
# Edit .env with your API URL

# Start development server
npm run dev
```

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/helpuvio

# JWT
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Paystack
PAYSTACK_SECRET_KEY=sk_test_xxx
PAYSTACK_PUBLIC_KEY=pk_test_xxx

# File Storage (Cloudflare R2)
R2_ENDPOINT=https://xxx.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=helpuvio-datasets

# Frontend URL
FRONTEND_URL=http://localhost:5173

# Environment
ENVIRONMENT=development
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
VITE_PAYSTACK_PUBLIC_KEY=pk_test_xxx
```

## API Endpoints

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user

### Datasets
- `GET /datasets` - List published datasets (with filters)
- `GET /datasets/{slug}` - Get dataset detail
- `GET /datasets/categories` - List categories

### Purchases
- `POST /purchases` - Create purchase (returns Paystack URL)
- `GET /purchases/my-purchases` - Get user's purchases
- `GET /purchases/{id}/verify` - Verify payment status

### Downloads
- `GET /downloads/{purchase_id}` - Get signed download URL

### Admin
- `POST /admin/login` - Admin login
- `GET /admin/dashboard` - Dashboard stats
- `GET /admin/datasets` - List all datasets
- `POST /admin/datasets` - Create dataset
- `PATCH /admin/datasets/{id}` - Update dataset
- `POST /admin/datasets/{id}/publish` - Publish dataset
- `GET /admin/purchases` - List all purchases
- `POST /admin/purchases/{id}/refund` - Issue refund
- `GET /admin/users` - List users

### Webhooks
- `POST /webhooks/paystack` - Paystack webhook handler

## Database Schema

### Core Tables

- **users** - User accounts (from existing schema)
- **datasets** - Products for sale
- **purchases** - Order records
- **download_logs** - Download audit trail
- **admin_users** - Admin accounts
- **categories** - Dataset categories (from existing schema)

### Key Fields

**datasets:**
- `enrichment_level`: 'phone_only' or 'email_and_phone'
- `price_cents`: Price in smallest currency unit
- `is_published`: Whether dataset is available for purchase

**purchases:**
- `status`: 'pending', 'paid', 'failed', 'refunded'
- `paystack_reference`: Unique payment reference

## Deployment

### Railway (Backend)

1. Create new project on Railway
2. Connect GitHub repository
3. Add PostgreSQL service
4. Set environment variables
5. Deploy

### Vercel (Frontend)

1. Import project on Vercel
2. Set `VITE_API_URL` to your Railway URL
3. Deploy

### Cloudflare R2 (File Storage)

1. Create R2 bucket: `helpuvio-datasets`
2. Create API token with read/write access
3. Add credentials to backend `.env`

## Paystack Integration

### Setup

1. Create Paystack account at paystack.com
2. Get API keys from dashboard
3. Add webhook URL: `https://your-api.com/webhooks/paystack`
4. Add keys to environment variables

### Payment Flow

1. User clicks "Purchase" on dataset page
2. Backend creates Purchase record (status: pending)
3. Backend initializes Paystack transaction
4. User is redirected to Paystack checkout
5. After payment, Paystack sends webhook
6. Backend verifies signature and updates purchase status
7. User can now download CSV

## File Storage

### Uploading Datasets (Admin)

1. Prepare CSV with required columns
2. Upload via admin panel
3. CSV is stored in R2 bucket
4. Dataset record is created with file path

### Downloading (Users)

1. User has paid purchase
2. Backend verifies ownership
3. Backend generates signed URL (expires in 1 hour)
4. User downloads directly from R2

## Security

- JWT tokens with 15-minute expiry
- Refresh tokens stored server-side
- Webhook signature verification
- Purchase ownership validation
- Admin role separation
- Audit logging

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Adding New Dataset Fields

1. Update `dataset_fields` table
2. Update CSV template
3. Update sample preview generation

## Support

For issues, contact: support@helpuvio.com

## License

Proprietary. All rights reserved.
