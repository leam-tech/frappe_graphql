## DELETE_DOC Mutation
#### Query
```graphql
mutation DELETE_DOC($doctype: String!, $name: String!) {
    deleteDoc(doctype: $doctype, name: $name) {
        doctype,
        name,
        success
    }
}
```
#### Variables
```json
{
  "doctype":  "Test Doctype",
  "name": "Example Doc"
}
```
#### Response
```json
{
  "data": {
    "deleteDoc": {
      "doctype": "Test Doctype",
      "name": "Example Doc",
      "success": true
    }
  }
}
```
