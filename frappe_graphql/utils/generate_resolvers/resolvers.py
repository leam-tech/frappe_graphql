import frappe
import os
import re


def scan_extension_for_functions(path):

    # open the file
    file = open(path, 'r')

    # replace all spaces with nothing
    contents = file.read()

    contents = contents.replace(" ", "")

    in_query_block = False
    in_mutation_block = False

    query_names = []
    mutation_names = []

    # Go through contents line by line
    for line in contents.splitlines():

        if "}" in line:
            in_query_block = False
            in_mutation_block = False

        if in_query_block:
            if line != "":
                query_names.append(re.match(r'^\w*', line).group())

        if in_mutation_block:
            if line != "":
                mutation_names.append(re.match(r'^\w*', line).group())

        if "Query" in line:
            in_query_block = True

        if "Mutation" in line:
            in_mutation_block = True

    '''DEBUG PRINT'''
    #print("Queries found: ", query_names)
    #print("Mutation found: ", mutation_names)

    return query_names, mutation_names


def generate_schema_content(queries, mutations, root_name, doc_name):

    contents = ""

    header = 'import {{root_name}}.graphql.{{doc_name}}.resolvers as {{doc_name}}_resolver\nfrom graphql import GraphQLSchema'

    binding_header = 'def bind_{{doc_name}}_{{type}}(schema: GraphQLSchema):'

    binding = '    schema.{{type}}_type.fields["{{field}}"].resolve = \\\n      {{doc_name}}_resolver.{{field_slug}}_resolver'

    contents += frappe.render_template(
        header,
        frappe._dict(root_name=root_name, doc_name=doc_name)
    )
    contents += "\n\n\n"

    if queries != []:
        contents += frappe.render_template(
            binding_header,
            frappe._dict(doc_name=doc_name, type="queries")
        )
        contents += "\n\n"
        for query in queries:
            contents += frappe.render_template(binding, frappe._dict(
                type="query",
                field=query,
                doc_name=doc_name,
                field_slug=camelCase_to_snake_case(query)
            ))
            contents += "\n\n"

    if mutations != []:
        contents += "\n"
        contents += frappe.render_template(
            binding_header,
            frappe._dict(doc_name=doc_name, type="mutations")
        )
        contents += "\n\n"

        for mutation in mutations:
            contents += frappe.render_template(binding, frappe._dict(
                type="mutation",
                field=mutation,
                doc_name=doc_name,
                field_slug=camelCase_to_snake_case(mutation)
            ))
            contents += "\n\n"

    return contents


def generate_functions(function_names, output_path):

    header = 'from graphql import GraphQLResolveInfo\n\n\n'
    function = 'def {{field}}_resolver(obj, info: GraphQLResolveInfo, **kwargs):\n    return # Your resolver implementation\n\n'
    init_entry = 'from .{{function_file}} import *\n\n'
    init_contents = ''
    init_path = os.path.join(output_path, "__init__")

    # for every query/mutation:
    for function_name in function_names:
        name = camelCase_to_snake_case(function_name)
        file_path = os.path.join(output_path, name)

        file_contents = header
        file_contents += frappe.render_template(function, frappe._dict(field=name))
        file = open(f'{file_path}.py', 'w')
        file.write(file_contents)
        file.close()

        # Make an entry in the contents of the init.py
        init_contents += frappe.render_template(init_entry, frappe._dict(function_file=name))

    # Make the init.py file
    file = open(f'{init_path}.py', 'w')
    file.write(init_contents)
    file.close()


def edit_hooks_file(root_path, doc_name, binding_types):
    '''
    Will append the binding to hooks.py

    If bindings already exists, no changes will be made.
    Returns True if changes were made, False otherwise.
    '''

    '''DEBUG PRINT'''
    #print(binding_types)

    schema_binding_line = "    \"{{root_name}}.graphql.{{doctype_name}}.schema.bind_{{doctype_name}}_{{binding_type}}\",\n\n"

    root_name = os.path.split(root_path)[1]

    try:
        file = open(os.path.join(root_path, 'hooks.py'), 'r+')
        contents = file.read()
        new_contents = ''

        lines_to_generate = []
        for binding_type in binding_types:
            lines_to_generate.append(frappe.render_template(
                schema_binding_line,
                frappe._dict(
                    root_name=root_name,
                    doctype_name=doc_name,
                    binding_type=binding_type
                )
            ))

        in_schema_block = False
        written_lines = 0
        for line in contents.splitlines(keepends=True):

            if "graphql_schema_processors" in line:
                in_schema_block = True

            # If line already exists in file, remove it from the list
            if line in lines_to_generate:
                lines_to_generate.remove(line)

            if in_schema_block and line.replace(" ", '') == "]\n":
                in_schema_block = False

                for line_to_generate in lines_to_generate:
                    new_contents += "\n"
                    new_contents += line_to_generate
                    written_lines += 1

            new_contents += line

        file.seek(0)
        file.write(new_contents)
        file.close()

        if written_lines > 0:

            '''DEBUG PRINT'''
            #print("hooks.py successfully edited.")

            return True
        else:

            '''DEBUG PRINT'''
            #print("No changes made to hooks.py")

            return False

    except Exception as e:
        file.close()
        print("Failed to edit hooks.py")
        print(e)


def camelCase_to_snake_case(string):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()
