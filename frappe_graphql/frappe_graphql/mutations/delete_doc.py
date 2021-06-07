from graphql import GraphQLSchema, GraphQLResolveInfo

from frappe_graphql.utils.delete_doc import delete_doc
import frappe

def bind(schema: GraphQLSchema):
    schema.mutation_type.fields["deleteDoc"].resolve = delete_doc_resolver


def delete_doc_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    doctype = kwargs.get("doctype")
    name = kwargs.get("name")
    delete_doc(doctype, name)
    return frappe._dict({
        "doctype": doctype,
        "name": name,
        "success": True
    })
