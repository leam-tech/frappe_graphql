# Adding a Hello World Query

- Add a cmd in `graphql_schema_processors` hook
- Use the following function definition for the cmd specified:

```py
def hello_world(schema: GraphQLSchema):

    def hello_resolver(obj, info: GraphQLResolveInfo, **kwargs):
        return f"Hello {kwargs.get('name')}!"

    schema.query_type.fields["hello"] = GraphQLField(
        GraphQLString,
        resolve=hello_resolver,
        args={
            "name": GraphQLArgument(
                type_=GraphQLString,
                default_value="World"
            )
        }
    )
```

- Now, you can query like query like this:

```py
# Request
query Hello($var_name: String) {
    hello(name: $var_name)
}

# Variables
{
    "var_name": "Mars"
}

# Response
{
    "data": {
        "hello": "Hello Mars!"
    }
}
```
