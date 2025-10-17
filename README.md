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
 # Register response
curl -X POST http://localhost:8000/api/register \   
  -H "Content-Type: application/json" \
  -d '{
        "first_name": "Shivansh",
        "last_name": "Saxena",
        "phone_number": "9876543210",
        "age": 20,  
        "monthly_income": 60000,
        "approved_limit": 200000
      }'

{"customer_id":303,"name":"Shivansh Saxena","age":20,"monthly_income":"60000.00","approved_limit":"2200000","phone_number":"9876543210"}%  
```

curl -X POST http://localhost:8000/api/check-eligibility/ \
  -H "Content-Type: application/json" \
  -d '{
        "customer_id": 314,
        "monthly_income": 60000,
        "existing_loans": 1
      }'

{
  "customer_id": 314,
  "eligible": true,
  "max_loan_amount": "2200000",
  "reason": "Meets all eligibility criteria"
}



curl -X POST http://localhost:8000/api/create-loan/ \
  -H "Content-Type: application/json" \
  -d '{
        "customer_id": 314,
        "loan_amount": 1500000,
        "tenure_months": 24
      }'


{
  "loan_id": 102,
  "customer_id": 314,
  "loan_amount": "1500000.00",
  "tenure_months": 24,
  "status": "approved",
  "emi": "70000.00",
  "approved_on": "2025-10-17T17:30:00Z"
}


curl -X GET http://localhost:8000/api/view-loan/102/

{
  "loan_id": 102,
  "customer_id": 314,
  "loan_amount": "1500000.00",
  "tenure_months": 24,
  "status": "approved",
  "emi": "70000.00",
  "approved_on": "2025-10-17T17:30:00Z",
  "remaining_balance": "1400000.00"
}


curl -X GET http://localhost:8000/api/view-loans/314/


{
  "customer_id": 314,
  "loans": [
    {
      "loan_id": 102,
      "loan_amount": "1500000.00",
      "tenure_months": 24,
      "status": "approved",
      "emi": "70000.00",
      "approved_on": "2025-10-17T17:30:00Z",
      "remaining_balance": "1400000.00"
    },
    {
      "loan_id": 103,
      "loan_amount": "500000.00",
      "tenure_months": 12,
      "status": "closed",
      "emi": "45000.00",
      "approved_on": "2024-05-10T12:00:00Z",
      "remaining_balance": "0.00"
    }
  ]
}

# API END POINTS

http://localhost:8000/api/register
http://localhost:8000/api/check-eligibility
http://localhost:8000/api/create-loan
http://localhost:8000/api/view-loan/<loan_id>
http://localhost:8000/api/view-loans/<customer_id>
