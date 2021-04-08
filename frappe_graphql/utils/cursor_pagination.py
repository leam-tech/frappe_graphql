import base64
from graphql import GraphQLResolveInfo, GraphQLError

import frappe


class CursorPaginator(object):
    def __init__(
            self,
            doctype,
            filters=None,
            skip_process_filters=False,
            count_resolver=None,
            node_resolver=None,
            extra_args=None):

        if (not count_resolver) != (not node_resolver):
            frappe.throw(
                "Please provide both count_resolver & node_resolver to have custom implementation")

        self.doctype = doctype
        self.predefined_filters = filters
        self.skip_process_filters = skip_process_filters
        self.custom_count_resolver = count_resolver
        self.custom_node_resolver = node_resolver
        self.extra_args = extra_args

    def resolve(self, obj, info: GraphQLResolveInfo, **kwargs):
        self.resolve_obj = obj
        self.resolve_info = info
        self.resolve_kwargs = kwargs

        has_next_page = False
        has_previous_page = False
        before = kwargs.get("before")
        after = kwargs.get("after")
        first = kwargs.get("first")
        last = kwargs.get("last")

        filters = kwargs.get("filter") or []
        filters.extend(self.predefined_filters or [])

        sort_key, sort_dir = self.get_sort_args(kwargs.get("sortBy"))
        self.validate_connection_args(kwargs)

        original_sort_dir = sort_dir
        if last:
            # to get LAST, we swap the sort order
            # data will be reversed after fetch
            sort_dir = "desc" if sort_dir == "asc" else "asc"

        cursor = after or before
        limit = (first or last) + 1
        requested_count = first or last

        if not self.skip_process_filters:
            filters = self.process_filters(filters)

        count = self.get_count(self.doctype, filters)

        if cursor:
            # Cursor filter should be applied after taking count
            has_previous_page = True
            cursor = self.from_cursor(cursor)
            operator_map = {
                "after": {"asc": ">", "desc": "<"},
                "before": {"asc": "<", "desc": ">"},
            }
            filters.append([
                sort_key,
                operator_map["after"][original_sort_dir]
                if after else operator_map["before"][original_sort_dir],
                cursor[0]
            ])

        data = self.get_data(self.doctype, filters, sort_key, sort_dir, limit)
        matched_count = len(data)
        if matched_count > requested_count:
            has_next_page = True
            data.pop()
        if sort_dir != original_sort_dir:
            data = reversed(data)

        edges = [frappe._dict(
            cursor=self.to_cursor(x, sort_key=sort_key), node=x
        ) for x in data]

        return frappe._dict(
            totalCount=count,
            pageInfo=frappe._dict(
                hasNextPage=has_next_page,
                hasPreviousPage=has_previous_page,
                startCursor=edges[0].cursor if len(edges) else None,
                endCursor=edges[-1].cursor if len(edges) else None
            ),
            edges=edges
        )

    def validate_connection_args(self, args):
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

    def get_count(self, doctype, filters):
        if self.custom_count_resolver:
            return self.custom_count_resolver(
                paginator=self,
                filters=filters
            )

        return frappe.get_list(
            doctype,
            fields=["COUNT(*) as total_count"],
            filters=filters
        )[0].total_count

    def get_data(self, doctype, filters, sort_key, sort_dir, limit):
        if self.custom_node_resolver:
            return self.custom_node_resolver(
                paginator=self,
                filters=filters,
                sort_key=sort_key,
                sort_dir=sort_dir,
                limit=limit
            )

        return frappe.get_list(
            doctype,
            fields=["name", f"SUBSTR(\".{doctype}\", 2) as doctype", sort_key],
            filters=filters,
            order_by=f"{sort_key} {sort_dir}",
            limit_page_length=limit
        )

    def get_sort_args(self, sorting_input=None):
        sort_key = "modified"
        sort_dir = "desc"
        if sorting_input and sorting_input.get("field"):
            sort_key = sorting_input.get("field").lower()
            sort_dir = sorting_input.get("direction").lower() \
                if sorting_input.get("direction") else "desc"

        return sort_key, sort_dir

    def process_filters(self, input_filters):
        filters = []
        operator_map = frappe._dict(
            EQ="=", NEQ="!=", LT="<", GT=">", LTE="<=", GTE=">=",
            LIKE="like", NOT_LIKE="not like"
        )
        for f in input_filters:
            if not isinstance(f, dict):
                filters.append(f)
            else:
                filters.append([
                    f.get("fieldname"),
                    operator_map[f.get("operator")],
                    f.get("value")
                ])

        return filters

    def to_cursor(self, row, sort_key):
        _json = frappe.as_json([row.get(sort_key)])
        return frappe.safe_decode(base64.b64encode(_json.encode("utf-8")))

    def from_cursor(self, cursor):
        return frappe.parse_json(frappe.safe_decode(base64.b64decode(cursor)))
