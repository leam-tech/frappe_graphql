from graphql import GraphQLSchema

from .root_query import setup_root_query_resolvers
from .link_field import setup_link_field_resolvers
from .child_tables import setup_child_table_resolvers


def setup_default_resolvers(schema: GraphQLSchema):
    setup_root_query_resolvers(schema=schema)
    setup_link_field_resolvers(schema=schema)
    setup_select_field_resolvers(schema=schema)
    setup_child_table_resolvers(schema=schema)


def setup_select_field_resolvers(schema: GraphQLSchema):
    pass
