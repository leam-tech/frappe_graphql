from graphql import GraphQLSchema


def bind(schema: GraphQLSchema):
    schema.query_type.fields["ping"].resolve = lambda obj, info: "pong"
