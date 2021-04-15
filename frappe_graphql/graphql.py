import frappe
import graphql

from frappe_graphql.utils.loader import get_schema
from frappe_graphql.utils.resolver import default_field_resolver


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
        field_resolver=default_field_resolver
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
    content_type = request.content_type or ""

    if request.method == "GET":
        query = frappe.safe_decode(request.args["query"])
        variables = frappe.safe_decode(request.args["variables"])
        operation_name = frappe.safe_decode(request.args["operation_name"])
    elif request.method == "POST":
        # raise Exception("Please send in application/json")
        if "application/json" in content_type:
            graphql_request = frappe.parse_json(request.get_data(as_text=True))
            query = graphql_request.query
            variables = graphql_request.variables
            operation_name = graphql_request.operationName

        elif "multipart/form-data" in content_type:
            # Follows the spec here: https://github.com/jaydenseric/graphql-multipart-request-spec
            # This could be used for file uploads, single / multiple
            operations = frappe.parse_json(request.form.get("operations"))
            query = operations.get("query")
            variables = operations.get("variables")
            operation_name = operations.get("operationName")

            files_map = frappe.parse_json(request.form.get("map"))
            for file_key in files_map:
                file_instances = files_map[file_key]
                for file_instance in file_instances:
                    path = file_instance.split(".")
                    obj = operations[path.pop(0)]
                    while len(path) > 1:
                        obj = obj[path.pop(0)]

                    obj[path.pop(0)] = file_key

    return query, variables, operation_name
