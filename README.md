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

## Features
### Filtering
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
    User(full_name: "Fahim") {
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

### RolePermission integration
Data is returned based on Read access to the resource

### Generic Mutations: set_value & save_doc
### Pagination
### Support SDL Extensions
https://docs.reactioncommerce.com/docs/how-to-extend-graphql-to-add-field
### Support additional Mutations via Hooks