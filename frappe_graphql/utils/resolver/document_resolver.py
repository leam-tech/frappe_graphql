from graphql import GraphQLResolveInfo

import frappe
from frappe.model import default_fields

from .utils import get_singular_doctype


def document_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    doctype = obj.get('doctype') or get_singular_doctype(info.parent_type.name)
    if not doctype:
        return None

    frappe.has_permission(doctype=doctype, doc=obj.get("name"), throw=True)

    cached_doc = frappe.get_cached_doc(doctype, obj.get("name"))
    # verbose check of is_owner of doc
    role_permissions = frappe.permissions.get_role_permissions(doctype)
    if role_permissions.get("if_owner", {}).get("read"):
        if cached_doc.get("owner") != frappe.session.user:
            frappe.throw(frappe._("No permission for {0}").format(doctype + " " + obj.get("name")))
    # apply field level read perms
    cached_doc.apply_fieldlevel_read_permissions()
    meta = frappe.get_meta(doctype)

    df = meta.get_field(info.field_name)
    if not df:
        if info.field_name in default_fields:
            df = get_default_field_df(info.field_name)

    def _get_value(fieldname):
        # Preference to fetch from obj first, cached_doc later
        if obj.get(fieldname) is not None:
            return obj.get(fieldname)
        return cached_doc.get(fieldname)

    if info.field_name.endswith("__name"):
        fieldname = info.field_name.split("__name")[0]
        return _get_value(fieldname)
    elif df and df.fieldtype == "Link":
        if not _get_value(df.fieldname):
            return None
        return frappe._dict(name=_get_value(df.fieldname), doctype=df.options)
    else:
        value = _get_value(info.field_name)
        if df.translatable:
            return get_translated(cached_doc, info.field_name, value)

        return value


def get_default_field_df(fieldname):
    df = frappe._dict(
        fieldname=fieldname,
        fieldtype="Data"
    )
    if fieldname in ("owner", "modified_by"):
        df.fieldtype = "Link"
        df.options = "User"

    return df


def get_translated(doc, fieldname, value):
    """
    Precedence Order:
        key:doctype:name:fieldname
        key:doctype:name
        key:parenttype:parent
        key:doctype:fieldname
        key:doctype
        key:parenttype
        key
    """
    if not isinstance(value, str):
        return value

    plain_translation = frappe._(value)

    # key:doctype:name:fieldname
    field_translation = frappe._(value, context=f"{doc.doctype}:{doc.name}:{fieldname}")
    if field_translation != plain_translation:
        return field_translation

    # key:doctype:name
    doc_translation = frappe._(value, context=f"{doc.doctype}:{doc.name}")
    if doc_translation != plain_translation:
        return doc_translation

    # key:parenttype:parent
    if doc.get("parenttype") and doc.get("parent"):
        parent_translation = frappe._(value, context=f"{doc.parenttype}:{doc.parent}")
        if parent_translation != plain_translation:
            return parent_translation

    # key:doctype:fieldname
    doctype_field_translation = frappe._(value, context=f"{doc.doctype}:{fieldname}")
    if doctype_field_translation != plain_translation:
        return doctype_field_translation

    # key:doctype
    doctype_translation = frappe._(value, context=f"{doc.doctype}")
    if doctype_translation != plain_translation:
        return doctype_translation

    if doc.get("parenttype"):
        parenttype_translation = frappe._(value, context=f"{doc.parenttype}")
        if parenttype_translation != plain_translation:
            return parenttype_translation

    return plain_translation
