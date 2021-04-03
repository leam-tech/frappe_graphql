from graphql import GraphQLSchema, GraphQLObjectType, GraphQLResolveInfo

import frappe


def bind_mutation_resolvers(schema: GraphQLSchema):
    mutation_type = schema.mutation_type
    mutation_type.fields["setValue"].resolve = set_value_resolver
    mutation_type.fields["saveDoc"].resolve = save_doc_resolver
    mutation_type.fields["deleteDoc"].resolve = delete_doc_resolver

    SET_VALUE_TYPE: GraphQLObjectType = mutation_type.fields["setValue"].type
    SAVE_DOC_TYPE: GraphQLObjectType = mutation_type.fields["saveDoc"].type

    def resolve_dt(obj, info, *args, **kwargs):
        return obj.doctype.replace(" ", "")

    # setting type resolver for Abstract type (interface)
    SET_VALUE_TYPE.fields["doc"].type.of_type.resolve_type = resolve_dt
    SAVE_DOC_TYPE.fields["doc"].type.of_type.resolve_type = resolve_dt


def set_value_resolver(obj, info: GraphQLResolveInfo, **kwargs):
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


def save_doc_resolver(obj, info: GraphQLResolveInfo, **kwargs):
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


def delete_doc_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    doctype = kwargs["doctype"]
    name = kwargs["name"]
    doc = frappe.get_doc(doctype, name)
    doc.delete()
    return {
        "doctype": doctype,
        "name": name,
        "success": True
    }
