import base64
from graphql import GraphQLResolveInfo, GraphQLError

import frappe
from frappe.model.db_query import DatabaseQuery


def list_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    doctype = kwargs["doctype"]
    frappe.has_permission(doctype=doctype, throw=True)

    before = kwargs.get("before")
    after = kwargs.get("after")
    first = kwargs.get("first")
    last = kwargs.get("last")
    filters = kwargs.get("filter") or []
    sort_key, sort_dir = get_sort_args(kwargs.get("sortBy"))
    _validate_connection_args(kwargs)

    original_sort_dir = sort_dir
    if last and sort_dir == "asc":
        # to get LAST, we swap the sort order
        # data will be reversed after fetch
        sort_dir = "desc"

    cursor = after or before
    limit = first or last

    filters = process_filters(doctype, filters)

    count = frappe.db.sql(f"""
        SELECT COUNT(*)
        FROM `tab{doctype}`
        {"WHERE {}".format(" AND ".join(filters)) if len(filters) else ""}
    """)[0][0]

    if cursor:
        # Cursor filter should be applied after taking count
        cursor = from_cursor(cursor)
        filters.append(get_db_filter(doctype, [
            sort_key,
            ">" if after else "<",
            cursor[0]
        ]))

    data = frappe.db.sql(f"""
        SELECT name, "{doctype}" as doctype, {sort_key}
        FROM `tab{doctype}`
        {"WHERE {}".format(" AND ".join(filters)) if len(filters) else ""}
        ORDER BY {sort_key} {sort_dir}
        LIMIT {limit}
    """, as_dict=1)

    if sort_dir != original_sort_dir:
        data = reversed(data)

    edges = [
        frappe._dict(
            cursor=to_cursor(x, sort_key=sort_key),
            node=x
        ) for x in data
    ]

    return frappe._dict(
        totalCount=count,
        pageInfo=frappe._dict(
            hasNextPage=True,
            hasPreviousPage=True,
            startCursor=edges[0].cursor if len(edges) else None,
            endCursor=edges[-1].cursor if len(edges) else None
        ),
        edges=edges
    )


def _validate_connection_args(args):
    first = args.get("first")
    last = args.get("last")

    if not first and not last:
        raise GraphQLError("Argument `first` or `last` should be specified")
    if first and not (isinstance(first, int) and first > 0):
        raise GraphQLError("Argument `first` must be a non-negative integer.")
    if last and not (isinstance(last, int) and last > 0):
        raise GraphQLError("Argument `last` must be a non-negative integer.")
    if first and last:
        raise GraphQLError("Argument `last` cannot be combined with `first`.")
    if first and args.get("before"):
        raise GraphQLError("Argument `first` cannot be combined with `before`.")
    if last and args.get("after"):
        raise GraphQLError("Argument `last` cannot be combined with `after`.")


def process_filters(doctype, input_filters):
    filters = []
    operator_map = frappe._dict(
        EQ="=", NEQ="!=", LT="<", GT=">", LTE="<=", GTE=">=",
        LIKE="like", NOT_LIKE="not like"
    )
    for f in input_filters:
        filters.append(get_db_filter(doctype, [
            f.get("fieldname"),
            operator_map[f.get("operator")],
            f.get("value")
        ]))

    return filters


def get_db_filter(doctype, filter):
    return DatabaseQuery(doctype=doctype).prepare_filter_condition(filter)


def get_sort_args(sorting_input=None):
    sort_key = "modified"
    sort_dir = "desc"
    if sorting_input and sorting_input.get("field"):
        sort_key = sorting_input.get("field").lower()
        sort_dir = sorting_input.get("direction").lower() \
            if sorting_input.get("direction") else "desc"

    return sort_key, sort_dir


def to_cursor(row, sort_key):
    _json = frappe.as_json([row.get(sort_key)])
    return frappe.safe_decode(base64.b64encode(_json.encode("utf-8")))


def from_cursor(cursor):
    return frappe.parse_json(frappe.safe_decode(base64.b64decode(cursor)))
