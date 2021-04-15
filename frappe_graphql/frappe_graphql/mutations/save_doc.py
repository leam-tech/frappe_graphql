from graphql import GraphQLSchema, GraphQLResolveInfo, GraphQLObjectType

import frappe


def bind(schema: GraphQLSchema):
    schema.mutation_type.fields["saveDoc"].resolve = save_doc_resolver

    # setting type resolver for Abstract type (interface)
    SAVE_DOC_TYPE: GraphQLObjectType = schema.mutation_type.fields["saveDoc"].type

    def resolve_dt(obj, info, *args, **kwargs):
        return obj.doctype.replace(" ", "")

    SAVE_DOC_TYPE.fields["doc"].type.of_type.resolve_type = resolve_dt


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
