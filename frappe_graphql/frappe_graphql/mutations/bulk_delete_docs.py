from graphql import GraphQLSchema, GraphQLResolveInfo

import frappe

from frappe_graphql.utils.delete_doc import delete_doc


def bind(schema: GraphQLSchema):
    schema.mutation_type.fields[
        "bulkDeleteDocs"].resolve = bulk_delete_docs_resolver


def bulk_delete_docs_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    dt = kwargs.get('doctype')
    docs = kwargs.get('ids', [])
    return bulk_delete_docs(dt, docs)


def bulk_delete_docs(doctype: str, docs: list):
    queued = False
    success_count = 0
    failure_count = 0
    if len(docs) >= 10:
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
        except Exception:
            frappe.db.rollback()
            failure_count += 1
    return success_count, failure_count
