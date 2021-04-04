## SAVE_DOC Mutation

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