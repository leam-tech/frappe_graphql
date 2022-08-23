## Getting single Document and getting a filtered doctype list

You can get a single document by its name using `<doctype>` query.  
For sort by fields, only those fields that are search_indexed / unique can be used. NAME, CREATION & MODIFIED can also be used

### Query

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
        totalCount,
        pageInfo {
            hasNextPage,
            hasPreviousPage,
            startCursor,
            endCursor
        },
        edges {
            cursor,
            node {
                name,
                first_name
            }
        }
    }
    }
}
```
