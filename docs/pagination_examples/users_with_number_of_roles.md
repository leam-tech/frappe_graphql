# Users with NumRoles
In this example, sorting is done on an aggregated field, and conditions are applied in `HAVING` clause

<details>
<summary>Query</summary>

```gql
{
    user_with_number_of_roles(first: 15, sortBy: { direction: DESC, field: NUM_ROLES }) {
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
                full_name
                num_roles
                user {
                    email,
                    modified
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
        "user_with_number_of_roles": {
            "totalCount": 8,
            "pageInfo": {
                "hasNextPage": false,
                "hasPreviousPage": false,
                "startCursor": "WwogMjUsCiAiQWRtaW5pc3RyYXRvciIKXQ==",
                "endCursor": "WwogMSwKICJHdWVzdCIKXQ=="
            },
            "edges": [
                {
                    "cursor": "WwogMjUsCiAiQWRtaW5pc3RyYXRvciIKXQ==",
                    "node": {
                        "full_name": "Administrator",
                        "num_roles": 25,
                        "user": {
                            "email": "admin@example.com",
                            "modified": "2021-02-02 08:35:14.026077"
                        }
                    }
                },
                {
                    "cursor": "WwogMjIsCiAiVGVzdCBBbGkgWmFpbiIKXQ==",
                    "node": {
                        "full_name": "Test User",
                        "num_roles": 22,
                        "user": {
                            "email": "test_user@gmail.com",
                            "modified": "2021-02-13 23:23:55.278023"
                        }
                    }
                },
                {
                    "cursor": "WwogMjAsCiAiVCAzIgpd",
                    "node": {
                        "full_name": "T 3",
                        "num_roles": 20,
                        "user": {
                            "email": "t3@t.com",
                            "modified": "2021-04-17 03:05:16.303065"
                        }
                    }
                },
                {
                    "cursor": "WwogNiwKICJUIDIiCl0=",
                    "node": {
                        "full_name": "T 2",
                        "num_roles": 6,
                        "user": {
                            "email": "t2@t.com",
                            "modified": "2021-04-17 03:32:21.515262"
                        }
                    }
                },
                {
                    "cursor": "WwogNSwKICJUIDUiCl0=",
                    "node": {
                        "full_name": "T 5",
                        "num_roles": 5,
                        "user": {
                            "email": "t5@t.com",
                            "modified": "2021-04-17 03:33:20.008605"
                        }
                    }
                },
                {
                    "cursor": "WwogMSwKICJUIDQiCl0=",
                    "node": {
                        "full_name": "T 4",
                        "num_roles": 1,
                        "user": {
                            "email": "t4@t.com",
                            "modified": "2021-04-05 08:32:48.494305"
                        }
                    }
                },
                {
                    "cursor": "WwogMSwKICJUIDEiCl0=",
                    "node": {
                        "full_name": "T 1",
                        "num_roles": 1,
                        "user": {
                            "email": "t1@t.com",
                            "modified": "2021-04-05 08:32:03.416163"
                        }
                    }
                },
                {
                    "cursor": "WwogMSwKICJHdWVzdCIKXQ==",
                    "node": {
                        "full_name": "Guest",
                        "num_roles": 1,
                        "user": {
                            "email": "guest@example.com",
                            "modified": "2021-04-06 19:59:00.394288"
                        }
                    }
                }
            ]
        }
    }
}
```
</details>

<details>
<summary>Code</summary>

```py
import graphql as gql

import frappe
from frappe_graphql.utils.cursor_pagination import CursorPaginator
from graphql.type.definition import GraphQLObjectType
from graphql.type.scalars import GraphQLInt, GraphQLString


def bind_user_with_number_of_roles(schema: gql.GraphQLSchema):

    def node_resolver(
            paginator: CursorPaginator, filters=None, sorting_fields=[], sort_dir="asc", limit=5):

        # When after OR before is specified, we expect a SINGLE filter
        conditions = " HAVING {}".format(filters[0]) if len(filters) else ""
        if conditions:
            conditions = conditions.replace("`tabUser`.num_roles", "num_roles")
            conditions = conditions.replace("`tabUser`.full_name", "full_name")

        data = frappe.db.sql(f"""
            SELECT
                user.name,
                'User' as doctype,
                user.full_name,
                COUNT(*) AS num_roles
            FROM `tabUser` user
            JOIN `tabHas Role` has_role
                ON has_role.parent = user.name AND has_role.parenttype = "User"
            GROUP BY has_role.parent
            {conditions}
            ORDER BY {", ".join([
                f"{'user.' if x == 'modified' else ''}{x} {sort_dir}"
                for x in sorting_fields
            ])}
            LIMIT {limit}
        """, as_dict=1)

        for r in data:
            r.user = frappe._dict(doctype="User", name=r.name)

        return data

    def count_resolver(paginator: CursorPaginator, filters=None):
        return frappe.db.count("User")

    schema.query_type.fields["user_with_number_of_roles"] = gql.GraphQLField(

        args=frappe._dict(
            first=gql.GraphQLInt,
            after=gql.GraphQLString,
            last=gql.GraphQLInt,
            before=gql.GraphQLString,
            sortBy=gql.GraphQLArgument(
                default_value={
                    "direction": "DESC",
                    "field": "NUM_ROLES"
                },
                type_=gql.GraphQLInputObjectType(
                    name="UserWithNumRolesSortInfo",
                    fields=frappe._dict(
                        direction=schema.type_map["SortDirection"],
                        field=gql.GraphQLEnumType(
                            name="UserWithNumRolesSortField",
                            values={
                                "NUM_ROLES": ["num_roles", "full_name"],
                                "NAME": ["full_name", "modified"]
                            }
                        )
                    )
                )
            )
        ),

        # return type
        type_=gql.GraphQLObjectType(
            name="UserWithNumRolesConnection",
            fields=frappe._dict(
                totalCount=GraphQLInt,
                pageInfo=schema.type_map["PageInfo"],
                edges=gql.GraphQLList(gql.GraphQLObjectType(
                    name="UserWithNumRolesNode",
                    fields=frappe._dict(
                        cursor=GraphQLString,
                        node=GraphQLObjectType(
                            name="UserWithNumRolesNodeDetails",
                            fields=frappe._dict(
                                num_roles=GraphQLInt,
                                full_name=GraphQLString,
                                user=schema.type_map["User"]
                            )
                        )
                    )
                ))
            )
        ),

        resolve=lambda obj, info, **kwargs: CursorPaginator(
            doctype="User",
            node_resolver=node_resolver,
            count_resolver=count_resolver
        ).resolve(obj, info, **kwargs)
    )

```
</details>