import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

# Helper function for phone validation
def validate_phone_number(value):
    """Validates phone number format: +1234567890 or 123-456-7890"""
    # Regex for +1234567890 or 123-456-7890
    if not re.match(r'^\+?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$', value):
        raise ValidationError('Phone number must be in a valid format (e.g., +1234567890 or 123-456-7890)')

class Customer(models.Model):
    """Represents a customer in the CRM."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    email = models.EmailField(unique=True, null=False, blank=False)
    phone = models.CharField(max_length=20, blank=True, null=True, validators=[validate_phone_number])

    def __str__(self):
        return self.name

class Product(models.Model):
    """Represents a product available for sale."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    stock = models.PositiveIntegerField(null=False, blank=False, default=0)

    def clean(self):
        """Custom cleaning to ensure price is positive."""
        if self.price <= 0:
            raise ValidationError({'price': 'Price must be positive.'})
        if self.stock < 0: # Although PositiveIntegerField handles this, explicit check can be clearer
            raise ValidationError({'stock': 'Stock cannot be negative.'})

    def __str__(self):
        return self.name

class Order(models.Model):
    """Represents a customer order."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    products = models.ManyToManyField(Product, through='OrderItem')
    order_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Order {self.id} for {self.customer.name}"

class OrderItem(models.Model):
    """Links orders to products and stores quantity and price at the time of order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} for Order {self.order.id}"

    # Ensure price_at_order is set correctly when an OrderItem is created
    def save(self, *args, **kwargs):
        if not self.price_at_order:
            self.price_at_order = self.product.price
        super().save(*args, **kwargs)