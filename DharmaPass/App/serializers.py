from rest_framework import serializers
from .models import Pilgrim
import uuid
from django.utils import timezone
from datetime import timedelta

class PilgrimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pilgrim
        fields = ['name', 'aadhar_number', 'gender', 'phone_number']
        read_only_fields = ['unique_id', 'created_at', 'valid_until']

    def create(self, validated_data):
        # Generate a unique ID (or any other logic you need)
        unique_id = str(uuid.uuid4())
        # Set the current time and expiration time
        created_at = timezone.now()
        valid_until = created_at + timedelta(hours=12)

        # Create a new Pilgrim instance with the unique ID and timestamps
        pilgrim = Pilgrim.objects.create(
            unique_id=unique_id,
            created_at=created_at,
            valid_until=valid_until,
            **validated_data  # Unpack validated data for remaining fields
        )
        return pilgrim



class EntryPointSerializer(serializers.Serializer):
    unique_code = serializers.UUIDField()





