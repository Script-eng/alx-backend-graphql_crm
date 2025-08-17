import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Customer, Product, Order, OrderItem
import re # For phone number validation

# --- GraphQL Object Types (Mirroring Django Models) ---

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")

class OrderItemType(DjangoObjectType):
    class Meta:
        model = OrderItem
        fields = ("id", "order", "product", "quantity", "price_at_order")

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount") # "products" will be resolved via OrderItem

    # Custom resolver to fetch associated products and their details from OrderItem
    # This makes the 'products' field in OrderType return a list of Product objects
    # with their correct quantity and price_at_order.
    products = graphene.List(
        graphene.JSONString, # Using JSONString to represent a list of dictionaries for simplicity
        source='order_items' # Django's ORM can directly access related OrderItems
    )

    def resolve_products(root, info):
        # root is an Order instance. root.order_items gives us the related OrderItem objects.
        return [
            {
                "id": oi.product.id,
                "name": oi.product.name,
                "price": oi.price_at_order, # Price at the time of order
                "quantity": oi.quantity
            } for oi in root.order_items.select_related('product')
        ]


# --- Input Types for Mutations ---

# For creating a single customer
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False) # Optional

# For creating multiple customers
class CustomerInputForBulk(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

# For creating a product
class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False, default_value=0)

# For creating an order
class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime(required=False)

# --- Mutation Classes ---

# Mutation to create a single customer
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    # The output of the mutation
    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(root, info, input=None):
        # 1. Validate phone number format
        if input.phone and not re.match(r'^\+?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$', input.phone):
            raise Exception("Invalid phone number format. Please use '+1234567890' or '123-456-7890'.")

        # 2. Check for duplicate email
        if Customer.objects.filter(email=input.email).exists():
            raise Exception("Email address already exists.")

        try:
            # 3. Create the customer
            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.phone or None # Ensure None if blank
            )
            return CreateCustomer(customer=customer, message="Customer created successfully.")
        except Exception as e:
            # Catch any unexpected database errors
            raise Exception(f"An unexpected error occurred: {e}")

# Mutation to create multiple customers in bulk
class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInputForBulk, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic # Ensure all or nothing for the batch
    def mutate(root, info, input=None):
        created_customers = []
        customer_errors = []

        for customer_data in input:
            try:
                # Validation: email uniqueness
                if Customer.objects.filter(email=customer_data.email).exists():
                    customer_errors.append(f"Email '{customer_data.email}' already exists.")
                    continue # Skip this customer

                # Validation: phone format (optional)
                if customer_data.phone and not re.match(r'^\+?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$', customer_data.phone):
                    customer_errors.append(f"Phone format for '{customer_data.email}' is invalid.")
                    continue # Skip this customer

                # Create customer if validations pass
                customer = Customer.objects.create(
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.phone or None
                )
                created_customers.append(customer)

            except Exception as e:
                # Catch any other unexpected errors during creation
                customer_errors.append(f"Failed to create customer '{customer_data.email}': {e}")
                # Note: transaction.atomic will roll back if any error occurs and we re-raise or don't catch it cleanly.
                # For partial success, we catch, record error, and continue.

        return BulkCreateCustomers(customers=created_customers, errors=customer_errors)


# Mutation to create a product
class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(root, info, input=None):
        # 1. Validate price and stock
        if input.price <= 0:
            raise Exception("Price must be positive.")
        if input.stock < 0:
            raise Exception("Stock cannot be negative.")

        try:
            # 2. Create the product
            product = Product.objects.create(
                name=input.name,
                price=input.price,
                stock=input.stock or 0 # Ensure default if not provided
            )
            return CreateProduct(product=product)
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {e}")

# Mutation to create an order
class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    def mutate(root, info, input=None):
        # 1. Validate customer ID
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID.")

        # 2. Validate product IDs and collect them for the order
        selected_products = []
        total_amount = 0
        try:
            # Ensure at least one product is selected
            if not input.product_ids:
                raise Exception("At least one product must be selected for an order.")

            for prod_id in input.product_ids:
                try:
                    product = Product.objects.get(id=prod_id)
                    # Validate stock if needed (e.g., reduce stock, check availability)
                    # For this basic setup, we just collect them.
                    selected_products.append(product)
                    total_amount += product.price # Add product's current price for total
                except Product.DoesNotExist:
                    raise Exception(f"Invalid product ID: {prod_id}")
        except Exception as e:
            raise Exception(e) # Re-raise validation errors

        try:
            # 3. Create the order
            order = Order.objects.create(
                customer=customer,
                order_date=input.order_date or timezone.now(),
                total_amount=total_amount # Set the calculated total amount
            )

            # 4. Associate products and create OrderItem entries
            order_items_to_create = []
            for product in selected_products:
                order_items_to_create.append(
                    OrderItem(
                        order=order,
                        product=product,
                        quantity=1, # Assuming quantity 1 per product ID for simplicity here
                        price_at_order=product.price # Store price at time of order
                    )
                )
            OrderItem.objects.bulk_create(order_items_to_create)

            # Recalculate total amount to be sure, or just use the calculated one.
            # A more robust approach would be to sum the price_at_order from OrderItems.
            # For now, the calculated total_amount is used.

            return CreateOrder(order=order)
        except Exception as e:
            raise Exception(f"An unexpected error occurred during order creation: {e}")

# --- Root Mutation ---
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

# --- Main Schema Definition ---
# This part is usually in graphql_crm/schema.py, but for this task, we'll
# combine Query and Mutation here for simplicity of demonstration.
# In a real project, you'd import Query and Mutation from crm.schema into graphql_crm/schema.py.

# Placeholder for a Query class if you had one defined in crm/schema.py
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello from CRM Schema!")

schema = graphene.Schema(query=Query, mutation=Mutation)