import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

# Inherit queries from the crm app's schema
class Query(CRMQuery, graphene.ObjectType):
    pass

# Inherit mutations from the crm app's schema
class Mutation(CRMMutation, graphene.ObjectType):
    pass

# Create the final schema, enabling both queries and mutations
schema = graphene.Schema(query=Query, mutation=Mutation)