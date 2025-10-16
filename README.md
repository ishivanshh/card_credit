# Credit Approval System

## Setup
1. Place `customer_data.xlsx` and `loan_data.xlsx` in `./data/`.
2. Copy `.env.example` to `.env` and edit if needed.
3. Build and run:

```bash
docker-compose up --build
```

What runs:
- `db` Postgres
- `redis`
- `web` gunicorn Django app on port 8000
- `celery_worker` consumes tasks
- `initializer` enqueues ingestion task; it will exit after enqueuing

API base: `http://localhost:8000/api/`

Endpoints:
- `POST /api/register` — register new customer
- `POST /api/check-eligibility` — check loan eligibility
- `POST /api/create-loan` — create approved loan
- `GET /api/view-loan/{loan_id}` — view single loan
- `GET /api/view-loans/{customer_id}` — view loans for customer

```
 Python
shivanshsaxena@Shivanshs-MacBook-Air credit_approval_project % curl -X POST http://localhost:8000/api/register \   
  -H "Content-Type: application/json" \
  -d '{
        "first_name": "Shivansh",
        "last_name": "Saxena",
        "phone_number": "9876543210",
        "age": 20,  
        "monthly_income": 60000,
        "approved_limit": 200000
      }'

{"customer_id":303,"name":"Shivansh Saxena","age":20,"monthly_income":"60000.00","approved_limit":"2200000","phone_number":"9876543210"}%  ```