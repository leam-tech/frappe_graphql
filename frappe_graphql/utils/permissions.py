import frappe
from frappe.model import default_fields, no_value_fields
from frappe.model.meta import Meta


def get_allowed_fieldnames_for_doctype(doctype: str, parent_doctype: str = None):
    """
    Gets a list of fieldnames that's allowed for the current User to
    read on the specified doctype. This includes default_fields
    """
    fieldnames = list(default_fields) + ["\"{}\" as `doctype`".format(doctype)]
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

    return fieldnames


def _get_permlevel_read_access(meta: Meta):
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
