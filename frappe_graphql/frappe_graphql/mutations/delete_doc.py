from graphql import GraphQLSchema, GraphQLResolveInfo

import frappe


def bind(schema: GraphQLSchema):
    schema.mutation_type.fields["deleteDoc"].resolve = delete_doc_resolver


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
