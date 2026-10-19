import os
import requests

from decimal import Decimal
from dotenv import load_dotenv

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Order, OrderItem
from .serializers import OrderSerializer


load_dotenv()

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL")


class OrderListCreateView(APIView):

    # GET: View all orders except cancelled orders
    def get(self, request):

        orders = Order.objects.exclude(status='CANCELLED')

        serializer = OrderSerializer(orders, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # POST: Create an order
    def post(self, request):

        user_id = request.data.get("user_id")
        items = request.data.get("items")

        if not user_id:
            return Response(
                {"error": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not items or not isinstance(items, list):
            return Response(
                {"error": "items must be a list"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check whether the user exists
        try:
            user_url = f"{USER_SERVICE_URL}{user_id}/"
            print("Calling User Service:", user_url,flush=True)

            user_response = requests.get(f"{USER_SERVICE_URL}{user_id}/",
                timeout=5
            )
            # print("User Service status:", user_response.status_code)
            # print("User Service response:", user_response.text)

        except requests.RequestException:
            print("User Service error:", str(e))
            return Response(
                {"error": "User Service is unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        if user_response.status_code != 200:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        total = Decimal("0.00")
        validated_items = []

        # Validate products and calculate total
        for item in items:

            product_id = item.get("product_id")
            quantity = item.get("quantity")

            if product_id is None or quantity is None:
                return Response(
                    {"error": "product_id and quantity are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                return Response(
                    {"error": "Quantity must be a positive integer"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if quantity <= 0:
                return Response(
                    {"error": "Quantity must be greater than 0"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check whether the product exists
            try:
                product_response = requests.get(
                    f"{PRODUCT_SERVICE_URL}{product_id}/",
                    timeout=5
                )
            except requests.RequestException:
                return Response(
                    {"error": "Product Service is unavailable"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            if product_response.status_code != 200:
                return Response(
                    {"error": f"Product {product_id} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            product = product_response.json()

            if product["stock"] < quantity:
                return Response(
                    {
                        "error": f"Insufficient stock for product {product_id}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            price = Decimal(str(product["price"]))
            total += price * quantity

            validated_items.append({
                "product_id": product_id,
                "quantity": quantity,
                "price": price
            })

        # Create the order
        order = Order.objects.create(
            user_id=user_id,
            total=total,
            status="CONFIRMED"
        )

        # Create the order items
        for item in validated_items:
            OrderItem.objects.create(
                order=order,
                product_id=item["product_id"],
                quantity=item["quantity"],
                price=item["price"]
            )

        serializer = OrderSerializer(order)

        # return Response(
        #     serializer.data,
        #     status=status.HTTP_201_CREATED
        # )
        return Response(
    {
        "message": "Order placed successfully",
        "id": order.id,
        "user_id": order.user_id,
        "total": str(order.total),
        "status": order.status
    },
    status=status.HTTP_201_CREATED
)


class OrderDetailView(APIView):

    # GET: View one order
    def get(self, request, pk):

        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = OrderSerializer(order)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    # PATCH: Update order details
    def patch(self, request, pk):

        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if order.status == "CANCELLED":
            return Response(
                {"error": "Cancelled order cannot be updated"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrderSerializer(
            order,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # DELETE: Cancel order
    def delete(self, request, pk):

        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if order.status == "CANCELLED":
            return Response(
                {"error": "Order is already cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = "CANCELLED"
        order.save(update_fields=["status"])

        return Response(
            {"message": "Order cancelled successfully"},
            status=status.HTTP_200_OK
        )


class UserOrderListView(APIView):

    def get(self, request, pk):

        orders = Order.objects.filter(user_id=pk)

        serializer = OrderSerializer(orders, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )