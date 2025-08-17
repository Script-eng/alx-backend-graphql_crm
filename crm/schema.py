import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.utils import timezone
from .models import Customer, Product, Order, OrderItem

# --- Object Types (How data is represented in GraphQL) ---

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount")

# --- Input Types (How data is received by mutations) ---

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(default_value=0)

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.UUID(required=True)
    product_ids = graphene.List(graphene.UUID, required=True)
    order_date = graphene.DateTime()


# --- Mutations (Classes that perform actions) ---

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(root, info, input):
        try:
            # Check for existing email before creating
            if Customer.objects.filter(email=input.email).exists():
                raise Exception("Email already exists.")
            
            customer = Customer(name=input.name, email=input.email, phone=input.phone)
            customer.full_clean() # Run model validators (like phone format)
            customer.save()
            
            return CreateCustomer(customer=customer, message="Customer created successfully.")
        except Exception as e:
            # Return a user-friendly error
            raise Exception(f"Validation Error: {e}")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(root, info, input):
        created_customers = []
        error_messages = []

        for customer_data in input:
            try:
                if Customer.objects.filter(email=customer_data.email).exists():
                    raise Exception(f"Email '{customer_data.email}' already exists.")
                
                customer = Customer(name=customer_data.name, email=customer_data.email, phone=customer_data.phone)
                customer.full_clean()
                # We save each one individually to handle partial success
                customer.save()
                created_customers.append(customer)
            except Exception as e:
                error_messages.append(f"Failed to create customer '{customer_data.email}': {e}")
        
        return BulkCreateCustomers(customers=created_customers, errors=error_messages)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(root, info, input):
        try:
            # Model's save method already validates positive price
            product = Product(name=input.name, price=input.price, stock=input.stock)
            product.save()
            return CreateProduct(product=product)
        except Exception as e:
            raise Exception(f"Validation Error: {e}")

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    @transaction.atomic
    def mutate(root, info, input):
        # Validate customer
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID.")

        # Validate products
        if not input.product_ids:
            raise Exception("At least one product must be provided.")
        
        products = Product.objects.filter(pk__in=input.product_ids)
        if len(products) != len(input.product_ids):
            raise Exception("One or more invalid product IDs provided.")

        # Calculate total amount
        total_amount = sum(p.price for p in products)

        # Create order
        order = Order.objects.create(
            customer=customer,
            order_date=input.get('order_date', timezone.now()),
            total_amount=total_amount
        )

        # Create order items
        order_items = [OrderItem(order=order, product=p) for p in products]
        OrderItem.objects.bulk_create(order_items)
        
        return CreateOrder(order=order)


# --- Root Mutation Class for the CRM App ---
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

# --- Root Query Class for the CRM App ---
class Query(graphene.ObjectType):
    # Add queries here in the future
    hello_crm = graphene.String(default_value="Welcome to the CRM API!")