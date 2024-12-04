from django.db import models
import uuid
from django.db import models
from django.utils.timezone import now, timedelta

def get_expiry_time():
    return now() + timedelta(hours=12)

class Token(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    ID_PROOF_CHOICES = [
        ('Aadhaar', 'Aadhaar'),
        ('PAN', 'PAN'),
        ('Passport', 'Passport'),
    ]

    PURPOSE_CHOICES = [
        ('Darshan', 'Darshan'),
        ('Donation', 'Donation'),
        ('Volunteering', 'Volunteering'),
    ]
    barcode = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(null=True,blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age = models.PositiveIntegerField()
    phone_number = models.CharField(max_length=15)
    id_proof_type = models.CharField(max_length=20, choices=ID_PROOF_CHOICES)
    id_proof_number = models.CharField(max_length=20)
    purpose_of_visit = models.CharField(max_length=30, choices=PURPOSE_CHOICES)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expired_at = models.DateTimeField(default=get_expiry_time)

    def __str__(self):
        return f"{self.name} - {self.barcode}"

class Queue(models.Model):
    queue_name = models.CharField(max_length=50, unique=True)  
    order = models.IntegerField(unique=True)

    def __str__(self):
        return self.queue_name

class QueueLog(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    scanned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('token', 'queue')

    def __str__(self):
        return f"Token {self.token.barcode} - {self.queue.queue_name}"
