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

        self.validate_connection_args(kwargs)

        self.resolve_obj = obj
        self.resolve_info = info
        self.resolve_kwargs = kwargs

        self.has_next_page = False
        self.has_previous_page = False
        self.before = kwargs.get("before")
        self.after = kwargs.get("after")
        self.first = kwargs.get("first")
        self.last = kwargs.get("last")

        self.filters = kwargs.get("filter") or []
        self.filters.extend(self.predefined_filters or [])

        self.sorting_fields, self.sort_dir = self.get_sort_args(kwargs.get("sortBy"))

        self.original_sort_dir = self.sort_dir
        if self.last:
            # to get LAST, we swap the sort order
            # data will be reversed after fetch
            self.sort_dir = "desc" if self.sort_dir == "asc" else "asc"

        self.cursor = self.after or self.before
        limit = (self.first or self.last) + 1
        requested_count = self.first or self.last

        if not self.skip_process_filters:
            self.filters = self.process_filters(self.filters)

        count = self.get_count(self.doctype, self.filters)

        if self.cursor:
            # Cursor filter should be applied after taking count
            self.has_previous_page = True
            self.filters.append(self.get_cursor_filter())

        data = self.get_data(self.doctype, self.filters, self.sorting_fields, self.sort_dir, limit)
        matched_count = len(data)
        if matched_count > requested_count:
            self.has_next_page = True
            data.pop()
        if self.sort_dir != self.original_sort_dir:
            data = reversed(data)

        edges = [frappe._dict(
            cursor=self.to_cursor(x, sorting_fields=self.sorting_fields), node=x
        ) for x in data]

        return frappe._dict(
            totalCount=count,
            pageInfo=frappe._dict(
                hasNextPage=self.has_next_page,
                hasPreviousPage=self.has_previous_page,
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

    def get_data(self, doctype, filters, sorting_fields, sort_dir, limit):
        if self.custom_node_resolver:
            return self.custom_node_resolver(
                paginator=self,
                filters=filters,
                sorting_fields=sorting_fields,
                sort_dir=sort_dir,
                limit=limit
            )

        return frappe.get_list(
            doctype,
            fields=["name", f"SUBSTR(\".{doctype}\", 2) as doctype"] + sorting_fields,
            filters=filters,
            order_by=f"{', '.join([f'{x} {sort_dir}' for x in sorting_fields])}",
            limit_page_length=limit
        )

    def get_sort_args(self, sorting_input=None):
        sorting_fields = ["modified"]
        sort_dir = "desc"
        if sorting_input and sorting_input.get("field"):
            sort_dir = sorting_input.get("direction").lower() \
                if sorting_input.get("direction") else "asc"

            sorting_input_field = sorting_input.get("field")
            if isinstance(sorting_input_field, str):
                sorting_fields = [sorting_input_field.lower()]
            elif isinstance(sorting_input_field, (list, tuple)):
                sorting_fields = sorting_input_field

        return sorting_fields, sort_dir

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

    def get_cursor_filter(self):
        cursor_values = self.from_cursor(self.cursor)
        operator_map = {
            "after": {"asc": ">", "desc": "<"},
            "before": {"asc": "<", "desc": ">"},
        }
        operator = operator_map["after"][self.original_sort_dir] \
            if self.after else operator_map["before"][self.original_sort_dir]

        def format_column_name(column):
            if "." in column:
                return column
            meta = frappe.get_meta(self.doctype)
            return f"`tab{self.doctype}`.{column}" if column in \
                meta.get_valid_columns() else column

        def db_escape(v):
            return frappe.db.escape(v)

        or_conditions = []
        for index, field_name in enumerate(self.sorting_fields):
            if cursor_values[index] is None and operator == ">":
                continue

            and_conditions = []
            for cursor_id, cursor_value in enumerate(cursor_values[:index]):
                and_conditions.append(
                    f"{format_column_name(self.sorting_fields[cursor_id])} = "
                    + f"{db_escape(cursor_value)}")

            if operator == ">":
                and_conditions.append(
                    f"({format_column_name(field_name)} "
                    + f"{operator} {db_escape(cursor_values[index])} OR "
                    + f"{format_column_name(field_name)} IS NULL)")
            elif cursor_values[index] is not None:
                and_conditions.append(
                    f"{format_column_name(field_name)} "
                    + f"{operator} {db_escape(cursor_values[index])}"
                )
            else:
                and_conditions.append(
                    f"{format_column_name(field_name)} IS NOT NULL"
                )

            or_conditions.append("({})".format(" AND ".join(and_conditions)))

        return " OR ".join(or_conditions)

    def to_cursor(self, row, sorting_fields):
        # sorting_fields could be [custom_table.field_1],
        # where only field_1 will be available on row
        _json = frappe.as_json([row.get(x.split('.')[1] if '.' in x else x)
                                for x in sorting_fields])
        return frappe.safe_decode(base64.b64encode(_json.encode("utf-8")))

    def from_cursor(self, cursor):
        return frappe.parse_json(frappe.safe_decode(base64.b64decode(cursor)))
