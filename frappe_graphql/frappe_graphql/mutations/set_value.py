from graphql import GraphQLSchema, GraphQLResolveInfo, GraphQLObjectType

import frappe


def bind(schema: GraphQLSchema):
    schema.mutation_type.fields["setValue"].resolve = set_value_resolver

    # setting type resolver for Abstract type (interface)
    SET_VALUE_TYPE: GraphQLObjectType = schema.mutation_type.fields["setValue"].type

    def resolve_dt(obj, info, *args, **kwargs):
        return obj.doctype.replace(" ", "")

    SET_VALUE_TYPE.fields["doc"].type.of_type.resolve_type = resolve_dt


def set_value_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    doctype = kwargs.get("doctype")
    name = kwargs.get("name")
    frappe.set_value(
        doctype=doctype,
        docname=name,
        fieldname=kwargs.get("fieldname"),
        value=kwargs.get("value")
    )
    frappe.clear_document_cache(doctype, name)
    doc = frappe.get_doc(doctype, name).as_dict()
    return {
        "doctype": doctype,
        "name": name,
        "fieldname": kwargs.get("fieldname"),
        "value": kwargs.get("value"),
        "doc": doc
    }
