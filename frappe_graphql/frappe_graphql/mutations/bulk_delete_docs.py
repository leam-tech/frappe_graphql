from graphql import GraphQLSchema, GraphQLResolveInfo
import frappe
from frappe_graphql.utils.delete_doc import delete_doc
from frappe import _
from frappe_graphql.api import get_max_http_status_code, get_query
from frappe_graphql.utils.http import get_operation_name, get_masked_variables


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
                       doctype=doctype, items=docs)
    else:
        success_count, failure_count = delete_bulk(doctype, docs)
        success_count = success_count
        failure_count = failure_count
    return {"success": True if not failure_count else False, "queued": queued,
            "success_count": success_count, "failure_count": failure_count}


def delete_bulk(doctype, items):
    success_count = 0
    failure_count = 0
    error_outputs = []
    for i, d in enumerate(items):
        try:
            delete_doc(doctype, d)
            if len(items) >= 5:
                frappe.publish_realtime("progress",
                                        dict(progress=[i + 1, len(items)],
                                             title=_('Deleting {0}').format(
                                                 doctype), description=d),
                                        user=frappe.session.user)
            frappe.db.commit()
            success_count += 1
        except Exception as e:
            frappe.db.rollback()
            failure_count += 1
            error_outputs.append(e)
    if len(error_outputs):
        for error_output in error_outputs:
            query, variables, operation_name = get_query()
            log_bulk_delete_error(query, variables, operation_name,
                                  {
                                      "success": True if not failure_count else False,
                                      "queued": True if len(
                                          items) >= ENQUEUE_DOC_DELETION else False,
                                      "success_count": success_count,
                                      "failure_count": failure_count
                                  },
                                  error_output)
    return success_count, failure_count


def log_bulk_delete_error(query, variables, operation_name, graphql_output,
                          exception_cls):
    import traceback as tb
    tracebacks = f"Http Status Code: {exception_cls.http_status_code}\n\n" + \
                 f"{str(exception_cls)}\n\n" + \
                 f"{''.join(tb.format_exception(exception_cls, exception_cls, exception_cls.__traceback__))}"
    if frappe.conf.get("developer_mode"):
        frappe.errprint(tracebacks)
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
