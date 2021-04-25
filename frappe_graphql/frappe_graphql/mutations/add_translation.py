from graphql import GraphQLSchema, GraphQLResolveInfo

import frappe


def bind(schema: GraphQLSchema):
    schema.mutation_type.fields["addTranslation"].resolve = add_translation_resolver


def add_translation_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    language = kwargs.get("language")
    source_text = kwargs.get("source_text")
    translated_text = kwargs.get("translated_text")
    context = kwargs.get("context")
    doctype = kwargs.get("doctype")
    docname = kwargs.get("docname")
    docfield = kwargs.get("docfield")

    if doctype:
        context = doctype

    if doctype and docname:
        context += f":{docname}"

    if doctype and docfield:
        context += f":{docfield}"

    existing_tr = frappe.db.get_value("Translation", frappe._dict(
        language=language,
        source_text=source_text,
        context=context
    ))
    if existing_tr:
        frappe.set_value("Translation", existing_tr, "translated_text", translated_text)
        tr_doc = frappe.get_doc("Translation", existing_tr)
    else:
        tr_doc = frappe.get_doc(frappe._dict(
            doctype="Translation",
            language=language,
            source_text=source_text,
            translated_text=translated_text,
            context=context
        )).insert()

    return tr_doc
