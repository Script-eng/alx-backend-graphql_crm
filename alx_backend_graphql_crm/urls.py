from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

urlpatterns = [
    path('admin/', admin.site.urls),
    # The `graphiql=True` part gives us the nice in-browser IDE for testing.
    # `csrf_exempt` is used to allow external clients to POST to this endpoint.
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
]