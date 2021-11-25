import unittest
from frappe_graphql.graphql import execute


class TestDocumentResolver(unittest.TestCase):
    def test_get_administrator(self):
        """
        Test basic get_doc
        """
        r = execute(
            query="""
            query FetchAdmin($user: String!) {
                User(name: $user) {
                    doctype
                    name
                    email
                    full_name
                }
            }
            """,
            variables={
                "user": "administrator"
            }
        )
        self.assertIsNone(r.get("errors"))
        self.assertIsInstance(r.get("data"), dict)
        self.assertIsInstance(r.get("data").get("User", None), dict)

        admin = r.get("data").get("User")
        self.assertEqual(admin.get("doctype"), "User")
        self.assertEqual(admin.get("name"), "administrator")
        self.assertEqual(admin.get("full_name"), "Administrator")

    def test_link_fields(self):
        """
        Test user.roles.role__name is equal to user.roles.role.name
        """
        r = execute(
            query="""
            query FetchAdmin($user: String!) {
                User(name: $user) {
                    doctype
                    name
                    full_name
                    roles {
                        role__name
                        role {
                            name
                        }
                    }
                }
            }
            """,
            variables={
                "user": "administrator"
            }
        )
        self.assertIsNone(r.get("errors"))
        self.assertIsInstance(r.get("data"), dict)
        self.assertIsInstance(r.get("data").get("User", None), dict)

        admin = r.get("data").get("User")
        for role in admin.get("roles"):
            self.assertEqual(role.get("role__name"),
                             role.get("role").get("name"))
