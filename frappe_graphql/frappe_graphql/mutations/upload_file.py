import frappe
from graphql import GraphQLSchema, GraphQLResolveInfo


def bind(schema: GraphQLSchema):
    schema.mutation_type.fields["uploadFile"].resolve = file_upload_resolver


def file_upload_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    from frappe_graphql.utils.file import make_file_document

    file_doc = make_file_document(
        file_key=kwargs.get("file"),
        is_private=1 if kwargs.get("is_private") else 0,
        doctype=kwargs.get("attached_to_doctype"),
        docname=kwargs.get("attached_to_name"),
        fieldname=kwargs.get("fieldname"),
    )

    # Access to file-document is restricted to System Manager by default
    return frappe._dict(
        name=file_doc.get("name"),
        file_url=file_doc.get("file_url"),
        file_name=file_doc.get("file_name"),
        file_size=file_doc.get("file_size"),
        is_private=file_doc.get("is_private"),
        folder=file_doc.get("folder"),
        content_hash=file_doc.get("content_hash"),
        attached_to_doctype=file_doc.get("attached_to_doctype"),
        attached_to_name=file_doc.get("attached_to_name"),
        attached_to_field=file_doc.get("attached_to_field"),
    )
