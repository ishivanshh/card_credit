from django.db import models

class Customer(models.Model):
    customer_id = models.IntegerField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2)
    approved_limit = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    current_debt = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)
    age = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.customer_id} - {self.first_name} {self.last_name}"

class Loan(models.Model):
    loan_id = models.IntegerField(unique=True)
    customer = models.ForeignKey(Customer, related_name='loans', on_delete=models.CASCADE)
    loan_amount = models.DecimalField(max_digits=14, decimal_places=2)
    tenure = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=6, decimal_places=2)
    monthly_repayment = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    emis_paid_on_time = models.IntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Loan {self.loan_id} ({self.customer.customer_id})"
