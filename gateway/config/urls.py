import requests

from django.urls import path
from django.http import JsonResponse


def users(request):
    response = requests.get("http://127.0.0.1:8000/api/users/")
    return JsonResponse(response.json(), safe=False)


def products(request):
    response = requests.get("http://127.0.0.1:8001/api/products/")
    return JsonResponse(response.json(), safe=False)


def orders(request):
    response = requests.get("http://127.0.0.1:8002/api/orders/")
    return JsonResponse(response.json(), safe=False)
def payments(request):
    response = requests.get("http://127.0.0.1:8003/api/payment/")
    return JsonResponse(response.json(), safe=False)


urlpatterns = [
    path("api/users/", users),
    path("api/products/", products),
    path("api/orders/", orders),
    path("api/payment/", orders),
]