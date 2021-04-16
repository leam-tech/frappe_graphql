# Users with Docs they Own

You can make use of `CursorPaginator` class to help you implement Cursor pagination.

The following example shows fetching users having particular Role, along with all of the Documents they ever created across ALL the doctype

## Query & Response

<details>
<summary>Query</summary>
<p>

```gql
query GetUsersByRole($role: String!, $first: Int, $last: Int, $after: String, $before: String, $sortBy: UserListSortingInput, $documents_filter: [DBFilterInput!]) {
    get_users(role: $role, first: $first, last: $last, after: $after, before: $before, sortBy: $sortBy) {
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
                first_name,
                documents(first: 10, filter: $documents_filter) {
                    totalCount,
                    edges {
                        cursor,
                        node {
                            doctype,
                            name
                            ... on User {
                                owner__name
                            }
                        }
                    }
                }
            }
        }
    },
    ping
}
```
</p>
</details>

<details>
<summary>Variables</summary>
<p>


```json
{
    "first": 10,
    "role": "Accounts User",
    "sortBy": {
        "field": "modified",
        "direction": "DESC"
    },
    "documents_filter": [
        { "fieldname": "doctype", "operator": "EQ", "value": "User"}
    ]
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
        "get_users": {
            "totalCount": 7,
            "pageInfo": {
                "hasNextPage": false,
                "hasPreviousPage": false,
                "startCursor": "WwogIjIwMjEtMDQtMDUgMTA6NDY6MDkuMDczNjk3Igpd",
                "endCursor": "WwogIjIwMjEtMDItMDIgMDg6MzU6MTQuMDI2MDc3Igpd"
            },
            "edges": [
                {
                    "cursor": "WwogIjIwMjEtMDQtMDUgMTA6NDY6MDkuMDczNjk3Igpd",
                    "node": {
                        "name": "t5@t.com",
                        "first_name": "T 5",
                        "documents": {
                            "totalCount": 0,
                            "edges": []
                        }
                    }
                },
                {
                    "cursor": "WwogIjIwMjEtMDQtMDUgMDg6MzI6NDguNDk0MzA1Igpd",
                    "node": {
                        "name": "t4@t.com",
                        "first_name": "T 4",
                        "documents": {
                            "totalCount": 0,
                            "edges": []
                        }
                    }
                },
                {
                    "cursor": "WwogIjIwMjEtMDQtMDUgMDg6MzI6MzUuODQzMjczIgpd",
                    "node": {
                        "name": "t3@t.com",
                        "first_name": "T 3",
                        "documents": {
                            "totalCount": 0,
                            "edges": []
                        }
                    }
                },
                {
                    "cursor": "WwogIjIwMjEtMDQtMDUgMDg6MzI6MTguMzA4Mzg5Igpd",
                    "node": {
                        "name": "t2@t.com",
                        "first_name": "T 2",
                        "documents": {
                            "totalCount": 0,
                            "edges": []
                        }
                    }
                },
                {
                    "cursor": "WwogIjIwMjEtMDQtMDUgMDg6MzI6MDMuNDE2MTYzIgpd",
                    "node": {
                        "name": "t1@t.com",
                        "first_name": "T 1",
                        "documents": {
                            "totalCount": 0,
                            "edges": []
                        }
                    }
                },
                {
                    "cursor": "WwogIjIwMjEtMDItMTMgMjM6MjM6NTUuMjc4MDIzIgpd",
                    "node": {
                        "name": "faztp12@gmail.com",
                        "first_name": "Test",
                        "documents": {
                            "totalCount": 1,
                            "edges": [
                                {
                                    "cursor": "WwogIjIwMjEtMDQtMDUgMTA6NDY6MDkuMDczNjk3Igpd",
                                    "node": {
                                        "doctype": "User",
                                        "name": "t5@t.com",
                                        "owner__name": "faztp12@gmail.com"
                                    }
                                }
                            ]
                        }
                    }
                },
                {
                    "cursor": "WwogIjIwMjEtMDItMDIgMDg6MzU6MTQuMDI2MDc3Igpd",
                    "node": {
                        "name": "Administrator",
                        "first_name": "Administrator",
                        "documents": {
                            "totalCount": 7,
                            "edges": [
                                {
                                    "cursor": "WwogIjIwMjEtMDQtMDUgMDg6MzI6NDguNDk0MzA1Igpd",
                                    "node": {
                                        "doctype": "User",
                                        "name": "t4@t.com",
                                        "owner__name": "Administrator"
                                    }
                                },
                                {
                                    "cursor": "WwogIjIwMjEtMDQtMDUgMDg6MzI6MzUuODQzMjczIgpd",
                                    "node": {
                                        "doctype": "User",
                                        "name": "t3@t.com",
                                        "owner__name": "Administrator"
                                    }
                                },
                                {
                                    "cursor": "WwogIjIwMjEtMDQtMDUgMDg6MzI6MTguMzA4Mzg5Igpd",
                                    "node": {
                                        "doctype": "User",
                                        "name": "t2@t.com",
                                        "owner__name": "Administrator"
                                    }
                                },
                                {
                                    "cursor": "WwogIjIwMjEtMDQtMDUgMDg6MzI6MDMuNDE2MTYzIgpd",
                                    "node": {
                                        "doctype": "User",
                                        "name": "t1@t.com",
                                        "owner__name": "Administrator"
                                    }
                                },
                                {
                                    "cursor": "WwogIjIwMjEtMDItMTMgMjM6MjM6NTUuMjc4MDIzIgpd",
                                    "node": {
                                        "doctype": "User",
                                        "name": "faztp12@gmail.com",
                                        "owner__name": "Administrator"
                                    }
                                },
                                {
                                    "cursor": "WwogIjIwMjEtMDItMDIgMDg6MzU6MTQuMDI2MDc3Igpd",
                                    "node": {
                                        "doctype": "User",
                                        "name": "Administrator",
                                        "owner__name": "Administrator"
                                    }
                                },
                                {
                                    "cursor": "WwogIjIwMjEtMDItMDIgMDg6MzU6MTIuODM2MzU5Igpd",
                                    "node": {
                                        "doctype": "User",
                                        "name": "Guest",
                                        "owner__name": "Administrator"
                                    }
                                }
                            ]
                        }
                    }
                }
            ]
        },
        "ping": "pong"
    }
}
```
</p>
</details>

## SDL & Resolvers
<details>
<summary>SDL</summary>
<p>

```gql
input UserListSortingInput {
    direction: SortDirection!
    field: String
}

type DocumentEdge {
    cursor: String!
    node: BaseDocType!
}

type DocumentConnection {
    totalCount: Int!
    pageInfo: PageInfo
    edges: [DocumentEdge!]!
}

type UserWithOwnership {
    doctype: String!
    name: String!
    first_name: String!
    documents(first: Int, last: Int, after: String, before: String, filter: [DBFilterInput!], sortBy: UserWithOwnershipSortBy): DocumentConnection!
}

input UserWithOwnershipSortBy {
    direction: SortDirection!
    field: UserWithOwnershipSortByFields
}

enum UserWithOwnershipSortByFields {
    DOCTYPE_AND_NAME 
    DOCTYPE_AND_DOCSTATUS
}

type UserEdge {
    cursor: String!
    node: UserWithOwnership!
}

type UserList {
    totalCount: Int!
    pageInfo: PageInfo
    edges: [UserEdge!]!
}
```
</p>
</details>

<details>
<summary>Code</summary>
<p>

```py
# add this to graphql_schema_processors
from graphql import GraphQLSchema, GraphQLInt, GraphQLNonNull, GraphQLString, GraphQLField

import frappe
from frappe.model.db_query import DatabaseQuery
from frappe_graphql import CursorPaginator


def bind_user_with_ownership(schema: GraphQLSchema):

    def count_resolver(paginator: CursorPaginator, filters):
        role = paginator.resolve_kwargs.get("role")
        return frappe.get_list(
            "Has Role",
            fields=["COUNT(*) as _count"],
            filters=frappe._dict(
                role=role,
                parenttype="User"
            )
        )[0]._count

    def node_resolver(paginator: CursorPaginator, filters, sorting_fields, sort_dir, limit):
        role = paginator.resolve_kwargs.get("role")
        conditions = [DatabaseQuery("User").prepare_filter_condition(
            f).replace("`tabUser`", "user") for f in filters or []]
        conditions.append("role.role = %(role)s")
        return frappe.db.sql(
            f"""
            SELECT user.name, "User" as doctype, {', '.join(['user.' + x for x in sorting_fields])}
            FROM `tabUser` user
            JOIN `tabHas Role` role
                ON role.parent = user.name
            WHERE
                {' AND '.join(conditions)}
            ORDER BY {', '.join(['user.' + x for x in sorting_fields])} {sort_dir}
            LIMIT {limit}
            """, {"role": role}, as_dict=1
        )

    def resolver(obj, info, **kwargs):
        return CursorPaginator(
            doctype="User",
            count_resolver=count_resolver,
            node_resolver=node_resolver,
        ).resolve(obj, info, **kwargs)

    schema.query_type.fields["get_users"] = GraphQLField(
        schema.type_map["UserList"],
        resolve=resolver,
        args={
            "role": GraphQLNonNull(GraphQLString),
            "first": GraphQLInt,
            "last": GraphQLInt,
            "before": GraphQLString,
            "after": GraphQLString,
            "sortBy": schema.type_map["UserListSortingInput"]
        }
    )

    def get_all_doctypes_union():
        doctypes = [x.name for x in frappe.get_all("DocType", {"issingle": 0, "istable": 0})]
        return " UNION ".join([
            f"SELECT name, \"{d}\" as doctype, docstatus, modified FROM `tab{d}` "
            + "WHERE owner = %(owner)s"
            for d in doctypes
        ])

    def documents_count_resolver(paginator: CursorPaginator, filters):
        owner = paginator.resolve_obj.name
        conditions = [DatabaseQuery(paginator.doctype).prepare_filter_condition(
            f).replace(F"`tab{paginator.doctype}`.", "") for f in filters or []]
        return frappe.db.sql(f"""
        SELECT COUNT(*) as _count
        FROM (
            {get_all_doctypes_union()}
        ) dt_tables
        {" WHERE {}".format(" AND ".join(conditions)) if len(conditions) else ""}
        """, {"owner": owner})[0][0]

    def document_node_resolver(
            paginator: CursorPaginator,
            filters,
            sorting_fields,
            sort_dir,
            limit):
        owner = paginator.resolve_obj.name
        conditions = [
            DatabaseQuery(
                paginator.doctype).prepare_filter_condition(f).replace(
                F"`tab{paginator.doctype}`.",
                "") if isinstance(
                f,
                list) else f for f in filters or []]
        return frappe.db.sql(f"""
        SELECT
            name, doctype, {', '.join(sorting_fields)}
        FROM (
            {get_all_doctypes_union()}
        ) dt_tables
        {" WHERE {}".format(" AND ".join(conditions)) if len(conditions) else ""}
        ORDER BY {', '.join([f'{x} {sort_dir}' for x in sorting_fields])}
        LIMIT {limit}
        """, {"owner": owner}, as_dict=1)

    def documents_resolver(obj, info, **kwargs):
        return CursorPaginator(
            doctype="DocType",
            count_resolver=documents_count_resolver,
            node_resolver=document_node_resolver
        ).resolve(obj, info, **kwargs)

    schema.type_map["UserWithOwnership"].fields["documents"].resolve = documents_resolver

    ownership_sortfield_enum = {
        "DOCTYPE_AND_NAME": ["dt_tables.doctype", "dt_tables.name"],
        "DOCTYPE_AND_DOCSTATUS": ["dt_tables.doctype", "dt_tables.docstatus", "dt_tables.modified"],
    }
    for sort_key, value in ownership_sortfield_enum.items():
        schema.type_map["UserWithOwnershipSortByFields"].values[sort_key].value = value

```
</p>
</details>