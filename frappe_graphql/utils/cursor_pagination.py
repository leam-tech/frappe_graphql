import base64
from graphql import GraphQLResolveInfo, GraphQLError

import frappe
from frappe_graphql.utils.permissions import get_allowed_fieldnames_for_doctype
from frappe_graphql.utils.selected_field_names import get_selected_fields_for_cursor_paginator_node


class CursorPaginator(object):
    def __init__(
            self,
            doctype,
            filters=None,
            skip_process_filters=False,
            count_resolver=None,
            node_resolver=None,
            default_sorting_fields=None,
            default_sorting_direction=None,
            extra_args=None):

        if (not count_resolver) != (not node_resolver):
            frappe.throw(
                "Please provide both count_resolver & node_resolver to have custom implementation")

        self.doctype = doctype
        self.predefined_filters = filters
        self.skip_process_filters = skip_process_filters
        self.custom_count_resolver = count_resolver
        self.custom_node_resolver = node_resolver
        self.default_sorting_fields = default_sorting_fields
        self.default_sorting_direction = default_sorting_direction

        # Extra Args are helpful for custom resolvers
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
            # We will flip hasNextPage & hasPreviousPage too
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

        # Flip! (last cursor is being used)
        if self.sort_dir != self.original_sort_dir:
            _swap_has_page = self.has_next_page
            self.has_next_page = self.has_previous_page
            self.has_previous_page = _swap_has_page
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
            fields=self.get_fields_to_fetch(doctype, filters, sorting_fields),
            filters=filters,
            order_by=f"{', '.join([f'{x} {sort_dir}' for x in sorting_fields])}",
            limit_page_length=limit
        )

    def get_fields_to_fetch(self, doctype, filters, sorting_fields):
        selected_fields = set(get_selected_fields_for_cursor_paginator_node(self.resolve_info))
        fieldnames = set(get_allowed_fieldnames_for_doctype(doctype))
        return list(set(list(selected_fields.intersection(fieldnames)) + sorting_fields))

    def get_sort_args(self, sorting_input=None):
        sort_dir = self.default_sorting_direction if self.default_sorting_direction in (
            "asc", "desc") else "desc"
        if not self.default_sorting_fields:
            meta = frappe.get_meta(self.doctype)
            if meta.istable:
                sort_dir = "asc"
                sorting_fields = ["idx", "modified"]
            else:
                sorting_fields = ["modified"]
        else:
            sorting_fields = self.default_sorting_fields

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
        """
        Inspired from
        - https://stackoverflow.com/a/38017813/2041598

        Examples:
        Cursor: {colA > A}
            -> (colA > A)

        Cursor: {colA > A, colB > B}
            -> (colA >= A AND (colA > A OR colB > B))

        Cursor: {colA > A, colB > B, colC > C}
            -> (colA >= A AND (colA > A OR (colB >= B AND (colB > B OR colC > C))))

        Cursor: {colA < A}
            -> (colA <= A OR colA IS NULL)

        Cursor: {colA < A, colB < B}
            -> (colA <= A OR colA IS NULL AND
                ((colA < A OR colA IS NULL) OR (colB < B OR colB IS NULL)))

        !! NONE Cursors !!:

        Cursor: {colA > None, colB > B}
            -> ((colA IS NULL && colB > B) OR colA IS NOT NULL)

        Cursor: {colA < None, colB < B}
            -> (colB IS NULL AND (colB < B OR colB IS NONE))
        """
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

        def _get_cursor_column_condition(operator, column, value, include_equals=False):
            if operator == ">":
                return format_column_name(column) \
                    + f" {operator}{'=' if include_equals else ''} " \
                    + db_escape(value)
            else:
                if value is None:
                    return format_column_name(column) \
                        + " IS NULL"
                return "(" \
                    + format_column_name(column) \
                    + f" {operator}{'=' if include_equals else ''} " \
                    + db_escape(value) \
                    + " OR " \
                    + format_column_name(column) \
                    + " IS NULL)"

        def _get_cursor_condition(sorting_fields, values):
            """
            Returns
            sf[0]_cnd AND (sf[0]_cnd OR (sf[1:]))
            """
            nonlocal operator

            if operator == ">" and values[0] is None:
                sub_condition = ""
                if len(sorting_fields) > 1:
                    sub_condition = _get_cursor_condition(
                        sorting_fields=sorting_fields[1:], values=values[1:])

                if sub_condition:
                    return f"(({format_column_name(sorting_fields[0])} IS NULL AND {sub_condition})" \
                        + f" OR {format_column_name(sorting_fields[0])} IS NOT NULL)"
                return ""

            condition = _get_cursor_column_condition(
                operator=operator,
                column=sorting_fields[0],
                value=values[0],
                include_equals=len(sorting_fields) > 1
            )

            if len(sorting_fields) == 1:
                return condition

            next_condition = _get_cursor_condition(
                sorting_fields=sorting_fields[1:], values=values[1:])

            if next_condition:
                if values[0] is not None:
                    condition += " AND (" + _get_cursor_column_condition(
                        operator=operator,
                        column=sorting_fields[0],
                        value=values[0]
                    )
                    condition += f" OR {next_condition})"
                else:
                    # If values[0] is none
                    # sf[0] is NULL AND (sf[1:]) condition is used
                    condition += f" AND ({next_condition})"

            return condition

        if len(self.sorting_fields) != len(cursor_values):
            frappe.throw("Invalid Cursor")

        return _get_cursor_condition(sorting_fields=self.sorting_fields, values=cursor_values)

    def to_cursor(self, row, sorting_fields):
        # sorting_fields could be [custom_table.field_1],
        # where only field_1 will be available on row
        _json = frappe.as_json([row.get(x.split('.')[1] if '.' in x else x)
                                for x in sorting_fields])
        return frappe.safe_decode(base64.b64encode(_json.encode("utf-8")))

    def from_cursor(self, cursor):
        return frappe.parse_json(frappe.safe_decode(base64.b64decode(cursor)))
