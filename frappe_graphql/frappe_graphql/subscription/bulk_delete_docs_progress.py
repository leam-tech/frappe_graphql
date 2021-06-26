import frappe
from graphql import GraphQLSchema, GraphQLResolveInfo
from frappe_graphql import setup_subscription, get_consumers, notify_consumer
from frappe import _

BULK_DELETE_DOCS_SUBSCRIPTION = "bulkDeleteDocsProgress"


def bind(schema: GraphQLSchema):
    schema.subscription_type.fields[
        "bulkDeleteDocsProgress"].resolve = bulk_delete_docs_progress_resolver


def bulk_delete_docs_progress_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    doctype = kwargs.get("doctype")
    if not frappe.db.exists("DocType", doctype):
        frappe.throw(_("Invalid argument"))
    frappe.has_permission(doctype=doctype, ptype="delete", throw=True)
    return setup_subscription(
        subscription=BULK_DELETE_DOCS_SUBSCRIPTION,
        info=info,
        variables=kwargs
    )


def notify_bulk_delete_docs_progress(data: dict):
    consumers = get_consumers(subscription=BULK_DELETE_DOCS_SUBSCRIPTION)
    doctype = data.get("doctype")
    docname = data.get("docname")
    if not len(consumers):
        return
    for consumer in consumers:
        variables = frappe._dict(frappe.parse_json(consumer.variables or "{}"))
        user = consumer.user
        if variables.get("doctype") != doctype:
            continue
        doc = None
        try:
            doc = frappe.get_doc(doctype, docname)
        except Exception as exc:
            pass
        # check user permissions
        if not frappe.has_permission(doctype, "delete", doc, user, verbose=True):
            continue

        notify_consumer(subscription=BULK_DELETE_DOCS_SUBSCRIPTION,
                        subscription_id=consumer.subscription_id, data=data)
