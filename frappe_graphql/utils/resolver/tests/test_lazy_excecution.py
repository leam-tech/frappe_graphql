import unittest
from unittest.mock import Mock
from frappe_graphql.utils.execution.execution_context import DeferredExecutionContext
from frappe_graphql.utils.execution.dataloader import DataLoader
from graphql import (
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLString,
    GraphQLArgument,
    GraphQLList,
    graphql_sync,
)


class TestLazyExecution(unittest.TestCase):

    def test_lazy_execution(self):

        NAMES = {
            "1": "Sarah",
            "2": "Lucy",
            "3": "Geoff",
            "5": "Dave",
        }

        def load_fn(keys):
            return [NAMES[key] for key in keys]

        mock_load_fn = Mock(wraps=load_fn)
        dataloader = DataLoader(load_fn=mock_load_fn)

        def name_resolver(root, info, key):
            return dataloader.load(key)

        schema = GraphQLSchema(
            query=GraphQLObjectType(
                name="Query",
                fields={
                    "name": GraphQLField(
                        GraphQLString,
                        args={
                            "key": GraphQLArgument(GraphQLString),
                        },
                        resolve=name_resolver,
                    )
                },
            )
        )

        result = graphql_sync(
            schema,
            """
            query {
                name1: name(key: "1")
                name2: name(key: "2")
            }
            """,
            execution_context_class=DeferredExecutionContext,
        )

        self.assertIsNone(result.errors)
        self.assertDictEqual(result.data, {"name1": "Sarah", "name2": "Lucy"})
        self.assertEqual(mock_load_fn.call_count, 1)

    def test_nested_lazy_execution(self):

        USERS = {
            "1": {
                "name": "Laura",
                "bestFriend": "2",
            },
            "2": {
                "name": "Sarah",
                "bestFriend": None,
            },
            "3": {
                "name": "Dave",
                "bestFriend": "2",
            },
        }

        def load_fn(keys):
            return [USERS[key] for key in keys]

        mock_load_fn = Mock(wraps=load_fn)
        dataloader = DataLoader(mock_load_fn)

        def resolve_user(root, info, id):
            return dataloader.load(id)

        def resolve_best_friend(user, info):
            return dataloader.load(user["bestFriend"])

        user = GraphQLObjectType(
            name="User",
            fields=lambda: {
                "name": GraphQLField(GraphQLString),
                "bestFriend": GraphQLField(user, resolve=resolve_best_friend),
            },
        )

        schema = GraphQLSchema(
            query=GraphQLObjectType(
                name="Query",
                fields={
                    "user": GraphQLField(
                        user,
                        args={
                            "id": GraphQLArgument(GraphQLString),
                        },
                        resolve=resolve_user,
                    )
                },
            )
        )

        result = graphql_sync(
            schema,
            """
            query {
                user1: user(id: "1") {
                    name
                    bestFriend {
                        name
                    }
                }
                user2: user(id: "3") {
                    name
                    bestFriend {
                        name
                    }
                }
            }
            """,
            execution_context_class=DeferredExecutionContext,
        )

        self.assertIsNone(result.errors)
        self.assertDictEqual(result.data, {
            "user1": {
                "name": "Laura",
                "bestFriend": {
                    "name": "Sarah",
                },
            },
            "user2": {
                "name": "Dave",
                "bestFriend": {
                    "name": "Sarah",
                },
            },
        })
        self.assertEqual(mock_load_fn.call_count, 2)

    def test_lazy_execution_list(self):
        USERS = {
            "1": {
                "name": "Laura",
                "bestFriend": "2",
            },
            "2": {
                "name": "Sarah",
                "bestFriend": None,
            },
            "3": {
                "name": "Dave",
                "bestFriend": "2",
            },
        }

        def load_fn(keys):
            return [USERS[key] for key in keys]

        mock_load_fn = Mock(wraps=load_fn)
        dataloader = DataLoader(mock_load_fn)

        def resolve_users(root, info):
            return [dataloader.load(id) for id in USERS.keys()]

        def resolve_best_friend(user, info):
            if user["bestFriend"]:
                return dataloader.load(user["bestFriend"])
            return None

        user = GraphQLObjectType(
            name="User",
            fields=lambda: {
                "name": GraphQLField(GraphQLString),
                "bestFriend": GraphQLField(user, resolve=resolve_best_friend),
            },
        )

        schema = GraphQLSchema(
            query=GraphQLObjectType(
                name="Query",
                fields={
                    "users": GraphQLField(
                        GraphQLList(user),
                        resolve=resolve_users,
                    )
                },
            )
        )

        result = graphql_sync(
            schema,
            """
            query {
                users {
                    name
                    bestFriend {
                        name
                    }
                }
            }
            """,
            execution_context_class=DeferredExecutionContext,
        )

        self.assertIsNone(result.errors)
        self.assertDictEqual(result.data, {
            "users": [
                {
                    "name": "Laura",
                    "bestFriend": {
                        "name": "Sarah",
                    },
                },
                {
                    "name": "Sarah",
                    "bestFriend": None,
                },
                {
                    "name": "Dave",
                    "bestFriend": {
                        "name": "Sarah",
                    },
                },
            ],
        })
        self.assertEqual(mock_load_fn.call_count, 1)
