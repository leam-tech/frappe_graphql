## SET VALUE Mutation

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