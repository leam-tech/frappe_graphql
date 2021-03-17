from typing import Any
import frappe
from graphql import GraphQLObjectType, GraphQLResolveInfo, GraphQLSchema


def default_doctype_resolver(obj: Any, info: GraphQLResolveInfo, **kwargs):
    parent_type: GraphQLObjectType = info.parent_type
    if not isinstance(info.parent_type, GraphQLObjectType):
        frappe.throw("Invalid GraphQL")

    if parent_type.name == "Query":
        # This section is executed on root query type fields
        doctype = get_doctype(info.field_name)
        if not frappe.has_permission(doctype=doctype):
            raise frappe.PermissionError("No read permission for doctype " + doctype)
        filters = frappe._dict()
        limit_start = kwargs.pop("limit_start") or 0
        limit_page_length = kwargs.pop("limit_page_length") or 20
        if kwargs and len(kwargs.keys()):
            if "filters" in kwargs:
                filters = frappe.parse_json(kwargs.get("filters"))
            else:
                filters = kwargs

        return frappe.get_list(
            doctype,
            filters=filters,
            limit_start=limit_start,
            limit_page_length=limit_page_length
        )
    elif parent_type.name in ("SET_VALUE_TYPE", "SAVE_DOC_TYPE"):
        # This section is executed on mutation return types
        return (obj or {}).get(info.field_name, None)
    elif (obj.get("doctype") and obj.get("name")) or get_doctype(parent_type.name):
        # this section is executed for Fields on DocType object types.
        doctype = obj.doctype or get_doctype(parent_type.name)
        if not doctype:
            return None

        if not frappe.has_permission(doctype=doctype):
            raise frappe.PermissionError("No read permission for doctype " + doctype)

        cached_doc = frappe.get_cached_doc(doctype, obj.name)
        if info.field_name.endswith("__doc"):
            fieldname = info.field_name.split("__doc")[0]
            linked_dt = frappe.get_meta(doctype).get("fields", fieldname)[0].options
            return frappe._dict(name=cached_doc.get(fieldname), doctype=linked_dt)
        else:
            value = cached_doc.get(info.field_name)

        return value

    try:
        # default resolver
        return (obj or {}).get(info.field_name)
    except Exception:
        return None


def get_doctype(name):
    map = getattr(frappe.local, "doctype_graphql_map", None)
    if not map:
        valid_doctypes = [x.name for x in frappe.get_all("DocType")]
        map = frappe._dict()
        for dt in valid_doctypes:
            map[dt.replace(" ", "")] = dt
        frappe.local.doctype_graphql_map = map

    return map.get(name, None)


def bind_mutation_resolvers(schema: GraphQLSchema):
    mutation_type = schema.mutation_type
    mutation_type.fields["setValue"].resolve = set_value_resolver
    mutation_type.fields["saveDoc"].resolve = save_doc_resolver

    SET_VALUE_TYPE: GraphQLObjectType = mutation_type.fields["setValue"].type
    SAVE_DOC_TYPE: GraphQLObjectType = mutation_type.fields["saveDoc"].type

    def resolve_dt(obj, info, *args, **kwargs):
        return obj.doctype.replace(" ", "")

    # setting type resolver for Abstract type (interface)
    SET_VALUE_TYPE.fields["doc"].type.of_type.resolve_type = resolve_dt
    SAVE_DOC_TYPE.fields["doc"].type.of_type.resolve_type = resolve_dt


def set_value_resolver(obj: Any, info: GraphQLResolveInfo, **kwargs):
    doctype = kwargs["doctype"]
    name = kwargs["name"]
    frappe.set_value(
        doctype=doctype,
        docname=name,
        fieldname=kwargs["fieldname"],
        value=kwargs["value"]
    )
    frappe.clear_document_cache(doctype, name)
    doc = frappe.get_doc(doctype, name).as_dict()
    return {
        "doctype": doctype,
        "name": name,
        "fieldname": kwargs["fieldname"],
        "value": kwargs["value"],
        "doc": doc
    }


def save_doc_resolver(obj: Any, info: GraphQLResolveInfo, **kwargs):
    new_doc = frappe.parse_json(kwargs["doc"])
    new_doc.doctype = kwargs["doctype"]

    if new_doc.name and frappe.db.exists(new_doc.doctype, new_doc.name):
        doc = frappe.get_doc(new_doc.doctype, new_doc.name)
    else:
        doc = frappe.new_doc(new_doc.doctype)
    doc.update(new_doc)
    doc.save()
    doc.reload()

    return {
        "doctype": doc.doctype,
        "name": doc.name,
        "doc": doc.as_dict()
    }
