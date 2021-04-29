import frappe
import graphql

from frappe_graphql.utils.loader import get_schema
from frappe_graphql.utils.resolver import default_field_resolver


@frappe.whitelist(allow_guest=True)
def execute(query=None, variables=None, operation_name=None):
    result = graphql.graphql_sync(
        schema=get_schema(),
        source=query,
        variable_values=variables,
        operation_name=operation_name,
        field_resolver=default_field_resolver,
        context_value=frappe._dict()
    )
    output = frappe._dict()
    for k in ("data", "errors"):
        if not getattr(result, k, None):
            continue
        output[k] = getattr(result, k)

    return output
