import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction
from django.utils import timezone
from .models import Customer, Product, Order, OrderItem
from .filters import CustomerFilter, ProductFilter, OrderFilter # Import our new filters

# ==============================================================================
# SECTION 1: RELAY NODE TYPES (FOR FILTERING, PAGINATION, AND QUERIES)
# ==============================================================================

class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        # Define which fields are available and link to our filter class
        fields = ("id", "name", "email", "phone", "created_at")
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node, )

class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node, )

class OrderNode(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount")
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node, )

# ==============================================================================
# SECTION 2: ROOT QUERY CLASS (HANDLES ALL DATA FETCHING)
# ==============================================================================

class Query(graphene.ObjectType):
    # Single object retrieval using Relay's global IDs
    customer = graphene.relay.Node.Field(CustomerNode)
    product = graphene.relay.Node.Field(ProductNode)
    order = graphene.relay.Node.Field(OrderNode)

    # List retrieval with filtering, sorting, and pagination
    all_customers = DjangoFilterConnectionField(CustomerNode)
    all_products = DjangoFilterConnectionField(ProductNode)
    all_orders = DjangoFilterConnectionField(OrderNode)

# ==============================================================================
# SECTION 3: MUTATION LOGIC (RETAINED FROM TASK 2)
# ==============================================================================

# --- Input Types for Mutations ---
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

# --- Mutation Classes ---
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    customer = graphene.Field(CustomerNode) # Use the Node type for consistency
    message = graphene.String()
    def mutate(root, info, input):
        try:
            if Customer.objects.filter(email=input.email).exists():
                raise Exception("Email already exists.")
            customer = Customer(name=input.name, email=input.email, phone=input.phone)
            customer.full_clean()
            customer.save()
            return CreateCustomer(customer=customer, message="Customer created successfully.")
        except Exception as e:
            raise Exception(f"Validation Error: {e}")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)
    customers = graphene.List(CustomerNode) # Use the Node type
    errors = graphene.List(graphene.String)
    def mutate(root, info, input):
        created_customers, error_messages = [], []
        for data in input:
            try:
                if Customer.objects.filter(email=data.email).exists():
                    raise Exception(f"Email '{data.email}' already exists.")
                customer = Customer(name=data.name, email=data.email, phone=data.phone)
                customer.full_clean()
                customer.save()
                created_customers.append(customer)
            except Exception as e:
                error_messages.append(f"Failed to create customer '{data.email}': {e}")
        return BulkCreateCustomers(customers=created_customers, errors=error_messages)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)
    product = graphene.Field(ProductNode) # Use the Node type
    def mutate(root, info, input):
        try:
            product = Product(name=input.name, price=input.price, stock=input.stock)
            product.save()
            return CreateProduct(product=product)
        except Exception as e:
            raise Exception(f"Validation Error: {e}")

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)
    order = graphene.Field(OrderNode) # Use the Node type
    @transaction.atomic
    def mutate(root, info, input):
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID.")
        if not input.product_ids:
            raise Exception("At least one product must be provided.")
        products = Product.objects.filter(pk__in=input.product_ids)
        if len(products) != len(input.product_ids):
            raise Exception("One or more invalid product IDs provided.")
        total_amount = sum(p.price for p in products)
        order = Order.objects.create(
            customer=customer,
            order_date=input.get('order_date', timezone.now()),
            total_amount=total_amount
        )
        order_items = [OrderItem(order=order, product=p) for p in products]
        OrderItem.objects.bulk_create(order_items)
        return CreateOrder(order=order)

# ==============================================================================
# SECTION 4: ROOT MUTATION CLASS (HANDLES ALL DATA WRITING)
# ==============================================================================

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()