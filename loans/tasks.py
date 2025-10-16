import os
from celery import shared_task
import pandas as pd
from decimal import Decimal
from django.db import transaction
from loans.models import Customer, Loan

DATA_DIR = '/code/data'

@shared_task(bind=True)
def ingest_excel_files(self):
    customer_file = os.path.join(DATA_DIR, 'customer_data.xlsx')
    loan_file = os.path.join(DATA_DIR, 'loan_data.xlsx')

    if not os.path.exists(customer_file):
        raise FileNotFoundError(f"{customer_file} not found")
    if not os.path.exists(loan_file):
        raise FileNotFoundError(f"{loan_file} not found")

    df_customers = pd.read_excel(customer_file, engine='openpyxl')
    df_loans = pd.read_excel(loan_file, engine='openpyxl')

    df_customers.columns = [c.strip().lower().replace(' ', '_') for c in df_customers.columns]
    df_loans.columns = [c.strip().lower().replace(' ', '_') for c in df_loans.columns]

    with transaction.atomic():
        for _, row in df_customers.iterrows():
            cid = int(row.get('customer_id'))
            first = str(row.get('first_name', '')).strip()
            last = str(row.get('last_name', '')).strip()
            phone = str(row.get('phone_number', '')).strip()
            monthly_salary = Decimal(row.get('monthly_salary') or 0)
            approved_limit = row.get('approved_limit')
            current_debt = Decimal(row.get('current_debt') or 0)
            if approved_limit is None or pd.isna(approved_limit):
                approved_limit = monthly_salary * 36
            else:
                approved_limit = Decimal(approved_limit)

            Customer.objects.update_or_create(
                customer_id=cid,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'phone_number': phone,
                    'monthly_salary': monthly_salary,
                    'approved_limit': approved_limit,
                    'current_debt': current_debt,
                }
            )

        for _, row in df_loans.iterrows():
            cid = int(row.get('customer_id'))
            loanid = int(row.get('loan_id'))
            loan_amount = Decimal(row.get('loan_amount') or 0)
            tenure = int(row.get('tenure') or 0)
            interest_rate = Decimal(row.get('interest_rate') or 0)
            monthly_repayment = row.get('monthly_repayment')
            if monthly_repayment is None or pd.isna(monthly_repayment):
                monthly_repayment = calculate_monthly_installment(loan_amount, interest_rate, tenure)
            else:
                monthly_repayment = Decimal(monthly_repayment)

            emis_paid_on_time = int(row.get('emis_paid_on_time') or 0)

            start_date = row.get('start_date')
            end_date = row.get('end_date')

            customer = Customer.objects.filter(customer_id=cid).first()
            if not customer:
                continue

            Loan.objects.update_or_create(
                loan_id=loanid,
                defaults={
                    'customer': customer,
                    'loan_amount': loan_amount,
                    'tenure': tenure,
                    'interest_rate': interest_rate,
                    'monthly_repayment': monthly_repayment,
                    'emis_paid_on_time': emis_paid_on_time,
                    'start_date': start_date,
                    'end_date': end_date
                }
            )

    return {'status': 'ok'}

def calculate_monthly_installment(P, annual_rate, n_months):
    if n_months == 0:
        return Decimal(0)
    r = (Decimal(annual_rate) / Decimal(100)) / Decimal(12)
    P = Decimal(P)
    if r == 0:
        return (P / Decimal(n_months)).quantize(Decimal('0.01'))
    numerator = P * r * (1 + r) ** n_months
    denominator = ((1 + r) ** n_months) - 1
    emi = numerator / denominator
    return emi.quantize(Decimal('0.01'))
