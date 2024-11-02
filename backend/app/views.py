# temple/views.py
from rest_framework.views import APIView
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.utils.timezone import now,make_aware
from datetime import datetime
from .models import Token, Queue, QueueLog
from .serializers import TokenSerializer, QueueSerializer, QueueLogSerializer, ReportSerializer
import pytz
from openpyxl import Workbook
from rest_framework.exceptions import NotFound
from datetime import timedelta
from openpyxl.styles import NamedStyle

IST = pytz.timezone('Asia/Kolkata')

class GenerateTokenView(APIView):
    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.save()

            created_at_ist = token.issued_at.astimezone(IST)
            expired_at_ist = token.expired_at.astimezone(IST)
            return Response({'barcode': str(token.barcode),
                'created_at': created_at_ist.strftime('%Y-%m-%d %H:%M:%S'),
                'expired_at': expired_at_ist.strftime('%Y-%m-%d %H:%M:%S'),
                'first_name':token.first_name,
                'last_name':token.last_name},
                status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class GetTokenView(APIView):
    def get(self, request, barcode):
        try:
            token = Token.objects.get(barcode=barcode)
            return Response({
                'first_name': token.first_name,
                'last_name': token.last_name,
                'purpose_of_visit': token.purpose_of_visit,
                'issued_at': token.issued_at,
                'expired_at': token.expired_at,
            })
        except Token.DoesNotExist:
            raise NotFound('Token not found.')

class QueueListView(APIView):                       
    def get(self, request):
        queues = Queue.objects.all().order_by('order')
        serializer = QueueSerializer(queues, many=True)
        return Response(serializer.data)
    def post(self,request):
        serializer = QueueSerializer(data= request.data)
        if serializer.is_valid():
            queue = serializer.save()
            return Response(QueueSerializer(queue).data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ScanTokenView(APIView):
    """
    Validates and logs a token at a specific queue, ensuring sequential entry.
    """
    def post(self, request):
        barcode = request.data.get('barcode')
        queue_id = request.data.get('queue_id')

        try:
            token = Token.objects.get(barcode=barcode)
        except Token.DoesNotExist:
            return Response({'error': 'Token not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            queue = Queue.objects.get(id=queue_id)
        except Queue.DoesNotExist:
            return Response({'error': 'Queue not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the token is expired or already used
        if token.is_used:
            raise ValidationError("This token has already been used.")
        if token.expired_at < now():
            raise ValidationError("This token has expired.")

        # Verify if the token is following the correct sequence
        required_previous_queues = Queue.objects.filter(order__lt=queue.order).order_by('order')

        for previous_queue in required_previous_queues:
            if not QueueLog.objects.filter(token=token, queue=previous_queue).exists():
                raise ValidationError(
                    f"Token must pass through {previous_queue.queue_name} before entering {queue.queue_name}."
                )

        # Log the current queue entry
        QueueLog.objects.create(token=token, queue=queue)

        # Mark the token as used if it passes the final queue
        if queue.order == Queue.objects.count():
            token.is_used = True
            token.save()

        return Response({'message': 'Token scanned successfully'}, status=status.HTTP_200_OK)
    
class ValidateTokenView(APIView):
    def post(self, request):
        barcode = request.data.get('barcode')
        queue_id = request.data.get('queue_id')

        if not barcode or not queue_id:
            raise ValidationError('Both barcode and queue_id are required.')

        # Check if the token exists
        try:
            token = Token.objects.get(barcode=barcode)
        except Token.DoesNotExist:
            raise NotFound('Token not found.')

        # Check if the token is expired
        if token.expired_at < now():
            raise ValidationError('Token is expired.')

        # Check if the queue exists
        try:
            queue = Queue.objects.get(id=queue_id)
        except Queue.DoesNotExist:
            raise ValidationError('Invalid queue selected.')

        # Check if the token has already been scanned for this queue
        if QueueLog.objects.filter(token=token, queue=queue).exists():
            raise ValidationError(f'Token has already been scanned at {queue.queue_name}.')

        # Validate queue sequence
        previous_queues = Queue.objects.filter(order__lt=queue.order).order_by('order')
        for prev_queue in previous_queues:
            if not QueueLog.objects.filter(token=token, queue=prev_queue).exists():
                raise ValidationError(f'Please complete {prev_queue.queue_name} before proceeding.')

        # Log the current queue scan
        QueueLog.objects.create(token=token, queue=queue)

        # Mark token as used if it's the final queue
        if not Queue.objects.filter(order__gt=queue.order).exists():
            token.is_used = True
            token.save()

        return Response({
            'message': f'Token validated for {queue.queue_name}.',
            'expires_at': token.expired_at,
        })

class ReportView(APIView):
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            raise ValidationError("Both start and end dates are required.")

        try:
            
            start_datetime = make_aware(datetime.strptime(start_date, "%Y-%m-%d"))

            # If start and end dates are the same as today, limit to the current time
            if start_date == end_date == now().strftime("%Y-%m-%d"):
                end_datetime = now()  # Use current time as end time
            else:
                # Use the end of the day (23:59:59) for other dates
                end_datetime = make_aware(datetime.strptime(end_date, "%Y-%m-%d")) + timedelta(days=1) - timedelta(seconds=1)

            # Query tokens issued within the range
            tokens = Token.objects.filter(issued_at__range=[start_datetime, end_datetime])

            # Generate the report
            report_data = {
                'total_issued': tokens.count(),
                'total_used': tokens.filter(is_used=True).count(),
                'total_expired': tokens.filter(expired_at__lt=now(), is_used=False).count(),
            }

            return Response(report_data, status=200)

        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD.")
        
def format_datetime(dt):
    """Convert a timezone-aware datetime to Excel-compatible format."""
    return dt.astimezone(None).strftime('%Y-%m-%d %H:%M:%S') if dt else ""



class GenerateReportView(APIView):
    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not start_date or not end_date:
            raise ValidationError('Both start date and end date are required.')

        # Parse dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise ValidationError('Invalid date format. Use YYYY-MM-DD.')

        # Create a new workbook
        workbook = Workbook()

        # 1. Sheet for Issued Tokens
        issued_sheet = workbook.active
        issued_sheet.title = "Issued Tokens"
        issued_sheet.append(["Barcode", "First Name", "Last Name", "Issued At"])
        issued_tokens = Token.objects.filter(issued_at__date__range=[start_date, end_date])
        for token in issued_tokens:
            issued_sheet.append([
                str(token.barcode), token.first_name, token.last_name, format_datetime(token.issued_at)
            ])

        # 2. Sheet for Used Tokens
        used_sheet = workbook.create_sheet(title="Used Tokens")
        used_sheet.append(["Barcode", "First Name", "Last Name", "Used At"])
        used_tokens = Token.objects.filter(is_used=True, issued_at__date__range=[start_date, end_date])
        for token in used_tokens:
            used_sheet.append([
                str(token.barcode), token.first_name, token.last_name, format_datetime(token.issued_at)
            ])

        # 3. Sheet for Expired Tokens
        expired_sheet = workbook.create_sheet(title="Expired Tokens")
        expired_sheet.append(["Barcode", "First Name", "Last Name", "Expired At"])
        expired_tokens = Token.objects.filter(expired_at__lt=now(), issued_at__date__range=[start_date, end_date])
        for token in expired_tokens:
            expired_sheet.append([
                str(token.barcode), token.first_name, token.last_name, format_datetime(token.expired_at)
            ])

        # 4. Sheets for Each Counter (Counter1, Counter2, etc.)
        counters = Queue.objects.all()
        for counter in counters:
            counter_sheet = workbook.create_sheet(title=counter.queue_name)
            counter_sheet.append(["Token Barcode", "First Name", "Scanned At"])
            logs = QueueLog.objects.filter(queue=counter, scanned_at__date__range=[start_date, end_date])
            for log in logs:
                token = log.token
                counter_sheet.append([
                    str(token.barcode), token.first_name, format_datetime(log.scanned_at)
                ])

        # 5. Combined Sheet with All Details
        combined_sheet = workbook.create_sheet(title="Combined Report")
        combined_sheet.append([
            "Barcode", "First Name", "Last Name", "Issued At", 
            "Used", "Expired", "Counter1", "Counter2", "Counter3", "Counter4"
        ])
        for token in issued_tokens:
            row = [
                str(token.barcode), token.first_name, token.last_name, 
                format_datetime(token.issued_at), 
                "Yes" if token.is_used else "No", 
                "Yes" if token.expired_at < now() else "No"
            ]

            # Add counter information
            for counter in counters:
                entered = QueueLog.objects.filter(
                    queue=counter, token=token, scanned_at__date__range=[start_date, end_date]
                ).exists()
                row.append("Yes" if entered else "No")

            combined_sheet.append(row)

        # Prepare the response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="report_{now().strftime("%Y%m%d%H%M%S")}.xlsx"'

        workbook.save(response)
        return response

class SummaryReportView(APIView):
    def get(self, request):
        # Get date range from query parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not start_date or not end_date:
            raise ValidationError('Start date and end date are required.')

        # Parse dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise ValidationError('Invalid date format. Use YYYY-MM-DD.')

        # Calculate summary metrics within the given date range
        total_issued = Token.objects.filter(issued_at__date__range=[start_date, end_date]).count()
        total_used = Token.objects.filter(is_used=True, issued_at__date__range=[start_date, end_date]).count()
        total_expired = Token.objects.filter(expired_at__lt=now(), issued_at__date__range=[start_date, end_date]).count()

        counter_stats = {
            queue.queue_name: QueueLog.objects.filter(queue=queue, scanned_at__date__range=[start_date, end_date]).count()
            for queue in Queue.objects.all()
        }

        return Response({
            'total_issued': total_issued,
            'total_used': total_used,
            'total_expired': total_expired,
            'counter_stats': counter_stats,
        })

