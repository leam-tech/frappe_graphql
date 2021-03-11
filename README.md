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
## Filtering
You can filter any doctype by its `name`, `standard_filters` or with a `filters` json

Filtering by name is straight forward:
```graphql
{
    User(name: "Administrator") {
        name,
        email,
        roles {
            role
        }
    }
}
```
For standard filters, lets take a look at the User doctype. It has 3 standard filters:
- `full_name`
- `username`
- `user_type`

It is possible to query them like this:
```graphql
{
    User(full_name: "Test A") {
        name, email
    }
}
```

And with `filters` json dict:
```graphql
{
    User(filters: "{ \"full_name\": [\"LIKE\", \"%TEST%\"] }") {
        name, email
    }
}
```  
## Access Field Linked Documents in nested queries
All Link fields are generate another graphql field with a `__doc` suffix.
```
{
    ToDo (limit_page_length: 1) {
        name,
        priority,
        description,
        assigned_by,
        assigned_by__doc {
            full_name,
            roles {
                role,
                role__doc {
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
                "description": "<div class=\"ql-editor read-mode\"><p>TESADASD</p></div>",
                "assigned_by": "Administrator",
                "assigned_by__doc": {
                    "full_name": "Administrator",
                    "roles": [
                        {
                            "role": "Administrator",
                            "role__doc": {
                                "name": "Administrator",
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

## Generic Mutations: set_value & save_doc
- SetValue
#### Query
```graphql
mutation SET_VALUE($doctype: String!, $name: String!, $fieldname: String!, $value: String!) {
    setValue(doctype: $doctype, name: $name, fieldname: $fieldname, value: $value) {
        doctype,
        name,
        fieldname,
        value,
        doc {
            name,
            ...on User {
                first_name,
                last_name,
                full_name
            }
        }
    }
}
```
#### Variables
```json
{
    "doctype": "User",
    "name": "test@test.com",
    "fieldname": "first_name",
    "value": "Test X"
}
```
#### Response
```json
{
    "data": {
        "setValue": {
            "doctype": "User",
            "name": "test@test.com",
            "fieldname": "first_name",
            "value": "Test",
            "doc": {
                "name": "test@test.com",
                "first_name": "Test X",
                "last_name": "Test A",
                "full_name": "Test X Test A"
            }
        }
    }
}
```

- Save Doc
#### Query
```graphql
mutation SAVE_DOC($doctype: String!, $doc: String!){
    saveDoc(doctype: $doctype, doc: $doc){
        doctype,
        name,
        doc {
            name,
            ... on ToDo {
                priority
            }
        }
    }
}
```
#### Variables
```json
{
    "doctype":"ToDo",
    "doc": "{ \"priority\": \"High\", \"description\": \"Test Todo 1\" }"
}
```
#### Response
```json
{
    "data": {
        "saveDoc": {
            "doctype": "ToDo",
            "name": "122cec40d0",
            "doc": {
                "name": "122cec40d0",
                "priority": "High"
            }
        }
    }
}
```

## Pagination
`limit_start` & `limit_page_length` could be passed to paginate through the doctypes
#### Query
```graphql
{
    User(limit_start: 0, limit_page_length: 10) {
        name
    }
}
```

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
$ bench --site test_site graphql generate_sdl --output-dir <your-app/graphql> --doctype <name>
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