## Cursor Based Pagination
You can pass in `first`, `last`, `after` and `before`  
[GraphQL Documentation on Pagination](https://graphql.org/learn/pagination/)

Example:
<details>
<summary>Query</summary>
<p>

```graphql
{
    Users(first: 10) {
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
```
</p>
</details>

<details>
<summary>Response</summary>
<p>

```json
{
    "data": {
        "Users": {
            "totalCount": 3,
            "pageInfo": {
                "hasNextPage": false,
                "hasPreviousPage": false,
                "startCursor": "WwogIjIwMjEtMDItMTMgMjM6MjM6NTUuMjc4MDIzIgpd",
                "endCursor": "WwogIjIwMjEtMDItMDIgMDg6MzU6MTIuODM2MzU5Igpd"
            },
            "edges": [
                {
                    "cursor": "WwogIjIwMjEtMDItMTMgMjM6MjM6NTUuMjc4MDIzIgpd",
                    "node": {
                        "name": "faztp12@gmail.com",
                        "first_name": "Test"
                    }
                },
                {
                    "cursor": "WwogIjIwMjEtMDItMDIgMDg6MzU6MTQuMDI2MDc3Igpd",
                    "node": {
                        "name": "Administrator",
                        "first_name": "Administrator"
                    }
                },
                {
                    "cursor": "WwogIjIwMjEtMDItMDIgMDg6MzU6MTIuODM2MzU5Igpd",
                    "node": {
                        "name": "Guest",
                        "first_name": "Guest"
                    }
                }
            ]
        }
    }
}
```
</p>
</details>

If you want to implement the same in one of your Custom queries, please check out the following examples here: [Custom & Nested Pagination](./nested_pagination.md)

More Examples:
- [Get Users with all the documents they `own`](./pagination_examples/users_with_ownership.md)
- [Get Todo list sorted by assigned_user (owner) & status](./pagination_examples/todo_with_user_status_sorting.md)
- Sort Users by number of Roles they got have assigned