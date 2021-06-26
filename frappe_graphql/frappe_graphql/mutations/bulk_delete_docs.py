from frappe.utils import flt
from graphql import GraphQLSchema, GraphQLResolveInfo
import frappe
from frappe_graphql.utils.delete_doc import delete_doc
from frappe import _
from frappe_graphql.api import get_max_http_status_code, get_query
from frappe_graphql.utils.http import get_operation_name, get_masked_variables
from frappe_graphql.frappe_graphql.subscription.bulk_delete_docs_progress import \
    notify_bulk_delete_docs_progress


def bind(schema: GraphQLSchema):
    schema.mutation_type.fields[
        "bulkDeleteDocs"].resolve = bulk_delete_docs_resolver


def bulk_delete_docs_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    dt = kwargs.get('doctype')
    docs = kwargs.get('ids', [])
    return bulk_delete_docs(dt, docs)


ENQUEUE_DOC_DELETION = 10


def bulk_delete_docs(doctype: str, docs: list):
    queued = False
    success_count = 0
    failure_count = 0
    if len(docs) >= ENQUEUE_DOC_DELETION:
        queued = True
        frappe.enqueue(delete_bulk,
                       doctype=doctype, items=docs, get_query=get_query())
    else:
        success_count, failure_count = delete_bulk(doctype, docs,
                                                   get_query=get_query())
        success_count = success_count
        failure_count = failure_count
    return {"success": True if not failure_count else False, "queued": queued,
            "success_count": success_count, "failure_count": failure_count}


def delete_bulk(doctype, items, get_query):
    success_count = 0
    failure_count = 0
    error_outputs = []
    for i, d in enumerate(items):
        try:
            delete_doc(doctype, d)
            frappe.db.commit()
            success_count += 1
            send_bulk_delete_progress(doctype, d, True, success_count, failure_count, len(items))
        except Exception as e:
            frappe.db.rollback()
            failure_count += 1
            send_bulk_delete_progress(doctype, d, False, success_count, failure_count, len(items))
            error_outputs.append(e)
    if len(error_outputs):
        query, variables, operation_name = get_query
        log_bulk_delete_error(query, variables, operation_name,
                              {
                                  "success": True if not failure_count else False,
                                  "queued": True if len(
                                      items) >= ENQUEUE_DOC_DELETION else False,
                                  "success_count": success_count,
                                  "failure_count": failure_count
                              },
                              error_outputs)
    return success_count, failure_count


def log_bulk_delete_error(query, variables, operation_name, graphql_output,
                          error_outputs):
    tracebacks = get_bulk_delete_tracebacks(error_outputs)
    error_log = frappe.new_doc("GraphQL Error Log")
    error_log.update(frappe._dict(
        title="GraphQL API Error",
        operation_name=get_operation_name(query, operation_name),
        query=query,
        variables=frappe.as_json(
            get_masked_variables(query, variables)) if variables else None,
        output=frappe.as_json(graphql_output),
        traceback=tracebacks
    ))
    error_log.insert(ignore_permissions=True)


def get_bulk_delete_tracebacks(error_outputs):
    import traceback as tb
    tracebacks = [f"Total BulkDeleteErrors : {len(error_outputs)}"]
    for idx, error_output in enumerate(error_outputs):
        tracebacks.append(
            f"BulkDeleteError #{idx}\n"
            f"Http Status Code: {error_output.http_status_code}\n\n" + \
            f"{str(error_output)}\n\n" + \
            f"{''.join(tb.format_exception(error_output, error_output, error_output.__traceback__))}")
    tracebacks = "\n==========================================\n".join(
        tracebacks)
    if frappe.conf.get("developer_mode"):
        frappe.errprint(tracebacks)
    return tracebacks


def send_bulk_delete_progress(doctype: str, docname: str, success: bool, success_count: int,
                              failure_count: int, total_count: int):
    data = frappe._dict(doctype=doctype, docname=docname, success=success,
                        success_count=success_count, failure_count=failure_count,
                        total_count=total_count,
                        progress=flt((success_count + failure_count) / total_count * 100,
                                     precision=2))
    notify_bulk_delete_docs_progress(data)
