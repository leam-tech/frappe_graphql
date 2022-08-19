from unittest import TestCase
from unittest.mock import patch

import frappe
from frappe.model import no_value_fields, default_fields

from ..permissions import get_allowed_fieldnames_for_doctype


class TestGetAllowedFieldNameForDocType(TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def test_admin_on_user(self):
        """
        Administrator on User doctype
        """
        meta = frappe.get_meta("User")
        fieldnames = get_allowed_fieldnames_for_doctype("User")
        self.assertCountEqual(
            fieldnames,
            [x.fieldname for x in meta.fields if x.fieldtype not in no_value_fields]
            + [x for x in default_fields if x != "doctype"]
            + ["\"{}\" as doctype".format(meta.name)]
        )

    def test_permlevels_on_user(self):
        frappe.set_user("Guest")

        # Guest is given permlevel=0 access on User DocType
        user_meta = self._get_custom_user_meta()

        with patch("frappe.get_meta") as get_meta_mock:
            get_meta_mock.return_value = user_meta
            fieldnames = get_allowed_fieldnames_for_doctype(user_meta.name)

        self.assertCountEqual(
            fieldnames,
            [x.fieldname for x in user_meta.fields
                if x.permlevel == 1 and x.fieldtype not in no_value_fields]
            + [x for x in default_fields if x != "doctype"]
            + ["\"{}\" as doctype".format(user_meta.name)]
        )

        # Clear meta_cache for User doctype
        del frappe.local.meta_cache["User"]

    def test_on_child_doctype(self):
        fieldnames = get_allowed_fieldnames_for_doctype("Has Role", parent_doctype="User")
        meta = frappe.get_meta("Has Role")
        self.assertCountEqual(
            fieldnames,
            [x.fieldname for x in meta.fields if x.fieldtype not in no_value_fields]
            + [x for x in default_fields if x != "doctype"]
            + ["\"{}\" as doctype".format(meta.name)]
        )

    def test_on_child_doctype_with_no_parent_doctype(self):
        fieldnames = get_allowed_fieldnames_for_doctype("Has Role")
        self.assertEqual(fieldnames, [])

    def _get_custom_user_meta(self):
        meta = frappe.get_meta("User")
        meta.permissions.append(dict(
            role="Guest",
            read=1,
            permlevel=1
        ))

        meta.get_field("full_name").permlevel = 1

        return meta
