from typing import List
import frappe
from frappe.model import default_fields, no_value_fields
from frappe.model.meta import Meta


def get_allowed_fieldnames_for_doctype(doctype: str, parent_doctype: str = None):
    """
    Gets a list of fieldnames that's allowed for the current User to
    read on the specified doctype. This includes default_fields
    """
    _from_locals = _get_allowed_fieldnames_from_locals(doctype, parent_doctype)
    if _from_locals is not None:
        return _from_locals

    fieldnames = list(default_fields)
    fieldnames.remove("doctype")

    meta = frappe.get_meta(doctype)
    has_access_to = _get_permlevel_read_access(meta=frappe.get_meta(parent_doctype or doctype))
    if not has_access_to:
        return []

    for df in meta.fields:
        if df.fieldtype in no_value_fields:
            continue

        if df.permlevel is not None and df.permlevel not in has_access_to:
            continue

        fieldnames.append(df.fieldname)

    _set_allowed_fieldnames_to_locals(
        allowed_fields=fieldnames,
        doctype=doctype,
        parent_doctype=parent_doctype
    )

    return fieldnames


def is_field_permlevel_restricted_for_doctype(
        fieldname: str, doctype: str, parent_doctype: str = None):
    """
    Returns a boolean when the given field is restricted for the current User under permlevel
    """
    meta = frappe.get_meta(doctype)
    if meta.get_field(fieldname) is None:
        return False

    allowed_fieldnames = get_allowed_fieldnames_for_doctype(
        doctype=doctype, parent_doctype=parent_doctype)
    if fieldname not in allowed_fieldnames:
        return True

    return False


def _get_permlevel_read_access(meta: Meta):
    if meta.istable:
        return [0]

    ptype = "read"
    _has_access_to = []
    roles = frappe.get_roles()
    for perm in meta.permissions:
        if perm.get("role") not in roles or not perm.get(ptype):
            continue

        if perm.get("permlevel") in _has_access_to:
            continue

        _has_access_to.append(perm.get("permlevel"))

    return _has_access_to


def _get_allowed_fieldnames_from_locals(doctype: str, parent_doctype: str = None):

    if not hasattr(frappe.local, "permlevel_fields"):
        frappe.local.permlevel_fields = dict()

    k = doctype
    if parent_doctype:
        k = (doctype, parent_doctype)

    return frappe.local.permlevel_fields.get(k)


def _set_allowed_fieldnames_to_locals(
        allowed_fields: List[str],
        doctype: str,
        parent_doctype: str = None):

    if not hasattr(frappe.local, "permlevel_fields"):
        frappe.local.permlevel_fields = dict()

    k = doctype
    if parent_doctype:
        k = (doctype, parent_doctype)

    frappe.local.permlevel_fields[k] = allowed_fields
