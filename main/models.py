from django.db import models
from django.utils import timezone

class Member(models.Model):
    full_name = models.CharField(max_length=255)
    birthday = models.DateField(null=True)
    email = models.EmailField(unique=True, null=True)
    phone = models.CharField(max_length=15)
    start_date = models.DateField()
    end_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    nfc_tag_uid = models.CharField(max_length=50, unique=True, null=True, blank=True) 
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)  

    class Meta:
        db_table = 'member'

class Price(models.Model):
    name = models.CharField(max_length=255)
    duration = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)  

    class Meta:
        db_table = 'price'

class PaymentLog(models.Model):
    MEMBERSHIP_TYPE_CHOICES = [
        ('new', 'New'),
        ('extended', 'Extended'),
    ]

    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_logs')  # Member can be null if deleted
    member_name = models.CharField(max_length=255)  # Store member's full name directly
    duration = models.IntegerField()  # Store the duration in months
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Store the price directly
    membership_type = models.CharField(max_length=10, choices=MEMBERSHIP_TYPE_CHOICES, default='new') 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_log'

class NFCTag(models.Model):
    tag_id = models.CharField(max_length=255, unique=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'nfc_tag'

    def __str__(self):
        return self.tag_id