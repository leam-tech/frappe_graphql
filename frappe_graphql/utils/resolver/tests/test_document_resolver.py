import unittest
import frappe

from frappe_graphql.graphql import get_schema, execute
from graphql import GraphQLArgument, GraphQLField, GraphQLScalarType, GraphQLString, GraphQLEnumType

"""
The following aspects of Document Resolver is tested here:
- BASIC_TESTS                   ✔️
- LINK_FIELD_TESTS              ✔️
- DYNAMIC_LINK_FIELD_TESTS      ⌛
- CHILD_TABLE_TESTS             ✔️
- SELECT_FIELD_TESTS            ✔️
- IGNORE_PERMS_TESTS            ✔️
- DB_DELETED_DOC_TESTS          ✔️
- TRANSLATION_TESTS             ⌛
- OWNER / MODIFIED_BY TESTS     ⌛

You can search for any one of the above keys to jump to related tests
"""


class TestDocumentResolver(unittest.TestCase):

    ADMIN_DOCNAME = "administrator"

    def tearDown(self) -> None:
        if frappe.local.user != "Administrator":
            frappe.set_user("Administrator")

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
        self.assertEqual(admin.get("name"), "Administrator")
        self.assertEqual(admin.get("full_name"), "Administrator")

    def test_enum_type_with_doctype_name(self):
        """
        Default Resolvers are setup only for Doctype GQLTypes
        The GQLType name is used to determine if it's a DocType or not.

        There are cases where some other GQLType (eg: GQLEnumType) is named as a DocType.
        In such cases, the default resolver should not be set. Trying to set it will result in
        an error.

        We will make a GQLEnumType named "ToDo" which is a valid Frappe Doctype.
        We will try to ping on the schema to validate no errors are thrown.
        """
        from .. import setup_default_resolvers

        schema = get_schema()
        todo_enum = GraphQLEnumType(
            name="ToDo",
            values={
                "TODO": "TODO",
                "DONE": "DONE"
            }
        )
        schema.type_map["ToDo"] = todo_enum

        # Rerun setup_default_resolvers
        setup_default_resolvers(schema)

        # Run Ping! to validate schema
        r = execute(
            query="""
            query Ping {
                ping
            }
            """
        )
        self.assertIsNone(r.get("errors"))
        self.assertEqual(r.get("data").get("ping"), "pong")

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
        # Make sure the field is a String field
        schema = get_schema()
        user_type = schema.type_map.get("User")
        original_type = None
        if not isinstance(user_type.fields.get("desk_theme").type, GraphQLScalarType):
            original_type = user_type.fields.get("desk_theme").type
            user_type.fields.get("desk_theme").type = GraphQLString

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

        # Set back the original type
        if original_type is not None:
            user_type.fields.get("desk_theme").type = original_type

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
    DB_DELETED_DOC_TESTS
    """

    def test_deleted_doc_resolution(self):
        d = frappe.get_doc(dict(
            doctype="Role",
            role_name="Example A",
        )).insert()

        d.delete()

        # We cannot call Query.Role(name: d.name) now since its deleted
        schema = get_schema()
        schema.type_map["RoleDocInput"] = GraphQLScalarType(
            name="RoleDocInput"
        )
        schema.query_type.fields["EchoRole"] = GraphQLField(
            type_=schema.type_map["Role"],
            args=dict(
                role=GraphQLArgument(
                    type_=schema.type_map["RoleDocInput"]
                )
            ),
            resolve=lambda obj, info, **kwargs: kwargs.get("role")
        )

        r = execute(
            query="""
            query EchoRole($role: RoleDocInput!) {
                EchoRole(role: $role) {
                    doctype
                    name
                    role_name
                }
            }
            """,
            variables={
                "role": d
            }
        )
        resolved_doc = frappe._dict(r.get("data").get("EchoRole"))

        self.assertEqual(resolved_doc.doctype, d.doctype)
        self.assertEqual(resolved_doc.name, d.name)
        self.assertEqual(resolved_doc.role_name, d.role_name)
