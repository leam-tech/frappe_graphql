import frappe
from graphql import GraphQLSchema, GraphQLResolveInfo
from frappe_graphql import setup_subscription, get_consumers, notify_consumer, get_schema
from frappe_graphql.utils.resolver import get_singular_doctype


def bind(schema: GraphQLSchema):
    schema.subscription_type.fields["doc_events"].resolve = doc_events_resolver


def doc_events_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    return setup_subscription(
        subscription="doc_events",
        info=info,
        variables=kwargs
    )


def on_change(doc, method=None):
    frappe.enqueue(
        notify_consumers,
        enqueue_after_commit=True,
        doctype=doc.doctype,
        name=doc.name,
        triggered_by=frappe.session.user
    )


def notify_consumers(doctype, name, triggered_by):
    # Verify DocType type has beed defined in SDL
    schema = get_schema()
    if not schema.get_type(get_singular_doctype(doctype)):
        return

    for consumer in get_consumers("doc_events"):
        notify_consumer(
            subscription="doc_events",
            subscription_id=consumer.subscription_id,
            data=frappe._dict(
                event="on_change",
                doctype=doctype,
                name=name,
                document=frappe._dict(
                    doctype=doctype,
                    name=name
                ),
                triggered_by=frappe._dict(
                    doctype="User",
                    name=triggered_by
                )
            ))
