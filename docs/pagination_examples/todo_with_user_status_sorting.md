# Todo sorted by Assigned User, status


## Query & Response
<details>
<summary>Query</summary>

```gql
{
    get_todo_with_user_status_sorting(first: 15, after: "", sortBy: { direction: DESC, field: USER_AND_STATUS }) {
        totalCount
        pageInfo {
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }
        edges {
            cursor
            node {
                doctype
                name,
                modified
                ... on ToDo {
                    owner__name,
                    status
                }
            }
        }
    }
}
```
</details>

<details>
<summary>Response</summary>

```json
{
    "data": {
        "get_todo_with_user_status_sorting": {
            "totalCount": 11,
            "pageInfo": {
                "hasNextPage": false,
                "hasPreviousPage": false,
                "startCursor": "WwogImZhenRwMTJAZ21haWwuY29tIiwKICJPcGVuIiwKICIyMDIxLTA0LTE3IDAyOjIyOjIzLjg1NjQ4NCIKXQ==",
                "endCursor": "WwogIkFkbWluaXN0cmF0b3IiLAogIkNsb3NlZCIsCiAiMjAyMS0wNC0xNyAwMjoyMToyOC44NDQ5MTIiCl0="
            },
            "edges": [
                {
                    "cursor": "WwogImZhenRwMTJAZ21haWwuY29tIiwKICJPcGVuIiwKICIyMDIxLTA0LTE3IDAyOjIyOjIzLjg1NjQ4NCIKXQ==",
                    "node": {
                        "doctype": "ToDo",
                        "name": "6f1cc1afdb",
                        "modified": "2021-04-17 02:22:23.856484",
                        "owner__name": "test@gmail.com",
                        "status": "Open"
                    }
                },
                {
                    "cursor": "WwogIkFkbWluaXN0cmF0b3IiLAogIk9wZW4iLAogIjIwMjEtMDQtMTYgMDI6MDk6MzUuNjE2OTk0Igpd",
                    "node": {
                        "doctype": "ToDo",
                        "name": "122cec40d0",
                        "modified": "2021-04-16 02:09:35.616994",
                        "owner__name": "Administrator",
                        "status": "Open"
                    }
                },
                {
                    "cursor": "WwogIkFkbWluaXN0cmF0b3IiLAogIk9wZW4iLAogIjIwMjEtMDQtMDMgMTc6NTU6MTYuOTIyNTA0Igpd",
                    "node": {
                        "doctype": "ToDo",
                        "name": "d165ee497d",
                        "modified": "2021-04-03 17:55:16.922504",
                        "owner__name": "Administrator",
                        "status": "Open"
                    }
                },
                {
                    "cursor": "WwogIkFkbWluaXN0cmF0b3IiLAogIk9wZW4iLAogIjIwMjEtMDQtMDMgMTc6NTU6MDYuODQ0NTg2Igpd",
                    "node": {
                        "doctype": "ToDo",
                        "name": "c7379202e7",
                        "modified": "2021-04-03 17:55:06.844586",
                        "owner__name": "Administrator",
                        "status": "Open"
                    }
                },
                {
                    "cursor": "WwogIkFkbWluaXN0cmF0b3IiLAogIk9wZW4iLAogIjIwMjEtMDQtMDMgMTc6NTQ6MzQuOTMxNDA3Igpd",
                    "node": {
                        "doctype": "ToDo",
                        "name": "2c8a93cbe0",
                        "modified": "2021-04-03 17:54:34.931407",
                        "owner__name": "Administrator",
                        "status": "Open"
                    }
                },
                {
                    "cursor": "WwogIkFkbWluaXN0cmF0b3IiLAogIk9wZW4iLAogIjIwMjEtMDQtMDMgMTc6NTQ6MjUuNjIxNTc4Igpd",
                    "node": {
                        "doctype": "ToDo",
                        "name": "1a13ed221f",
                        "modified": "2021-04-03 17:54:25.621578",
                        "owner__name": "Administrator",
                        "status": "Open"
                    }
                },
                {
                    "cursor": "WwogIkFkbWluaXN0cmF0b3IiLAogIk9wZW4iLAogIjIwMjEtMDQtMDMgMTc6NTQ6MTIuNjM1NTE4Igpd",
                    "node": {
                        "doctype": "ToDo",
                        "name": "bf208504c4",
                        "modified": "2021-04-03 17:54:12.635518",
                        "owner__name": "Administrator",
                        "status": "Open"
                    }
                },
                {
                    "cursor": "WwogIkFkbWluaXN0cmF0b3IiLAogIk9wZW4iLAogIjIwMjEtMDQtMDMgMTc6NTI6NTEuNjQ0MDUyIgpd",
                    "node": {
                        "doctype": "ToDo",
                        "name": "402202c9ba",
                        "modified": "2021-04-03 17:52:51.644052",
                        "owner__name": "Administrator",
                        "status": "Open"
                    }
                },
                {
                    "cursor": "WwogIkFkbWluaXN0cmF0b3IiLAogIk9wZW4iLAogIjIwMjEtMDQtMDMgMTc6NTI6MzkuNDIxNDQ1Igpd",
                    "node": {
                        "doctype": "ToDo",
                        "name": "4c6e172020",
                        "modified": "2021-04-03 17:52:39.421445",
                        "owner__name": "Administrator",
                        "status": "Open"
                    }
                },
                {
                    "cursor": "WwogIkFkbWluaXN0cmF0b3IiLAogIk9wZW4iLAogIjIwMjEtMDQtMDMgMTc6NTI6MDIuMTUxMjE2Igpd",
                    "node": {
                        "doctype": "ToDo",
                        "name": "307062f0ab",
                        "modified": "2021-04-03 17:52:02.151216",
                        "owner__name": "Administrator",
                        "status": "Open"
                    }
                },
                {
                    "cursor": "WwogIkFkbWluaXN0cmF0b3IiLAogIkNsb3NlZCIsCiAiMjAyMS0wNC0xNyAwMjoyMToyOC44NDQ5MTIiCl0=",
                    "node": {
                        "doctype": "ToDo",
                        "name": "ae6f39845b",
                        "modified": "2021-04-17 02:21:28.844912",
                        "owner__name": "Administrator",
                        "status": "Closed"
                    }
                }
            ]
        }
    }
}
```
</details>


## Code
<details>
<summary>Code</summary>

```py
from graphql import GraphQLSchema, GraphQLField, GraphQLList, GraphQLObjectType, \
    GraphQLInt, GraphQLString, GraphQLInputObjectType, GraphQLEnumType

import frappe
from frappe_graphql.utils.cursor_pagination import CursorPaginator


def bind_todo_with_user_status_sorting(schema: GraphQLSchema):
    schema.query_type.fields["get_todo_with_user_status_sorting"] = GraphQLField(

        # Specify args, like first: 10
        args=frappe._dict(
            first=GraphQLInt,
            after=GraphQLString,
            last=GraphQLInt,
            before=GraphQLString,

            # The sortBy input type
            sortBy=GraphQLInputObjectType(
                name="TodoWithUserStatusSortingSortInfo",
                fields=frappe._dict(
                    direction=schema.type_map["SortDirection"],
                    field=GraphQLEnumType(
                        name="TodoWithUserStatusSortingSortField",
                        values={
                            "USER_AND_STATUS": ["owner", "status", "modified"],
                            "USER_AND_MODIFIED": ["owner", "modified"]
                        }
                    )
                )
            )),

        # resolve to CursorPaginator. Everything else will be taken care of
        resolve=lambda obj, info, **kwargs: CursorPaginator(doctype="ToDo").resolve(
            obj, info, **kwargs),

        # The return type
        type_=GraphQLObjectType(
            "TodoWithUserStatusSorting",
            frappe._dict(
                totalCount=GraphQLInt,
                pageInfo=schema.type_map["PageInfo"],
                edges=GraphQLList(
                    GraphQLObjectType(
                        "TodoWithUserStatusSorting",
                        frappe._dict(
                            cursor=GraphQLString,
                            node=schema.type_map["BaseDocType"])
                    ))
            )))

```
</details>
