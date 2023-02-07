# Adding a DocMeta Query

```py
# Add the cmd to the following function in `graphql_schema_processors`
def docmeta_query(schema):
    from graphql import GraphQLField, GraphQLObjectType, GraphQLString, GraphQLInt
    schema.query_type.fields["docmeta"] = GraphQLField(
        GraphQLList(GraphQLObjectType(
            name="DocTypeMeta",
            fields={
                "name": GraphQLField(
                    GraphQLString,
                    resolve=lambda obj, info: obj
                ),
                "number_of_docs": GraphQLField(
                    GraphQLInt,
                    resolve=lambda obj, info: frappe.db.count(obj)
                ),
            }
        )),
        resolve=lambda obj, info: [x.name for x in frappe.get_all("DocType")]
    )
```

Please refer `graphql-core` for more examples
