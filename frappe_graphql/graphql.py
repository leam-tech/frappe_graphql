import frappe
import graphql

from frappe_graphql.utils.loader import load_schema_from_path
from frappe_graphql.utils.resolver import default_doctype_resolver


def get_schema():
    target_dir = frappe.get_site_path("doctype_sdls")
    schema = load_schema_from_path(target_dir)

    ast_doc = graphql.parse(schema)
    schema = graphql.build_ast_schema(ast_doc)
    return schema


@frappe.whitelist(allow_guest=True)
def execute(query=None, variables=None, operation_name=None):
    query, variables, operation_name = get_query(
        query=query,
        variables=variables,
        operation_name=operation_name
    )
    result = graphql.graphql_sync(
        schema=get_schema(),
        source=query,
        variable_values=variables,
        operation_name=operation_name,
        field_resolver=default_doctype_resolver
    )
    output = frappe._dict()
    for k in ("data", "errors"):
        if not getattr(result, k, None):
            continue
        output[k] = getattr(result, k)

    if hasattr(frappe.local, "request"):
        frappe.local.response = output
    else:
        return output


def get_query(query, variables, operation_name):
    """
    Gets Query details as per the specs in https://graphql.org/learn/serving-over-http/
    """
    if query:
        return query, variables, operation_name

    if not hasattr(frappe.local, "request"):
        return query, variables, operation_name

    from werkzeug.wrappers import Request
    request: Request = frappe.local.request

    if request.method == "GET":
        query = frappe.safe_decode(request.args["query"])
        variables = frappe.safe_decode(request.args["variables"])
        operation_name = frappe.safe_decode(request.args["operation_name"])
    elif request.method == "POST":
        if "application/json" not in (request.content_type or ""):
            raise Exception("Please send in application/json")

        graphql_request = frappe.parse_json(request.get_data(as_text=True))
        query = graphql_request.query
        variables = graphql_request.variables
        operation_name = graphql_request.operationName

    return query, variables, operation_name
