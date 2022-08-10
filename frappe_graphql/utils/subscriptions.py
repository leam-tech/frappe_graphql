from datetime import timedelta
from graphql import GraphQLResolveInfo, ExecutionContext, DocumentNode, GraphQLField, \
    FieldNode, GraphQLError, parse

import frappe
from frappe.realtime import emit_via_redis
from frappe.utils import now_datetime, get_datetime

from frappe_graphql import get_schema

"""
Implemented similar to
https://github.com/apollographql/subscriptions-transport-ws/blob/master/PROTOCOL.md

Server --> Client Message Types:
- GQL_DATA
- GQL_COMPLETE

Only the above two are implemented as of now. Once we have a mechanism for
SocketIO -> Python communication in frappe, we can implement the complete spec
which includes types like:
- GQL_START
- GQL_STOP
- GQL_CONNECTION_ACK
- GQL_CONNECTION_KEEP_ALIVE
"""


def setup_subscription(subscription, info: GraphQLResolveInfo, variables, complete_on_error=False):
    """
    Set up a frappe task room for the subscription
    Args:
        subscription: The name of the subscription, usually the field name itself
        info: The graphql resolve info
        variables: incoming variable dict object
        complete_on_error: Stop / Send Completed Event on GQL Error

    Returns:
        Subscription info, including the subscription_id
    """
    excluded_field_nodes = filter_selection_set(info)
    variables = frappe._dict(variables)
    subscription_id = frappe.generate_hash(f"{subscription}-{frappe.session.user}", length=8)

    subscription_data = frappe._dict(
        subscribed_at=now_datetime(),
        last_ping=now_datetime(),
        variables=variables,
        subscription_id=subscription_id,
        selection_set=excluded_field_nodes,
        user=frappe.session.user,
        complete_on_error=complete_on_error
    )

    frappe.cache().hset(
        get_subscription_redis_key(subscription), subscription_id, subscription_data)

    return frappe._dict(
        subscription_id=subscription_id
    )


def get_consumers(subscription):
    """
    Gets a list of consumers subscribed to a particular subscription
    Args:
        subscription: The name of the subscription

    Returns:
        A list of consumers with their subscription info
    """
    redis_key = get_subscription_redis_key(subscription)
    consumers = frappe.cache().hgetall(redis_key)
    return consumers.values()


def notify_consumer(subscription, subscription_id, data):
    consumer = frappe.cache().hget(
        get_subscription_redis_key(subscription),
        subscription_id
    )
    if not consumer:
        return

    original_user = frappe.session.user
    frappe.set_user(consumer.user)

    execution_data = gql_transform(subscription, consumer.selection_set, data or frappe._dict())
    response = frappe._dict(
        type="GQL_DATA",
        id=subscription_id,
        payload=execution_data
    )

    room = get_task_room(subscription_id)
    emit_via_redis(
        event=subscription,
        message=response,
        room=room
    )

    if len(execution_data.get("errors") or []):
        log_error(
            subscription=subscription,
            subscription_id=subscription_id,
            output=execution_data)
        if consumer.complete_on_error:
            complete_subscription(subscription=subscription, subscription_id=subscription_id)

    frappe.set_user(original_user)


def complete_subscription(subscription, subscription_id, data=None):
    consumer = frappe.cache().hget(
        get_subscription_redis_key(subscription),
        subscription_id
    )
    if not consumer:
        return

    response = frappe._dict(
        id="GQL_COMPLETE",
        payload=data
    )

    room = get_task_room(subscription_id)
    emit_via_redis(
        event=subscription,
        message=response,
        room=room
    )
    frappe.cache().hdel(get_subscription_redis_key(subscription), subscription_id)


def notify_consumers(subscription, subscription_ids, data):
    """
    Notify a set of consumers
    Args:
        subscription: The name of the subscription
        subscription_ids: List[str] of Subscription Ids
        data: The event data to send
    """

    for id in subscription_ids:
        notify_consumer(
            subscription=subscription,
            subscription_id=id,
            data=data)


def notify_all_consumers(subscription, data):
    """
    Notify all Consumers of subscription
    Args:
        subscription: The name of the subscription
        data: The event data to send every consumer
    """
    for consumer in get_consumers(subscription):
        notify_consumer(
            subscription=subscription,
            subscription_id=consumer.subscription_id,
            data=data)


def gql_transform(subscription, selection_set, obj):
    if not obj or not isinstance(selection_set, list):
        return obj

    schema = get_schema()
    schema.query_type.fields["__subscription__"] = GraphQLField(
        type_=schema.subscription_type.fields[subscription].type
    )

    document: DocumentNode = parse("""
        query {
            __subscription__ {
                subscription_id
            }
        }
    """)
    subscription_field_node = document.definitions[0].selection_set.selections[0]
    subscription_field_node.selection_set.selections = selection_set

    exc_ctx = ExecutionContext.build(
        schema=schema,
        document=document,
    )
    data = exc_ctx.execute_operation(exc_ctx.operation, frappe._dict(__subscription__=obj))
    result = frappe._dict(exc_ctx.build_response(data).formatted)

    # Cleanup
    del schema.query_type.fields["__subscription__"]
    if result.get("data") and result.get("data").get("__subscription__"):
        result.get("data")[subscription] = result.get("data").get("__subscription__")
        del result.get("data")["__subscription__"]

    return result


def log_error(subscription, subscription_id, output):
    import traceback as tb

    consumer = frappe.cache().hget(
        get_subscription_redis_key(subscription),
        subscription_id
    )
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
        )

    tracebacks.append(f"Frappe Traceback: \n{frappe.get_traceback()}")
    if frappe.conf.get("developer_mode"):
        frappe.errprint(tracebacks)

    tracebacks = "\n==========================================\n".join(tracebacks)
    error_log = frappe.new_doc("GraphQL Error Log")
    error_log.update(frappe._dict(
        title="GraphQL Subscription Error",
        query="-- subscription --",
        operation_name=subscription,
        variables=frappe.as_json(consumer.variables),
        output=frappe.as_json(output),
        traceback=tracebacks
    ))
    error_log.insert(ignore_permissions=True)


def filter_selection_set(info: GraphQLResolveInfo):
    """
    This will clear all non subscription_id fields from the response
    Since a subscription operation type is a single root field operation,
    it is safe to assume that there is going to be only a single subscription per operation
    http://spec.graphql.org/June2018/#sec-Subscription-Operation-Definitions
    """
    from graphql import Location
    from .pyutils import unfreeze

    excluded_field_nodes = []

    def _should_include(field_node: FieldNode):
        if not field_node.name:
            # Unknown field_node type
            return True
        if field_node.name.value == "subscription_id":
            return True

        # Location is a highly nested AST type
        excluded_field_nodes.append(unfreeze(field_node, ignore_types=[Location]))
        return False

    info.field_nodes[0].selection_set.selections = [
        x for x in info.field_nodes[0].selection_set.selections if _should_include(x)]

    return excluded_field_nodes


def remove_inactive_consumers():
    """
    Removes Inactive Consumers if they don't send in a ping
    within the THRESHOLD_MINUTES time
    """

    THRESHOLD_MINUTES = 5

    schema = get_schema()
    for subscription in schema.subscription_type.fields.keys():
        to_remove = []
        for consumer in frappe.cache().hkeys(get_subscription_redis_key(subscription)):
            subscription_info = frappe.cache().hget(
                get_subscription_redis_key(subscription), consumer)

            should_remove = True
            if subscription_info.last_ping:
                last_ping = get_datetime(subscription_info.last_ping)
                if last_ping + timedelta(minutes=THRESHOLD_MINUTES) >= now_datetime():
                    should_remove = False

            if should_remove:
                to_remove.append(consumer)

        if len(to_remove):
            frappe.cache().hdel(
                get_subscription_redis_key(subscription), *to_remove)


@frappe.whitelist(allow_guest=True)
def subscription_keepalive(subscription, subscription_id):
    schema = get_schema()
    if subscription not in schema.subscription_type.fields:
        frappe.throw("{} is not a valid subscription".format(subscription))

    subscription_info = frappe.cache().hget(
        get_subscription_redis_key(subscription), subscription_id)

    if not subscription_info:
        frappe.throw(
            "No consumer: {} registered for subscription: {}".format(
                subscription_id, subscription))

    subscription_info.last_ping = now_datetime()
    frappe.cache().hset(
        get_subscription_redis_key(subscription), subscription_id, subscription_info)

    return subscription_info


def get_subscription_redis_key(name):
    return f"gql_subscription_{name}"


def get_task_room(task_id):
    return f"{frappe.local.site}:task_progress:{task_id}"
