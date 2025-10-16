from rest_framework import serializers
from .models import Customer, Loan

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['customer_id', 'first_name', 'last_name', 'age', 'phone_number', 'monthly_salary', 'approved_limit', 'current_debt']

class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    age = serializers.IntegerField()
    monthly_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    phone_number = serializers.CharField()

class CheckEligibilitySerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=6, decimal_places=2)
    tenure = serializers.IntegerField()

class LoanSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    class Meta:
        model = Loan
        fields = ['loan_id', 'customer', 'loan_amount', 'interest_rate', 'monthly_repayment', 'tenure']
