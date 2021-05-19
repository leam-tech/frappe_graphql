# Subscriptions
GraphQL Spec allows us to be really flexible in choosing the transport for realtime communication. Here, frappe's existing Socket IO implementation is being used to get the same.

Our target is to have an implementation that conforms to:
https://github.com/apollographql/subscriptions-transport-ws/blob/master/PROTOCOL.md    

Server --> Client Message Types:
- GQL_DATA
- GQL_COMPLETE

Only the above two are implemented as of now. Once we have a mechanism for SocketIO -> Python communication in frappe, we can implement the complete spec
which includes types like:
- GQL_START
- GQL_STOP
- GQL_CONNECTION_ACK
- GQL_CONNECTION_KEEP_ALIVE

## Protocol Overview
1. Client will send in a GQL Subscription Query
    <details><summary>Example</summary>

    ```gql
    subscription {
        doc_events {
            subscription_id
            doctype
            name
            document {
                ... on User {
                    email
                    full_name
                }
            }
        }
    }
    ```
    </details>
2. Server will store the variables and field selections, and gives back `subscription_id` to the client
    <details><summary>Server Response Example</summary>

    ```json
    {
        "data": {
            "doc_events": {
                "subscription_id": "9cbj89kcv"
            }
        }
    }
    ```
    </details>
3. Client will have to emit `task_subscribe` with data `[subscription_id]` via SocketIO connection and listen for subscription events coming under the event name same as the subscription name
    <details><summary>Example</summary>

    ```js
    frappe.socketio.socket.emit("task_subscribe", [subscription_id]);
    frappe.socketio.socket.on("doc_events", (data) => {
        console.log("doc_events received: ", data);
    })
    ```
    </details>
4. Periodically, send in keep alive requests. You can do this in two ways, via frappe-cmd, or gql-mutation. This is mandatory, otherwise your subscription will be lost after 5minutes. So please choose an interval accordingly, perhaps every minute ?
    <details><summary>Frappe CMD Example</summary>

    ```js
    frappe.call({
        cmd: "frappe_graphql.utils.subscriptions.subscription_keepalive",
        args: {
            subscription: "doc_events",
            subscription_id: "9cbj89kcv"
        },
    })
    ```
    </details>
    <details><summary>GQL Mutation Example</summary>

    ```gql
    mutation {
        subscriptionKeepAlive(subscription: "doc_events", subscription_id: "483f4bdb") {
            error
            success
            subscribed_at
            subscription_id
            variables
        }
    }
    ```
    </details>
5. Done, wait for your subscription events.
6. By default, Subscriptions auto-complete on Error. You can change the behavior while calling `setup_subscription(complete_on_error=False)`
7. You can complete manually by calling `complete_subscription("doc_events", "a789df0")`

## Creating New Subscriptions
frappe_graphql provides a couple of subscription utility functions. They can be called to make events easily. Some of them are:
- `frappe_graphql.setup_subscription`
- `frappe_graphql.get_consumers`
- `frappe_graphql.notify_consumer`
- `frappe_graphql.notify_all_consumers`
- `frappe_graphql.complete_subscription`

Please go through the following examples to get better idea on when to use them

### Example: Doc Events
Let's make a subscription, `doc_events` which will receive doctype on_change events.

<details><summary>Implementation</summary>

#### 1. Define Subscription in SDL

`BaseSubscription` is an interface with single field, `subscription_id`

```gql
type DocEvent implements BaseSubscription {
  doctype: String!
  name: String!
  event: String!
  document: BaseDocType!
  triggered_by: User!
  subscription_id: String!
}

extend type Subscription {
    doc_events(doctypes: [String!]): DocEvent!
}
```

#### 2. Bind Resolvers

In your `graphql_schema_processors` add the py module path to the following function:
```py
from frappe_graphql import setup_subscription

def doc_events_bind(schema: GraphQLSchema):
    schema.subscription_type.fields["doc_events"].resolve = doc_events_resolver

def doc_events_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    return setup_subscription(
        subscription="doc_events",
        info=info,
        variables=kwargs
    )
```

#### 3. Define Event Source

Event source can be anything. Frappe Doc Events, or any other hooks.
For the purpose of our example, we will use `doc_events` hook

in `<app>/hooks.py` define a `doc_events['*']['on_change']` for the following function:
```py
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
        variables = frappe._dict(frappe.parse_json(consumer.variables or "{}"))
        if variables.get("doctypes") and doctype not in variables["doctypes"]:
            continue

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

```

</details>

### Example: User Login

Another example subscription that gets triggered whenever a User logs in.

<details><summary>Implementation</summary>

#### 1. Define Subscription in SDL
```gql
type UserLogin implements BaseSubscription {
  user: User
  subscription_id: String!
}


extend type Subscription {
    user_login: UserLogin!
}
```

#### 2. Bind Resolvers

In your `graphql_schema_processors` define the following function

```py
import frappe
from graphql import GraphQLSchema, GraphQLResolveInfo
from frappe_graphql import setup_subscription

def bind(schema: GraphQLSchema):
    schema.subscription_type.fields["user_login"].resolve = user_login_resolver


def user_login_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    frappe.only_for("System Manager")
    return setup_subscription(
        subscription="user_login",
        info=info,
        variables=kwargs
    )
```

#### 3. Define Event Source
in your `<app>/hooks.py` define `on_login` with the py module path of the following function:

```py
from frappe_graphql import notify_all_consumers

def on_login(login_manager):
    frappe.enqueue(
        notify_all_consumers,
        enqueue_after_commit=True,
        subscription="user_login",
        data=frappe._dict(
            user=frappe._dict(doctype="User", name=login_manager.user)
        ))
```

</details>