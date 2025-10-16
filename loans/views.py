from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from django.shortcuts import get_object_or_404
from .models import Customer, Loan
from .serializers import (
    RegisterSerializer, CheckEligibilitySerializer,
    CustomerSerializer, LoanSerializer
)
from .tasks import calculate_monthly_installment

def round_nearest_lakh(x):
    lakh = Decimal(100000)
    return ( (x / lakh).quantize(Decimal('1')) * lakh )

class RegisterView(APIView):
    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        data = ser.validated_data
        monthly_income = Decimal(data['monthly_income'])
        approved_limit = round_nearest_lakh(monthly_income * Decimal(36))
        customer = Customer.objects.create(
            customer_id=0,
            first_name=data['first_name'],
            last_name=data['last_name'],
            age=data['age'],
            phone_number=data['phone_number'],
            monthly_salary=monthly_income,
            approved_limit=approved_limit,
            current_debt=Decimal(0)
        )
        customer.customer_id = customer.id
        customer.save()
        resp = {
            'customer_id': customer.customer_id,
            'name': f"{customer.first_name} {customer.last_name}",
            'age': customer.age,
            'monthly_income': str(customer.monthly_salary),
            'approved_limit': str(customer.approved_limit),
            'phone_number': customer.phone_number
        }
        return Response(resp, status=status.HTTP_201_CREATED)

class CheckEligibilityView(APIView):
    def post(self, request):
        ser = CheckEligibilitySerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        data = ser.validated_data
        customer = get_object_or_404(Customer, customer_id=data['customer_id'])

        loans = Loan.objects.filter(customer=customer)
        total_loans = loans.count()
        if total_loans == 0:
            on_time_pct = 100
        else:
            total_emis = sum([l.emis_paid_on_time for l in loans])
            total_expected = sum([l.tenure for l in loans]) or 1
            on_time_pct = (total_emis / total_expected) * 100

        from django.utils import timezone
        year = timezone.now().year
        activity_this_year = loans.filter(start_date__year=year).count()

        total_volume = sum([l.loan_amount for l in loans]) or Decimal(0)
        try:
            vol_score = min(100, (total_volume / (customer.approved_limit or Decimal(1))) * 100)
        except Exception:
            vol_score = 0

        score = (on_time_pct * 0.5) + (max(0, 100 - total_loans * 5) * 0.1) + (min(100, activity_this_year * 10) * 0.1) + ( (100 - vol_score) * 0.3 )
        score = max(0, min(100, score))

        sum_current_loans = sum([l.loan_amount for l in loans]) or Decimal(0)
        if sum_current_loans > customer.approved_limit:
            score = 0

        sum_emis = sum([l.monthly_repayment or Decimal(0) for l in loans]) or Decimal(0)
        if sum_emis > (customer.monthly_salary * Decimal('0.5')):
            approval = False
            reason = 'Existing EMIs exceed 50% of monthly income'
        else:
            approval = None
            reason = ''

        interest = Decimal(data['interest_rate'])
        corrected_interest = interest
        if score > 50:
            approval = True if approval is not False else False
        elif 30 < score <= 50:
            if interest >= Decimal('12'):
                approval = True
            else:
                corrected_interest = Decimal('12')
                approval = False
        elif 10 < score <= 30:
            if interest >= Decimal('16'):
                approval = True
            else:
                corrected_interest = Decimal('16')
                approval = False
        else:
            approval = False

        monthly_installment = calculate_monthly_installment(Decimal(data['loan_amount']), corrected_interest, int(data['tenure']))

        resp = {
            'customer_id': customer.customer_id,
            'credit_score': float(score),
            'approval': bool(approval),
            'interest_rate': float(interest),
            'corrected_interest_rate': float(corrected_interest),
            'tenure': data['tenure'],
            'monthly_installment': str(monthly_installment),
            'reason': reason
        }
        return Response(resp)

class CreateLoanView(APIView):
    def post(self, request):
        ser = CheckEligibilitySerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        data = ser.validated_data
        check_view = CheckEligibilityView()
        check_resp = check_view.post(request)
        if check_resp.status_code != 200:
            return check_resp
        payload = check_resp.data
        if not payload.get('approval'):
            return Response({'loan_id': None, 'customer_id': data['customer_id'], 'loan_approved': False, 'message': 'Not approved', 'monthly_installment': payload.get('monthly_installment')}, status=status.HTTP_400_BAD_REQUEST)

        customer = get_object_or_404(Customer, customer_id=data['customer_id'])
        from django.db import models
        max_loan = Loan.objects.aggregate(models.Max('loan_id'))['loan_id__max'] or 0
        new_loan_id = int(max_loan) + 1
        monthly_installment = Decimal(payload['monthly_installment'])
        loan = Loan.objects.create(
            loan_id=new_loan_id,
            customer=customer,
            loan_amount=Decimal(data['loan_amount']),
            tenure=data['tenure'],
            interest_rate=Decimal(payload['corrected_interest_rate']),
            monthly_repayment=monthly_installment
        )
        customer.current_debt = (customer.current_debt or Decimal(0)) + Decimal(data['loan_amount'])
        customer.save()

        return Response({'loan_id': loan.loan_id, 'customer_id': customer.customer_id, 'loan_approved': True, 'message': 'Loan approved', 'monthly_installment': str(monthly_installment)})

class ViewLoanView(APIView):
    def get(self, request, loan_id):
        loan = get_object_or_404(Loan, loan_id=loan_id)
        data = {
            'loan_id': loan.loan_id,
            'customer': {
                'id': loan.customer.customer_id,
                'first_name': loan.customer.first_name,
                'last_name': loan.customer.last_name,
                'phone_number': loan.customer.phone_number,
                'age': loan.customer.age,
            },
            'loan_amount': str(loan.loan_amount),
            'interest_rate': float(loan.interest_rate),
            'monthly_installment': str(loan.monthly_repayment),
            'tenure': loan.tenure
        }
        return Response(data)

class ViewLoansByCustomerView(APIView):
    def get(self, request, customer_id):
        customer = get_object_or_404(Customer, customer_id=customer_id)
        loans = Loan.objects.filter(customer=customer)
        items = []
        for l in loans:
            repayments_left = 0
            if l.start_date:
                from django.utils import timezone
                now = timezone.now().date()
                months_passed = (now.year - l.start_date.year) * 12 + (now.month - l.start_date.month)
                repayments_left = max(0, l.tenure - months_passed)
            items.append({
                'loan_id': l.loan_id,
                'loan_amount': str(l.loan_amount),
                'interest_rate': float(l.interest_rate),
                'monthly_installment': str(l.monthly_repayment),
                'repayments_left': repayments_left
            })
        return Response(items)
