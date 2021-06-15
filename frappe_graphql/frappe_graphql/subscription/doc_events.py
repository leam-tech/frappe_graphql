import frappe
from graphql import GraphQLSchema, GraphQLResolveInfo
from frappe_graphql import setup_subscription, get_consumers, notify_consumers, get_schema
from frappe_graphql.utils.resolver import get_singular_doctype


def bind(schema: GraphQLSchema):
    schema.subscription_type.fields["doc_events"].resolve = doc_events_resolver


def doc_events_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    if frappe.session.user == "Guest":
        frappe.throw("Not Allowed for Guests")

    return setup_subscription(
        subscription="doc_events",
        info=info,
        variables=kwargs
    )


def on_change(doc, method=None):
    flags = ["in_migrate", "in_install", "in_patch",
             "in_import", "in_setup_wizard", "in_uninstall"]
    if any([getattr(frappe.flags, f, None) for f in flags]):
        return

    subscription_ids = []
    for consumer in get_consumers("doc_events"):
        doctypes = consumer.variables.get("doctypes", [])
        if len(doctypes) and doc.doctype not in doctypes:
            continue

        subscription_ids.append(consumer.subscription_id)

    if not len(subscription_ids):
        return

    # Verify DocType type has beed defined in SDL
    schema = get_schema()
    if not schema.get_type(get_singular_doctype(doc.doctype)):
        return

    frappe.enqueue(
        notify_consumers,
        enqueue_after_commit=True,
        subscription="doc_events",
        subscription_ids=subscription_ids,
        data=frappe._dict(
            event="on_change",
            doctype=doc.doctype,
            name=doc.name,
            document=frappe._dict(
                doctype=doc.doctype,
                name=doc.name
            ),
            triggered_by=frappe._dict(
                doctype="User",
                name=frappe.session.user
            )
        )
    )
