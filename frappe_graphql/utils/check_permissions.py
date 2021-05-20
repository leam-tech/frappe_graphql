from __future__ import unicode_literals
import frappe
from frappe import _
from six import string_types


def check_permissions(doctype: str, docname: str = None, ptypes=None):
    """
    Wrapper for permission check..
    """
    doc = None
    if docname:
        doc = frappe.get_cached_doc(doctype, docname)

    def check_perms():
        role_permissions = frappe.permissions.get_role_permissions(
            doctype)
        for ptype in ptypes:
            frappe.has_permission(doctype, ptype, doc, throw=True)
            if docname:
                if role_permissions.get("if_owner", {}).get("read"):
                    if frappe.get_cached_value(doctype, docname, 'owner'
                                               ) != frappe.session.user:
                        frappe.throw(
                            _("No permission for {0}").format(
                                doctype + " " + docname))

    if ptypes is None:
        ptypes = ['read']
    if isinstance(ptypes, string_types):
        ptypes = [ptypes]
    if frappe.is_table(doctype):
        # lets check the perms of the parent..
        if not docname:
            frappe.throw(
                _("Please specify docname for child table doctype {"
                  "0}").format(doctype))
        parenttype, parent = frappe.get_cached_value(doctype, docname,
                                                     ('parenttype', 'parent'))
        doctype = parenttype
        docname = parent
        doc = frappe.get_cached_doc(doctype, docname)
        check_perms()
    else:
        check_perms()
