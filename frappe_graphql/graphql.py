from graphql_sync_dataloaders import DeferredExecutionContext

import frappe
import graphql

from frappe_graphql.utils.loader import get_schema


@frappe.whitelist(allow_guest=True)
def execute(query=None, variables=None, operation_name=None):
    result = graphql.graphql_sync(
        schema=get_schema(),
        source=query,
        variable_values=variables,
        operation_name=operation_name if operation_name else None,
        middleware=[frappe.get_attr(cmd) for cmd in frappe.get_hooks("graphql_middlewares")],
        context_value=frappe._dict(),
        execution_context_class=DeferredExecutionContext
    )
    output = frappe._dict()
    for k in ("data", "errors"):
        if not getattr(result, k, None):
            continue
        output[k] = getattr(result, k)

    return output
