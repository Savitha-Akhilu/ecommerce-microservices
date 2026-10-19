from django.urls import path
from products.views import ProductList, ProductDetailView

urlpatterns = [
    path('products/', ProductList.as_view()),
    path('products/<int:pk>/', ProductDetailView.as_view()),
]