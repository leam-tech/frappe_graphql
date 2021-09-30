from graphql import GraphQLResolveInfo, GraphQLEnumType

import frappe
from frappe.model import default_fields

from .utils import get_singular_doctype


def document_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    doctype = obj.get('doctype') or get_singular_doctype(info.parent_type.name)
    if not doctype:
        return None

    try:
        # In the case when object signature lead into document resolver
        # But the document no longer exists in database
        cached_doc = frappe.get_cached_doc(doctype, obj.get("name"))

        # Permission check after the document is confirmed to exist
        # verbose check of is_owner of doc
        frappe.has_permission(doctype=doctype, doc=cached_doc, throw=True)
        role_permissions = frappe.permissions.get_role_permissions(doctype)
        if role_permissions.get("if_owner", {}).get("read"):
            if cached_doc.get("owner") != frappe.session.user:
                frappe.throw(
                    frappe._("No permission for {0}").format(
                        doctype + " " + obj.get("name")))
        # apply field level read perms
        cached_doc.apply_fieldlevel_read_permissions()

    except frappe.DoesNotExistError:
        cached_doc = obj

    meta = frappe.get_meta(doctype)

    df = meta.get_field(info.field_name)
    if not df:
        if info.field_name in default_fields:
            df = get_default_field_df(info.field_name)

    def _get_value(fieldname, ignore_translation=False):
        # Preference to fetch from obj first, cached_doc later
        if obj.get(fieldname) is not None:
            value = obj.get(fieldname)
        else:
            value = cached_doc.get(fieldname)

        # ignore_doc_resolver_translation might be helpful for overriding document_resolver
        # which might be a simple wrapper around this function (document_resolver)
        if not ignore_translation and isinstance(value, str) and not frappe.flags.ignore_doc_resolver_translation:
            return frappe._(value)

        return value

    if info.field_name.endswith("__name"):
        fieldname = info.field_name.split("__name")[0]
        return _get_value(fieldname)
    elif df:
        if df.fieldtype in ("Link", "Dynamic Link"):
            if not _get_value(df.fieldname):
                return None
            link_dt = df.options if df.fieldtype == "Link" else \
                _get_value(df.options)
            return frappe._dict(name=_get_value(df.fieldname), doctype=link_dt)
        elif df.fieldtype == "Select" and isinstance(info.return_type, GraphQLEnumType):
            # We allow Select fields whose returnType is just Strings
            value = _get_value(df.fieldname, ignore_translation=True) or ""
            return frappe.scrub(value).upper()

    return _get_value(info.field_name)


def get_default_field_df(fieldname):
    df = frappe._dict(
        fieldname=fieldname,
        fieldtype="Data"
    )
    if fieldname in ("owner", "modified_by"):
        df.fieldtype = "Link"
        df.options = "User"

    if fieldname == "parent":
        df.fieldtype = "Dynamic Link"
        df.options = "parenttype"

    return df
