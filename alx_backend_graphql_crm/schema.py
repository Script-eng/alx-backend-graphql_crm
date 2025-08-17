import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

# Inherit all queries defined in the crm app's schema
class Query(CRMQuery, graphene.ObjectType):
    """
    This is the root Query for the entire project. It combines queries
    from all apps.
    """
    pass

# Inherit all mutations defined in the crm app's schema
class Mutation(CRMMutation, graphene.ObjectType):
    """
    This is the root Mutation for the entire project. It combines mutations
    from all apps.
    """
    pass

# Create the final schema instance that Graphene will use,
# ensuring both queries and mutations are enabled.
schema = graphene.Schema(query=Query, mutation=Mutation)