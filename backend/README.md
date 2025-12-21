# KrouAI Bakong Payment Backend

Flask API for handling Bakong KHQR payments.

## Setup

### 1. Install Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

### 2. Create Environment File

Create a `.env` file with your credentials:

```env
# Bakong KHQR Token (get from https://api-bakong.nbc.gov.kh/register)
BAKONG_TOKEN=your_bakong_token_here

# Your Bakong Account ID (found in Bakong app under profile)
BAKONG_ACCOUNT=your_name@acleda

# Supabase credentials (use SERVICE ROLE key, not anon key)
SUPABASE_URL=https://dzpriubbvgnraiuvxwgu.supabase.co
SUPABASE_KEY=your_supabase_service_role_key

# Server settings
FLASK_ENV=production
PORT=5000
```

### 3. Add Database Table

Run the SQL in `pending_payments.sql` in your Supabase SQL Editor.

### 4. Run the Server

**Development:**
```bash
python app.py
```

**Production (with Gunicorn):**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### `POST /api/create-payment`

Create a new KHQR payment QR code.

**Request:**
```json
{
    "user_id": "user-uuid-from-supabase",
    "package": "20",
    "currency": "KHR"
}
```

**Response:**
```json
{
    "success": true,
    "qr_string": "00020101021229...",
    "md5_hash": "abc123...",
    "deeplink": "https://bakong.page.link/...",
    "bill_number": "KROU1234567890",
    "credits": 20,
    "amount": 2000,
    "currency": "KHR"
}
```

### `POST /api/check-payment`

Check if a payment has been completed.

**Request:**
```json
{
    "md5_hash": "abc123..."
}
```

**Response:**
```json
{
    "status": "PAID",
    "credits_added": 20,
    "message": "Successfully added 20 credits!"
}
```

## Deployment

### ⚠️ Important: Cambodia Server Required

The Bakong API requires your server to be located in Cambodia. Options:

1. **JESERVER** - https://jeserver.com
2. **CAMBOSERVER** - https://camboserver.com
3. **Any Cambodia-based VPS**

### Deploy with Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Credit Packages

| Package | Credits | Price (KHR) | Price (USD) |
|---------|---------|-------------|-------------|
| 20      | 20      | 2,000៛      | $0.50       |
| 50      | 50      | 4,500៛      | $1.10       |
| 100     | 100     | 8,000៛      | $2.00       |

