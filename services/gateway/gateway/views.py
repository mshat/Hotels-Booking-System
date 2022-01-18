from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import requests
from .env import get_uri
import sys
sys.path.append("..")
from my_modules import my_requests
import json


class PersonView(APIView):
    def get(self, request):
        reservation_service_uri = get_uri('reservation')
        reservation_service_uri.path = 'reservations'
        reservations_response = requests.get(str(reservation_service_uri))

        loyalty_service_uri = get_uri('loyalty')
        loyalty_response = requests.get(str(loyalty_service_uri), headers={"X-User-Name": "Test Max"})
        data = {
            "reservations": reservations_response.json(),
            "loyalty": loyalty_response.json()
        }
        return Response(status=status.HTTP_200_OK, data=data)


class HotelsListView(APIView):
    def get(self, request):
        reservation_service_uri = get_uri('reservation')
        reservation_service_uri.path = 'hotels'
        if request.META['QUERY_STRING']:
            reservation_service_uri.query = request.META['QUERY_STRING']
        else:
            raise Exception()

        response = requests.get(str(reservation_service_uri))
        return Response(status=status.HTTP_200_OK, data=response.json())


class ReservationsListView(APIView):
    def get(self, request):
        reservation_service_uri = get_uri('reservation')
        reservation_service_uri.path = 'reservations'
        response = requests.get(str(reservation_service_uri))
        return Response(status=status.HTTP_200_OK, data=response.json())

    def post(self, request):
        reservation_service_uri = get_uri('reservation')
        loyalty_service_uri = get_uri('loyalty')

        username = request.headers["x-user-name"]
        request_data = request.data
        hotel_uid = request_data["hotelUid"]
        start_date = request_data["startDate"]
        end_date = request_data["endDate"]

        # Запрос к Reservation Service для проверки, что такой отель существует
        try:
            reservation_service_uri.path = 'hotels'
            hotels_get_response = requests.get(str(reservation_service_uri))
        except Exception as e:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE,
                            data={'message': 'Reservation Service unavailable'})
        if hotels_get_response.status_code == 503:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE,
                            data={'message': 'Reservation Service unavailable'})
        elif hotels_get_response.status_code == 200:
            hotels_get_response_data = hotels_get_response.json()

            hotel_found = False
            for hotel in hotels_get_response_data:
                if hotel_uid == hotel['hotelUid']:
                    hotel_found = True
                    break
            if not hotel_found:
                return Response(status=status.HTTP_404_NOT_FOUND, data={'message': 'Hotel not found'})

        # Запрос к Loyalty Service для увеличения счетчика бронирований
        try:
            loyalty_patch_response = requests.patch(str(loyalty_service_uri), headers={"X-User-Name": username})
        except Exception as e:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data={'message': 'Loyalty Service unavailable'})
        if loyalty_patch_response.status_code == 503:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data={'message': 'Loyalty Service unavailable'})

        reservation_service_uri.path = 'reservations'
        reservation_post_response = requests.post(
            str(reservation_service_uri),
            data=json.dumps({"hotelUid": hotel_uid, "startDate": start_date, "endDate": end_date}),
            headers={"Content-Type": "application/json", "x-user-name": username}
        )

        if reservation_post_response.status_code == 503:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data={'message': 'Loyalty Service unavailable'})

        return Response(status=status.HTTP_200_OK, data=reservation_post_response.json())


class ReservationView(APIView):
    def get(self, request, uid):
        reservation_service_uri = get_uri('reservation')
        reservation_service_uri.path = f'reservation/{uid}'

        response = requests.get(str(reservation_service_uri))
        return Response(status=status.HTTP_200_OK, data=response.json())

    def delete(self, request, uid):
        loyalty_service_uri = get_uri('loyalty')
        username = request.headers["x-user-name"]
        requests.delete(str(loyalty_service_uri), headers={"X-User-Name": username})

        reservation_service_uri = get_uri('reservation')
        reservation_service_uri.path = f"reservation/{uid}"
        reservation_get_request = my_requests.GetRequest(reservation_service_uri)
        reservation_response = reservation_get_request.send()
        reservation = reservation_response.json()

        payment_service_uri = get_uri('payment')
        payment_service_uri.path = f"payment/{reservation['payment_uid']}"
        payment_status_patch_request = my_requests.PatchRequest(payment_service_uri, data={"status": "CANCELED"})
        payment_status_patch_request.send()

        reservation_service_uri.path = f"reservation/{uid}"
        reservation_status_patch_request = my_requests.PatchRequest(reservation_service_uri, data={"status": "CANCELED"})
        reservation_status_patch_request.send()

        return Response(status=status.HTTP_204_NO_CONTENT)


class LoyaltyView(APIView):
    def get(self, request):
        loyalty_service_uri = get_uri('loyalty')
        username = request.headers["x-user-name"]
        response = requests.get(str(loyalty_service_uri), headers={"X-User-Name": username})
        return Response(status=status.HTTP_200_OK, data=response.json())


class PaymentsListView(APIView):
    def get(self, request):
        payment_service_uri = get_uri('payment')
        payment_service_uri.path = 'payments'

        response = requests.get(payment_service_uri)
        return Response(status=response.status_code, data=response.json())

    def post(self, request):
        payment_service_uri = get_uri('payment')
        payment_service_uri.path = f'payments'

        price = request.data['price']
        response = requests.post(str(payment_service_uri), data={'price': price})
        if response.status_code == 200:
            return Response(status=status.HTTP_200_OK, data=response.json())
        else:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE, data={'message': 'Payment service unavailable'})


class PaymentView(APIView):
    def get(self, request, uid):
        payment_service_uri = get_uri('payment')
        payment_service_uri.path = f'payment/{uid}'

        response = requests.get(str(payment_service_uri))
        return Response(status=status.HTTP_200_OK, data=response.json())

        




