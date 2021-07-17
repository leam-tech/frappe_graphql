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

    return file_doc
