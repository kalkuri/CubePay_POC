import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

class Pilgrim(models.Model):
    # Unique field that will be converted into a barcode by the frontend team
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    aadhar_number = models.CharField(max_length=12, unique=True)
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=gender_choices)
    phone_number = models.CharField(max_length=15, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField()
    is_expired = models.BooleanField(default=False)
    compartment_1 = models.BooleanField(default=False)
    compartment_2 = models.BooleanField(default=False)
    compartment_3 = models.BooleanField(default=False)
    compartment_4 = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Check if the instance is new or an update
        if self.pk is None:
            # New instance: check for recent record
            recent_record = Pilgrim.objects.filter(
                aadhar_number=self.aadhar_number,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).exists()
            
            if recent_record:
                raise ValidationError("A pilgrim cannot get a new token within 24 hours using the same Aadhar number.")
        
        # Set the token validity for 12 hours if not set
        if not self.valid_until:
            self.valid_until = self.created_at + timedelta(hours=12)
        
        # Check if the token has expired
        if timezone.now() > self.valid_until:
            self.is_expired = True
        
        super().save(*args, **kwargs)
