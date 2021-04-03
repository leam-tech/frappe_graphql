import frappe
import inflect


def get_singular_doctype(name):
    map = getattr(frappe.local, "singular_doctype_graphql_map", None)
    if not map:
        valid_doctypes = [x.name for x in frappe.get_all("DocType")]
        map = frappe._dict()
        for dt in valid_doctypes:
            map[dt.replace(" ", "")] = dt
        frappe.local.singular_doctype_graphql_map = map

    return map.get(name, None)


def get_plural_doctype(name):
    map = getattr(frappe.local, "plural_doctype_graphql_map", None)
    if not map:
        p = inflect.engine()
        valid_doctypes = [x.name for x in frappe.get_all("DocType")]
        map = frappe._dict()
        for dt in valid_doctypes:
            map[p.plural(dt).replace(" ", "")] = dt
        frappe.local.plural_doctype_graphql_map = map

    return map.get(name, None)
