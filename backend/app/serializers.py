# temple/serializers.py
from rest_framework import serializers
from .models import Token, Queue, QueueLog
from django.utils.timezone import now

class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = "__all__"
        read_only_fields = ['barcode', 'issued_at', 'is_used', 'expired_at']

    def validate_aadhar(self, value):
        if not value.isdigit() or len(value) != 12:
            raise serializers.ValidationError("Aadhar number must be exactly 12 digits.")
        return value

    def validate_phone_number(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits.")
        return value
    def validate_age(self,value):
        if value <= 0 or value > 100:
            raise serializers.ValidationError("Please enter proper age")
        return value 
    

class QueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = ['id', 'queue_name', 'order']

class QueueLogSerializer(serializers.ModelSerializer):
    token = serializers.SlugRelatedField(slug_field='barcode', queryset=Token.objects.all())
    queue = serializers.SlugRelatedField(slug_field='queue_name', queryset=Queue.objects.all())

    class Meta:
        model = QueueLog
        fields = ['token', 'queue', 'scanned_at']
        read_only_fields = ['scanned_at']

class ReportSerializer(serializers.Serializer):
    total_issued = serializers.IntegerField()
    total_used = serializers.IntegerField()
    total_expired = serializers.IntegerField()
