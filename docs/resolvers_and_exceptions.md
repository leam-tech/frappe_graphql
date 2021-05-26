# Resolvers & Exceptions
You can wrap your resolver functions with our utility function, `ERROR_CODED_EXCEPTIONS` to automatically handle expected exceptions.

Example Query

<details><summary>Query</summary>

```gql
{
    MAGIC_DOOR(pwd: "Open Sesame!") {
        errors {
            error_code
            message
        }
        message
    }
}
```
</details>

<details><summary>Response</summary>

```json
{
    "MAGIC_DOOR": {
        "errors": [
            {
                "error_code": "DONT_YOU_KNOW_PWD_CHANGED",
                "message": "Password was changed"
            }
        ],
        "message": null
    }
}
```
</details>

<details><summary>Python</summary>

```py
import frappe
from enum import Enum
from graphql import GraphQLSchema, GraphQLField, GraphQLList, \
    GraphQLObjectType, GraphQLResolveInfo, GraphQLNonNull, GraphQLString, GraphQLEnumType

from frappe_graphql import ERROR_CODED_EXCEPTIONS, GQLExecutionUserError


class MAGIC_DOOR_ERROR_CODES(Enum):
    NOT_EVEN_CLOSE = "NOT_EVEN_CLOSE"
    DONT_YOU_KNOW_PWD_CHANGED = "DONT_YOU_KNOW_PWD_CHANGED"


def bind(schema: GraphQLSchema):
    schema.type_map["MAGIC_DOOR_ERROR_CODES"] = GraphQLEnumType(
        "MAGIC_DOOR_ERROR_CODES", MAGIC_DOOR_ERROR_CODES)

    schema.type_map["MAGIC_DOOR_ERROR_TYPE"] = GraphQLObjectType("MAGIC_DOOR_ERROR_TYPE", {
        "error_code": schema.type_map['MAGIC_DOOR_ERROR_CODES'],
        "message": GraphQLString
    })

    schema.type_map["MAGIC_DOOR_TYPE"] = GraphQLObjectType(
        "MAGIC_DOOR_TYPE",
        fields={
            "errors": GraphQLField(GraphQLList(schema.type_map['MAGIC_DOOR_ERROR_TYPE'])),
            "message": GraphQLString,
        },
    )

    schema.query_type.fields["MAGIC_DOOR"] = GraphQLField(
        type_=schema.type_map["MAGIC_DOOR_TYPE"],
        args={
            "pwd": GraphQLNonNull(GraphQLString)
        },
        resolve=magic_door_resolver)


class InvalidPassword(GQLExecutionUserError):
    error_code = MAGIC_DOOR_ERROR_CODES.NOT_EVEN_CLOSE.value


class PasswordChanged(GQLExecutionUserError):
    error_code = MAGIC_DOOR_ERROR_CODES.DONT_YOU_KNOW_PWD_CHANGED.value


@ERROR_CODED_EXCEPTIONS()
def magic_door_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    pwd = kwargs.get("pwd")
    if pwd == "Open Sesame!":
        raise PasswordChanged()
    elif pwd == "Open Noodle!":
        return frappe._dict(
            message="You get one coin!"
        )
    else:
        raise InvalidPassword()

```
</details>