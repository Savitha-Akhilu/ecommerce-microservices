from django.urls import path

from .views import (
    OrderListCreateView,
    OrderDetailView,
    UserOrderListView
)

urlpatterns = [
    path('orders/', OrderListCreateView.as_view()),
    path('orders/<int:pk>/', OrderDetailView.as_view()),
    path('users/<int:pk>/orders/', UserOrderListView.as_view()),
]