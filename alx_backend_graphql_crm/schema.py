import graphene

# 1. Define a Query class that inherits from graphene.ObjectType
class Query(graphene.ObjectType):
    """
    Defines the root fields for GraphQL queries.
    """
    # 2. Define the 'hello' field as a String type.
    hello = graphene.String(default_value="Hello, GraphQL!")

# 3. Create a schema instance and point it to our Query class.
schema = graphene.Schema(query=Query)