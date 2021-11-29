import unittest
import frappe

from frappe_graphql.graphql import get_schema, execute

"""
The following aspects of Document Resolver is tested here:
- BASIC_TESTS                   ✔️
- LINK_FIELD_TESTS              ✔️
- DYNAMIC_LINK_FIELD_TESTS      ⌛
- CHILD_TABLE_TESTS             ✔️
- SELECT_FIELD_TESTS            ✔️
- IGNORE_PERMS_TESTS
- DB_DELETED_DOC_TESTS
- TRANSLATION_TESTS

You can search for any one of the above keys to jump to related tests
"""


class TestDocumentResolver(unittest.TestCase):

    ADMIN_DOCNAME = "administrator"

    """
    BASIC_TESTS
    """

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
                "user": self.ADMIN_DOCNAME
            }
        )
        self.assertIsNone(r.get("errors"))
        self.assertIsInstance(r.get("data"), dict)
        self.assertIsInstance(r.get("data").get("User", None), dict)

        admin = r.get("data").get("User")
        self.assertEqual(admin.get("doctype"), "User")
        self.assertEqual(admin.get("name"), "administrator")
        self.assertEqual(admin.get("full_name"), "Administrator")

    """
    LINK_FIELD_TESTS
    """

    def test_link_fields(self):
        """
        Test User.language
        Set User.Administrator.language to en if not set already
        """
        if not frappe.db.get_value("User", self.ADMIN_DOCNAME, "language"):
            frappe.db.set_value("User", self.ADMIN_DOCNAME, "language", "en")

        r = execute(
            query="""
            query FetchAdmin($user: String!) {
                User(name: $user) {
                    doctype
                    name
                    email
                    full_name
                    language__name
                    language {
                        name
                        language_name
                    }
                }
            }
            """,
            variables={
                "user": self.ADMIN_DOCNAME
            }
        )
        self.assertIsNone(r.get("errors"))

        admin = r.get("data").get("User")
        self.assertIsNotNone(admin.get("language"))
        self.assertEqual(admin.get("language__name"), admin.get("language").get("name"))

        lang = admin.get("language")
        self.assertEqual(
            lang.get("language_name"),
            frappe.db.get_value("Language", lang.get("name"), "language_name")
        )

    def test_child_table_link_fields(self):
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

    """
    DYNAMIC_LINK_FIELD_TESTS
    """

    """
    CHILD_TABLE_TESTS
    """

    def test_child_table(self):
        """
        Test user.roles
        """
        r = execute(
            query="""
            query FetchAdmin($user: String!) {
                User(name: $user) {
                    doctype
                    name
                    full_name
                    roles {
                        doctype name
                        parent__name parenttype parentfield
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

        admin = r.get("data").get("User")
        for role in admin.get("roles"):
            self.assertEqual(role.get("doctype"), "Has Role")

            self.assertEqual(role.get("parenttype"), admin.get("doctype"))
            self.assertEqual(role.get("parent__name").lower(), admin.get("name").lower())
            self.assertEqual(role.get("parentfield"), "roles")

            self.assertEqual(role.get("role__name"),
                             role.get("role").get("name"))
    """
    SELECT_FIELD_TESTS
    """

    def test_simple_select(self):
        r = execute(
            query="""
            query FetchAdmin($user: String!) {
                User(name: $user) {
                    full_name
                    desk_theme
                }
            }
            """,
            variables={
                "user": "administrator"
            }
        )

        self.assertIsNone(r.get("errors"))
        admin = r.get("data").get("User")

        self.assertIn(admin.get("desk_theme"), ["Light", "Dark"])

    def test_enum_select(self):
        """
        Update SDL.User.desk_theme return type to be an Enum
        """
        from graphql import GraphQLScalarType, GraphQLEnumType
        schema = get_schema()
        user_type = schema.type_map.get("User")
        original_type = None
        if isinstance(user_type.fields.get("desk_theme").type, GraphQLScalarType):
            original_type = user_type.fields.get("desk_theme").type
            user_type.fields.get("desk_theme").type = GraphQLEnumType(
                name="UserDeskThemeType",
                values={
                    "DARK": "DARK",
                    "LIGHT": "LIGHT"
                }
            )

        r = execute(
            query="""
            query FetchAdmin($user: String!) {
                User(name: $user) {
                    full_name
                    desk_theme
                }
            }
            """,
            variables={
                "user": "administrator"
            }
        )

        self.assertIsNone(r.get("errors"))
        admin = r.get("data").get("User")

        self.assertIn(admin.get("desk_theme"), ["LIGHT", "DARK"])

        # Set back the original type
        if original_type is not None:
            user_type.fields.get("desk_theme").type = original_type

    """
    IGNORE_PERMS_TESTS
    """

    """
    DB_DELETED_DOC_TESTS
    """
    def test_deleted_doc_resolution(self):
        d = frappe.get_doc(dict(
            doctype="User",
            first_name="Example A",
            email="example_a@test.com",
            send_welcome_email=0
        )).insert()

        d.delete()

        # We cannot call Query.User(name: d.name) now since its deleted
        r = execute(
            query="""
            query FetchAdmin($user: String!) {
                User(name: $user) {
                    full_name
                    desk_theme
                }
            }
            """,
            variables={
                "user": d.name
            }
        )
        print(r)
    """
    TRANSLATION_TESTS
    """
