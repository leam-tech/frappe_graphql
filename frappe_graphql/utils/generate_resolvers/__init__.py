import os

from frappe_graphql.utils.file import make_dir_safe, make_file
from frappe_graphql.utils.generate_resolvers.resolvers import edit_hooks_file, generate_functions, generate_schema_content, scan_extension_for_functions

def make_extension_dirs(paths, only_folders):
    '''
    Will make directories for all _extension file paths passed in.
    Expects absolute paths.
    '''

    hooks_edited = False

    # overall loop to deal with every path:
    for file_path in paths:

    # '''DEBUG'''
    #file_path = paths[0]
    # if True:
        doctype_name = os.path.split(file_path)[1].split("_extension")[0]
        graphql_path = os.path.split(os.path.split(file_path)[0])[0]
        up_root_path, root_name = os.path.split(os.path.split(graphql_path)[0])

        '''DEBUG PRINT'''
        # print(root_name)

        # Make base directory for doctype
        doctype_root_path = make_dir_safe(
            os.path.join(graphql_path, doctype_name+"/"))

        schema_content = ""

        if not only_folders:

            queries, mutations = scan_extension_for_functions(file_path)

            if queries != [] or mutations != []:
                schema_content = generate_schema_content(
                    queries, mutations, root_name, doctype_name)

        # Inside, make the resolvers dir, and pop down a schema.py and __init__.py file
        make_file(os.path.join(doctype_root_path, "__init__.py"), "")
        make_file(os.path.join(doctype_root_path,
                               "schema.py"), schema_content)
        resolver_root_path = make_dir_safe(
            os.path.join(doctype_root_path, "resolvers/"))

        # Inside, make the queries and mutations dir, popping down another __init__.py file
        make_file(os.path.join(resolver_root_path, "__init__.py"),
                  "from .queries import *\nfrom .mutations import *")
        query_root_path = make_dir_safe(
            os.path.join(resolver_root_path, "queries/"))
        mutation_root_path = make_dir_safe(
            os.path.join(resolver_root_path, "mutations/"))

        # Inside both, pop down __init__.py files...
        make_file(os.path.join(query_root_path, "__init__.py"), "")
        make_file(os.path.join(mutation_root_path, "__init__.py"), "")

        #...and decide if you want to genertate files
        if not only_folders:

            binding_types = []

            if queries != []:
                generate_functions(queries, query_root_path)
                binding_types.append("queries")

            if mutations != []:
                generate_functions(mutations, mutation_root_path)
                binding_types.append("mutations")

            edited = edit_hooks_file(os.path.join(up_root_path, root_name),
                            doctype_name, binding_types)

            if edited:
                hooks_edited = True

    if hooks_edited:
        print("Successfully edited hooks.py")
    else:
        print("No changes made to hooks.py")

