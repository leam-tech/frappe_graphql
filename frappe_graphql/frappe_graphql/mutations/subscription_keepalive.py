from graphql import GraphQLSchema, GraphQLResolveInfo

import frappe
from frappe_graphql.utils.subscriptions import subscription_keepalive


def bind(schema: GraphQLSchema):
    schema.mutation_type.fields["subscriptionKeepAlive"].resolve = subscription_keepalive_resolver


def subscription_keepalive_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    response = frappe._dict(
        error=None,
        success=False
    )

    try:
        r = subscription_keepalive(
            subscription=kwargs.get("subscription"),
            subscription_id=kwargs.get("subscription_id")
        )
        response.success = True
        response.subscription_id = kwargs.get("subscription_id")
        response.subscribed_at = r.subscribed_at
        response.variables = frappe.as_json(
            r.variables) if not isinstance(
            r.variables, str) else r.variables
    except BaseException as e:
        if "is not a valid subscription" in str(e):
            response.error = "INVALID_SUBSCRIPTION"
        else:
            response.error = "SUBSCRIPTION_NOT_FOUND"

    return response
