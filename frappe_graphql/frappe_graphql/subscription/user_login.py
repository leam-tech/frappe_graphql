import frappe
from graphql import GraphQLSchema, GraphQLResolveInfo
from frappe_graphql import setup_subscription, notify_all_consumers


def bind(schema: GraphQLSchema):
    schema.subscription_type.fields["user_login"].resolve = user_login_resolver


def user_login_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    return setup_subscription(
        subscription="user_login",
        info=info,
        variables=kwargs
    )


def on_login(login_manager):
    frappe.enqueue(
        notify_all_consumers,
        enqueue_after_commit=True,
        subscription="user_login",
        data=frappe._dict(
            user=frappe._dict(doctype="User", name=login_manager.user)
        ))
