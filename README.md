## Frappe Graphql

GraphQL API Layer for Frappe Framework

#### License

MIT

## Instructions
Generate the sdls first
```
$ bench --site test_site graphql generate_sdl
```
and start making your graphql requests against:
```
/api/method/graphql
```

# Features
## Getting single Document and getting a filtered doctype list
You can get a single document by its name using `<doctype>` query.  
```
{
    User(name: "Administrator") {
        name,
        email
    }
}
```
You can get a list of documents by querying `<doctype-plural>`. You can also pass in filters and sorting details as arguments:
```graphql
{
    Users(filter: [["name", "like", "%a%"]], sortBy: { field: NAME, direction: ASC }) {
        name,
        email,
        roles {
            role
        }
    }
}
```
For sort by fields, only those fields that are search_indexed / unique can be used. NAME, CREATION & MODIFIED can also be used
  
## Access Field Linked Documents in nested queries
All Link fields return respective doc. Add `__name` suffix to the link field name to get the link name.
```
{
    ToDo (limit_page_length: 1) {
        name,
        priority,
        description,
        assigned_by__name,
        assigned_by {
            full_name,
            roles {
                role__name,
                role {
                    name,
                    creation
                }
            }
        }
    }
}
```
Result
```json
{
    "data": {
        "ToDo": [
            {
                "name": "ae6f39845b",
                "priority": "Low",
                "description": "<div class=\"ql-editor read-mode\"><p>Do this</p></div>",
                "assigned_by__name": "Administrator",
                "assigned_by": {
                    "full_name": "Administrator",
                    "roles": [
                        {
                            "role__name": "System Manager",
                            "role": {
                                "name": "System Manager",
                                "creation": "2021-02-02 08:34:42.170306",
                            }
                        }
                    ]
                }
            }
            ...
        ]
    }
}
```

## RolePermission integration
Data is returned based on Read access to the resource

## Standard Mutations: set_value , save_doc & delete_doc
- [SET_VALUE Mutation](./docs/SET_VALUE.md)
- [SAVE_DOC Mutation](./docs/SAVE_DOC.md)
- [DELETE_DOC Mutation](./docs/DELETE_DOC.md)

## Pagination
Cursor based pagination is implemented. You can read more about it here: [Cursor Based Pagination](./docs/cursor_pagination.md)

## Support Extensions via Hooks
You can extend the SDLs with additional query / mutations / subscriptions. Examples are provided for a specific set of Scenarios. Please read [GraphQL Spec](http://spec.graphql.org/June2018/#sec-Object-Extensions) regarding Extending types. There are mainly two hooks introduced:
- `graphql_sdl_dir`  
Specify a list of directories containing `.graphql` files relative to the app's root directory.
eg:
```py
# hooks.py
graphql_sdl_dir = [
    "./your-app/your-app/generated/sdl/dir1",
    "./your-app/your-app/generated/sdl/dir2",
]
```
The above will look for graphql files in `your-bench/apps/your-app/your-app/generated/sdl/dir1` & `./dir2` folders.


- `graphql_schema_processors`  
You can pass in a list of cmd that gets executed on schema creation. You are given `GraphQLSchema` object (please refer [graphql-core](https://github.com/graphql-python/graphql-core)) as the only parameter. You can modify it or extend it as per your requirements.
This is a good place to attach the resolvers for the custom SDLs defined via `graphql_sdl_dir`

## Examples
### Adding a newly created DocType
- Generate the SDLs in your app directory
```bash
# Generate sdls for all doctypes in <your-app>
$ bench --site test_site graphql generate_sdl --output-dir <your-app/graphql> --app <your-app>

# Generate sdls for all doctype in module <m1> <m2>
$ bench --site test_site graphql generate_sdl --output-dir <your-app/graphql> --module <m1> -m <m2> -m <name>

# Generate sdls for doctype <d1> <2>
$ bench --site test_site graphql generate_sdl --output-dir <your-app/graphql> --doctype <d1> -dt <d2> -dt <name>

```
- Specify this directory in `graphql_sdl_dir` hook and you are done.
### Introducing a Custom Field to GraphQL
- Add the `Custom Field` in frappe
- Add the following to a `.graphql` file in your app and specify its directory via `graphql_sdl_dir`
```graphql
extend type User {
    is_super: Int!
}
```

### Adding a Hello World Query
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
### Adding a DocMeta Query

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

### Adding a new Mutation
There are two ways:
1. Write SDL and Attach Resolver to the Schema  
    ```graphql
    # SDL for Mutation
    type MY_MUTATION_OUTPUT_TYPE {
        success: Boolean
    }

    extend type Mutation {
        myNewMutation(args): MY_MUTATION_OUTPUT_TYPE
    }
    ```

    ```py
    # Attach Resolver (Specify the cmd to this function in `graphql_schema_processors` hook)
    def myMutationResolver(schema: GraphQLSchema):
        def _myMutationResolver(obj: Any, info: GraphQLResolveInfo):
            # frappe.set_value(..)
            return {
                "success": True
            }

        mutation_type = schema.mutation_type
        mutation_type.fields["myNewMutation"].resolve = _myMutationResolver
    ```  

2. Make use of `graphql-core` apis
    ```py
    # Specify the cmd to this function in `graphql_schema_processors` hook
    def bindMyNewMutation(schema):

        def _myMutationResolver(obj: Any, info: GraphQLResolveInfo):
            # frappe.set_value(..)
            return {
                "success": True
            }

        mutation_type = schema.mutation_type
        mutation_type.fields["myNewMutation"] = GraphQLField(
            GraphQLObjectType(
                name="MY_MUTATION_OUTPUT_TYPE",
                fields={
                    "success": GraphQLField(
                        GraphQLBoolean,
                        resolve=lambda obj, info: obj["success"]
                    )
                }
            ),
            resolve=_myMutationResolver
        )
    ```
### Adding a new Subscription

### Modify the Schema randomly
```py
def schema_processor(schema: GraphQLSchema):
    schema.query_type.fields["hello"] = GraphQLField(
        GraphQLString, resolve=lambda obj, info: "World!")
```

## Subscriptions
Get notified instantly of the updates via existing frappe's SocketIO