from graphql import GraphQLResolveInfo

import frappe

from frappe_graphql.utils.permissions import is_field_permlevel_restricted_for_doctype


SINGULAR_DOCTYPE_MAP_REDIS_KEY = "singular_doctype_graphql_map"
PLURAL_DOCTYPE_MAP_REDIS_KEY = "plural_doctype_graphql_map"


def get_singular_doctype(name):
    singular_map = frappe.cache().get_value(SINGULAR_DOCTYPE_MAP_REDIS_KEY)
    if not singular_map:
        import inflect
        p = inflect.engine()

        valid_doctypes = [x.name for x in frappe.get_all("DocType")]
        singular_map = frappe._dict()
        for dt in valid_doctypes:

            # IF plural = singular, lets add a prefix: 'A'
            if p.plural(dt) == dt:
                prefix = "A"
                if dt[0].lower() in ("a", "e", "i", "o", "u"):
                    prefix = "An"

                singular_map[f"{prefix}{dt.replace(' ', '')}"] = dt
            else:
                singular_map[dt.replace(" ", "")] = dt

        frappe.cache().set_value(SINGULAR_DOCTYPE_MAP_REDIS_KEY, singular_map)

    return singular_map.get(name, None)


def get_plural_doctype(name):
    plural_map = frappe.cache().get_value(PLURAL_DOCTYPE_MAP_REDIS_KEY)
    if not plural_map:
        import inflect
        p = inflect.engine()
        valid_doctypes = [x.name for x in frappe.get_all("DocType")]
        plural_map = frappe._dict()
        for dt in valid_doctypes:
            plural_map[p.plural(dt).replace(" ", "")] = dt

        frappe.cache().set_value(PLURAL_DOCTYPE_MAP_REDIS_KEY, plural_map)

    return plural_map.get(name, None)


def get_frappe_df_from_resolve_info(info: GraphQLResolveInfo):
    return getattr(info.parent_type.fields[info.field_name], "frappe_df", None)


def field_permlevel_check(resolver):
    """
    A helper function when wrapped will check if the field
    being resolved is permlevel restricted & GQLNonNullField

    If permlevel restriction is applied on the field, None is returned.
    This will raise 'You cannot return Null on a NonNull field' error.
    This helper function will change it to a permission error.
    """
    import functools

    @functools.wraps(resolver)
    def _inner(obj, info: GraphQLResolveInfo, **kwargs):
        value = obj.get(info.field_name)
        if value is not None:
            return resolver(obj, info, **kwargs)

        # Ok, so value is None, and this field is Non-Null
        df = get_frappe_df_from_resolve_info(info)
        if not df or not df.parent:
            return

        dt = df.parent
        parent_dt = obj.get("parenttype")

        is_permlevel_restricted = is_field_permlevel_restricted_for_doctype(
            fieldname=info.field_name, doctype=dt, parent_doctype=parent_dt)

        if is_permlevel_restricted:
            raise frappe.PermissionError(frappe._(
                "You do not have read permission on field '{0}' in DocType '{1}'"
            ).format(
                info.field_name,
                "{} ({})".format(dt, parent_dt) if parent_dt else dt
            ))

        return resolver(obj, info, **kwargs)

    return _inner


def get_default_fields_docfield():
    """
    from frappe.model import default_fields are included on all DocTypes
    But, DocMeta do not include them in the fields
    """
    from frappe.model import default_fields

    def _get_default_field_df(fieldname):
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

        if fieldname in ["docstatus", "idx"]:
            df.fieldtype = "Int"

        return df

    return [
        _get_default_field_df(x) for x in default_fields
    ]
