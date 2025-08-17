import django_filters
from django.db.models import Q
from .models import Customer, Product, Order

class CustomerFilter(django_filters.FilterSet):
    # Challenge: Custom filter for phone number pattern
    phone_pattern = django_filters.CharFilter(method='filter_by_phone_pattern', label="Phone starts with")

    class Meta:
        model = Customer
        fields = {
            'name': ['icontains'],
            'email': ['icontains'],
            'created_at': ['gte', 'lte'], # Allows created_at__gte and created_at__lte
        }

    def filter_by_phone_pattern(self, queryset, name, value):
        return queryset.filter(phone__startswith=value)


class ProductFilter(django_filters.FilterSet):
    # Think: Filter for low stock (stock < 10)
    low_stock = django_filters.BooleanFilter(method='filter_by_low_stock', label="Low Stock (<10)")

    class Meta:
        model = Product
        fields = {
            'name': ['icontains'],
            'price': ['gte', 'lte'],
            'stock': ['exact', 'gte', 'lte'],
        }

    def filter_by_low_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__lt=10)
        return queryset


class OrderFilter(django_filters.FilterSet):
    # Related field lookups
    customer_name = django_filters.CharFilter(field_name='customer__name', lookup_expr='icontains')
    product_name = django_filters.CharFilter(field_name='products__name', lookup_expr='icontains')
    
    # Challenge: Filter orders that include a specific product ID
    product_id = django_filters.UUIDFilter(field_name='products__id')
    
    class Meta:
        model = Order
        fields = {
            'total_amount': ['gte', 'lte'],
            'order_date': ['gte', 'lte'],
        }