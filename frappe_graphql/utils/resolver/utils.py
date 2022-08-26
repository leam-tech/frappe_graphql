from graphql import GraphQLResolveInfo

import frappe

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
