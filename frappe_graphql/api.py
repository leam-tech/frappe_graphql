from graphql import GraphQLError
from typing import List

import frappe
from .graphql import execute


@frappe.whitelist(allow_guest=True)
def execute_gql_query():
    query, variables, operation_name = get_query()
    output = execute(
        query=query,
        variables=variables,
        operation_name=operation_name
    )

    frappe.local.response = output
    if len(output.get("errors", [])):
        frappe.db.rollback()
        log_error(query, variables, operation_name, output)
        frappe.local.response["http_status_code"] = get_max_http_status_code(output.get("errors"))


def get_query():
    """
    Gets Query details as per the specs in https://graphql.org/learn/serving-over-http/
    """

    query = None
    variables = None
    operation_name = None
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


def get_max_http_status_code(errors: List[GraphQLError]):
    http_status_code = 400
    for error in errors:
        exc = error.original_error

        if not exc:
            continue

        exc_status = getattr(exc, "http_status_code", 400)
        if exc_status > http_status_code:
            http_status_code = exc_status

    return http_status_code


def log_error(query, variables, operation_name, output):
    import traceback as tb
    tracebacks = []
    for idx, err in enumerate(output.errors):
        if not isinstance(err, GraphQLError):
            continue

        exc = err.original_error
        if not exc:
            continue
        tracebacks.append(
            f"GQLError #{idx}\n"
            + f"{str(err)}\n\n"
            + f"{''.join(tb.format_exception(exc, exc, exc.__traceback__))}"
            + "==========================================\n\n"
        )

    if frappe.conf.get("developer_mode"):
        frappe.errprint(f"frappe.get_traceback: {frappe.get_traceback()}")
        frappe.errprint(tracebacks)

    tracebacks = "\n\n".join(tracebacks)
    frappe.log_error(
        title="GraphQL API Error",
        message=f"""
Query: {query}
Variables: {variables}
Operation Name: {operation_name}

Output:
{output}

Tracebacks:

frappe.get_traceback():
{frappe.get_traceback()}
==========================================

GraphQLError tracebacks:
{tracebacks}
"""
    )
