import frappe

from frappe_graphql.utils.check_permissions import check_permissions


def delete_doc(doctype: str, name: str):
    check_permissions(doctype, name, ["delete"])
    doc = frappe.get_cached_doc(doctype, name)
    doc.delete()
