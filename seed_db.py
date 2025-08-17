import os
import uuid
from django.db import transaction
from crm.models import Customer, Product, Order, OrderItem
from django.utils import timezone

def seed_database():
    """Seeds the database with sample data."""
    print("Seeding database...")

    # Clear existing data
    Customer.objects.all().delete()
    Product.objects.all().delete()
    Order.objects.all().delete()
    OrderItem.objects.all().delete()

    try:
        with transaction.atomic():
            # Create Customers
            customer1 = Customer.objects.create(
                id=uuid.uuid4(),
                name="Alice Wonderland",
                email="alice@example.com",
                phone="+1234567890"
            )
            customer2 = Customer.objects.create(
                id=uuid.uuid4(),
                name="Bob The Builder",
                email="bob@example.com",
                phone="123-456-7890"
            )
            customer3 = Customer.objects.create(
                id=uuid.uuid4(),
                name="Charlie Chaplin",
                email="charlie@example.com"
            )
            print(f"Created {Customer.objects.count()} customers.")

            # Create Products
            product1 = Product.objects.create(
                id=uuid.uuid4(),
                name="Laptop Pro",
                price=1200.50,
                stock=15
            )
            product2 = Product.objects.create(
                id=uuid.uuid4(),
                name="Wireless Mouse",
                price=25.99,
                stock=100
            )
            product3 = Product.objects.create(
                id=uuid.uuid4(),
                name="Mechanical Keyboard",
                price=75.00,
                stock=50
            )
            print(f"Created {Product.objects.count()} products.")

            # Create Orders
            order1 = Order.objects.create(
                id=uuid.uuid4(),
                customer=customer1,
                order_date=timezone.now() - timezone.timedelta(days=2),
                total_amount=1226.49 # 1200.50 + 25.99
            )
            OrderItem.objects.create(order=order1, product=product1, quantity=1, price_at_order=product1.price)
            OrderItem.objects.create(order=order1, product=product2, quantity=1, price_at_order=product2.price)

            order2 = Order.objects.create(
                id=uuid.uuid4(),
                customer=customer2,
                order_date=timezone.now() - timezone.timedelta(days=1),
                total_amount=75.00 # 75.00
            )
            OrderItem.objects.create(order=order2, product=product3, quantity=1, price_at_order=product3.price)

            print(f"Created {Order.objects.count()} orders.")
            print("Database seeding complete.")

    except Exception as e:
        print(f"Error during seeding: {e}")

if __name__ == "__main__":
    # Ensure Django settings are configured if running script directly
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
    import django
    django.setup()
    seed_database()