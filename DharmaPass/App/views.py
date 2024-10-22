from rest_framework import viewsets, status
from rest_framework.response import Response
from django.utils import timezone
from .models import Pilgrim
from .serializers import PilgrimSerializer, EntryPointSerializer
from datetime import timedelta
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status

class PilgrimViewSet(viewsets.ModelViewSet):
    queryset = Pilgrim.objects.all()
    serializer_class = PilgrimSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            aadhar_number = serializer.validated_data.get('aadhar_number')
            
            # Check if a record for this Aadhar number was created within the last 24 hours
            recent_record = Pilgrim.objects.filter(
                aadhar_number=aadhar_number,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).exists()
            
            if recent_record:
                return Response(
                    {"error": "A pilgrim cannot get a new token within 24 hours using the same Aadhar number."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save the pilgrim and generate a unique code
            pilgrim = serializer.save()

            return Response(
                {
                    "message": "Pilgrim token generated successfully.",
                    "unique_code": str(pilgrim.unique_id),
                    "valid_until": pilgrim.valid_until
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



from rest_framework import views, status
from rest_framework.response import Response
from .models import Pilgrim
from .serializers import EntryPointSerializer

class EntryPointView(views.APIView):
    def post(self, request, entry_level):
        serializer = EntryPointSerializer(data=request.data)

        if serializer.is_valid():
            unique_code = serializer.validated_data['unique_code']
            
            try:
                # Retrieve the existing Pilgrim record by the unique_code
                pilgrim = Pilgrim.objects.get(unique_id=unique_code)
            except Pilgrim.DoesNotExist:
                return Response({"error": "Pilgrim not found."}, status=status.HTTP_404_NOT_FOUND)

            # Validate and update the fields based on the entry level from the URL
            if entry_level == 1:
                print('1'*20)
                if not pilgrim.compartment_1:
                    pilgrim.compartment_1 = True
                else:
                    return Response({"error": "Entry 1 is already marked as True."}, status=status.HTTP_400_BAD_REQUEST)

            elif entry_level == 2:
                print('2'*20)
                if pilgrim.compartment_1 and not pilgrim.compartment_2:
                    pilgrim.compartment_2 = True
                elif not pilgrim.compartment_1:
                    return Response({"error": "Entry 1 must be true to proceed to Entry 2."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"error": "Entry 2 is already marked as True."}, status=status.HTTP_400_BAD_REQUEST)

            elif entry_level == 3:
                print('3'*20)
                if pilgrim.compartment_1 and pilgrim.compartment_2 and not pilgrim.compartment_3:
                    pilgrim.compartment_3 = True
                elif not pilgrim.compartment_1 or not pilgrim.compartment_2:
                    return Response({"error": "Entry 1 and Entry 2 must be true to proceed to Entry 3."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"error": "Entry 3 is already marked as True."}, status=status.HTTP_400_BAD_REQUEST)

            elif entry_level == 4:
                print('4'*20)
                if pilgrim.compartment_1 and pilgrim.compartment_2 and pilgrim.compartment_3 and not pilgrim.compartment_4:
                    pilgrim.compartment_4 = True
                elif not (pilgrim.compartment_1 and pilgrim.compartment_2 and pilgrim.compartment_3):
                    return Response({"error": "Entry 1, Entry 2, and Entry 3 must be true to proceed to Entry 4."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"error": "Entry 4 is already marked as True."}, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response({"error": "Invalid entry level."}, status=status.HTTP_400_BAD_REQUEST)

            # Save the updated pilgrim record
            pilgrim.save()

            return Response({"message": "Success, entry granted."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# from rest_framework import views, status
# from rest_framework.response import Response
# from .models import Pilgrim
# from datetime import datetime

# class ReportView(views.APIView):
#     def post(self, request):
#         # Get start_date and end_date from the request body
#         start_date = request.data.get('start_date')
#         end_date = request.data.get('end_date')

#         # Parse the dates if needed
#         try:
#             start_date = datetime.strptime(start_date, '%Y-%m-%d')
#             end_date = datetime.strptime(end_date, '%Y-%m-%d')
#         except ValueError:
#             return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

#         # Retrieve Pilgrim records based on valid_until date
#         pilgrims = Pilgrim.objects.filter(valid_until__range=[start_date, end_date])
        
#         # Initialize counters
#         total_tokens_generated = pilgrims.count()
#         total_tokens_used = pilgrims.filter(is_expired=False).count()
#         total_tokens_expired = pilgrims.filter(is_expired=True).count()
#         total_tokens_not_used = total_tokens_generated - total_tokens_used

#         # Create the report data
#         report_data = {
#             "total_tokens_generated": total_tokens_generated,
#             "total_tokens_used": total_tokens_used,
#             "total_tokens_expired": total_tokens_expired,
#             "total_tokens_not_used": total_tokens_not_used,
#             "details": [
#                 {
#                     "unique_id": pilgrim.unique_id,
#                     "name": pilgrim.name,
#                     "aadhar_number": pilgrim.aadhar_number,
#                     "phone_number": pilgrim.phone_number,
#                     "valid_until": pilgrim.valid_until,
#                     "is_expired": pilgrim.is_expired,
#                     "compartment_1": pilgrim.compartment_1,
#                     "compartment_2": pilgrim.compartment_2,
#                     "compartment_3": pilgrim.compartment_3,
#                     "compartment_4": pilgrim.compartment_4,
#                 }
#                 for pilgrim in pilgrims
#             ]
#         }
#         print(report_data, 'reports dataaaaaaaaaaaaaa')
#         return Response(report_data, status=status.HTTP_200_OK)


from rest_framework import views, status
from rest_framework.response import Response
from .models import Pilgrim
from datetime import datetime

class ReportView(views.APIView):
    def post(self, request):
        # Get start_date and end_date from the request body
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        # Parse the dates if needed
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve Pilgrim records based on valid_until date
        pilgrims = Pilgrim.objects.filter(valid_until__range=[start_date, end_date])

        # Initialize counters
        total_tokens_generated = pilgrims.count()
        total_tokens_used = pilgrims.filter(is_expired=False).count()
        total_tokens_expired = pilgrims.filter(is_expired=True).count()
        total_tokens_not_used = total_tokens_generated - total_tokens_used
        
        # Count compartments
        tokens_passed_compartment_1 = pilgrims.filter(compartment_1=True).count()
        tokens_passed_compartment_2 = pilgrims.filter(compartment_2=True).count()
        tokens_passed_compartment_3 = pilgrims.filter(compartment_3=True).count()
        tokens_passed_compartment_4 = pilgrims.filter(compartment_4=True).count()

        # Create the report data
        report_data = {
            "total_tokens_generated": total_tokens_generated,
            "total_tokens_used": total_tokens_used,
            "total_tokens_expired": total_tokens_expired,
            "total_tokens_not_used": total_tokens_not_used,
            "tokens_passed_compartment_1": tokens_passed_compartment_1,
            "tokens_passed_compartment_2": tokens_passed_compartment_2,
            "tokens_passed_compartment_3": tokens_passed_compartment_3,
            "tokens_passed_compartment_4": tokens_passed_compartment_4,
            # "details": [
            #     {
            #         "unique_id": pilgrim.unique_id,
            #         "name": pilgrim.name,
            #         "aadhar_number": pilgrim.aadhar_number,
            #         "phone_number": pilgrim.phone_number,
            #         "valid_until": pilgrim.valid_until,
            #         "is_expired": pilgrim.is_expired,
            #         "compartment_1": pilgrim.compartment_1,
            #         "compartment_2": pilgrim.compartment_2,
            #         "compartment_3": pilgrim.compartment_3,
            #         "compartment_4": pilgrim.compartment_4,
            #     }
            #     for pilgrim in pilgrims
            # ]
        }

        return Response(report_data, status=status.HTTP_200_OK)

