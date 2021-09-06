from os import getcwd, path
from os import listdir
from os.path import isfile, join
import click
import frappe
from frappe_graphql.utils.generate_resolvers import make_extension_dirs
from frappe_graphql.utils.generate_sdl import make_doctype_sdl_files
from frappe.commands import pass_context, get_site


@click.group()
def graphql():
    pass


@click.command("generate_sdl")
@click.option("--output-dir", "-o", help="Directory to which to generate the SDLs")
@click.option("--app", help="Name of the app whose doctype sdls need to be generated")
@click.option("--module", "-m", multiple=True,
              help="Name of the module whose doctype sdls need to be generated")
@click.option("--doctype", "-dt", multiple=True,
              help="Doctype to generate sdls for. You can specify multiple")
@click.option("--ignore-custom-fields", is_flag=True, default=False,
              help="Ignore custom fields generation")
@pass_context
def generate_sdl(
    context, output_dir=None, app=None, module=None, doctype=None,
    ignore_custom_fields=False
):
    site = get_site(context=context)
    try:
        frappe.init(site=site)
        frappe.connect()
        target_dir = frappe.get_site_path("doctype_sdls")
        if output_dir:
            if not path.isabs(output_dir):
                target_dir = path.abspath(path.join(getcwd(), "../apps", output_dir))
            else:
                target_dir = output_dir
        target_dir = path.abspath(target_dir)
        print("Generating in Directory: " + target_dir)
        make_doctype_sdl_files(
            target_dir=target_dir,
            app=app,
            modules=list(module),
            doctypes=list(doctype),
            ignore_custom_fields=ignore_custom_fields
        )
    finally:
        frappe.destroy()


graphql.add_command(generate_sdl)


# TODO: Option to generate folder strcutres for a manually typed, custom doctype (even if _extension doesn't exist)
# TODO: Option to add controller dirs based on queries and mutations; can start by adding them as comments
# TODO: Consider skipping an _extension file if it doesn't have queries/mutations in it
@click.command("generate_resolvers")
@click.option("--app", "-ap", help="All _extensions in the app will have bindings generated.")
@click.option("--module", "-m", multiple=True, help="All _extensions in the modules(s) will have bindings generated.")
@click.option("--doctype", "-dt", multiple=True, help="Specify exact doctype(s) to generate binding for.")
@click.option("--only-folders", is_flag=True, default=False, help="Only generate the folders (No function files)")
@pass_context
def generate_resolvers(context, app=None, module=None, doctype=None, only_folders=False):
    '''
    Will generate /doc_type/reslovers/queries&mutations folder structure for every app in the site

    If app is defined, it will restrict to that app. If modules are given, it will be restricted to 
    only doctypes in those modules. Doctype names can be given to restrict to those doctypes specifically.
    Only one type (app/module/doctype) is allowed in one command.
    '''

    given_app = app
    given_modules = list(module)
    given_doctypes = list(doctype)

    type_option_count = 0
    if given_app:
        type_option_count += 1
    if len(given_modules) > 0:
        type_option_count += 1
    if len(given_doctypes) > 0:
        type_option_count += 1

    if type_option_count > 1:
        print("Can only specify one type (app or modules or doctypes). Exiting...")
        exit()

    module_paths = []

    site = get_site(context=context)
    try:
        frappe.init(site=site)
        frappe.connect()

        site_apps = frappe.get_installed_apps()

        if site_apps == []:
            print('No apps installed on this site. Exiting...')
            exit()

        '''DEBUG PRINT'''
        # print("installed apps:", frappe.get_installed_apps())

        # If app option was given
        if given_app:
            if given_app not in site_apps:
                print(
                    f'No app named {given_app} installed on this site. Exiting...')
                exit()
            selected_apps = [given_app]
        else:
            selected_apps = site_apps

        # If module option was given, try to find the module in the apps, otherwise find all modules in apps
        if len(given_modules) != 0:

            '''DEBUG PRINT'''
            # print("Got module option(s):", given_modules)

            for given_module in given_modules:

                # To check if any module was found
                number_of_module_paths = len(module_paths)

                for selected_app in selected_apps:
                    if given_module in frappe.get_module_list(selected_app):

                        if frappe.scrub(given_module) == selected_app:
                            # If module name is same as app, use the app root folder (because of convention)
                            module_paths.append(
                                path.join(frappe.get_app_path(selected_app)))
                        else:
                            module_paths.append(
                                frappe.get_module_path(given_module))

                if len(module_paths) == number_of_module_paths:
                    print(
                        f'No module named {given_module} found in any apps. Exiting...')
                    exit()
        else:
            for selected_app in selected_apps:
                app_modules = frappe.get_module_list(selected_app)
                for app_module in app_modules:

                    if frappe.scrub(app_module) == selected_app:
                        # If module name is same as app, use the app root folder (because of convention)
                        module_paths.append(
                            path.join(frappe.get_app_path(selected_app)))
                    else:
                        module_paths.append(frappe.get_module_path(app_module))

        '''DEBUG PRINT'''
        # print("All filtered module paths:")

        # Prune the modules so only relevant modules are left i.e: module paths with graphql/types folders in them
        valid_paths = []
        for module_path in module_paths:
            types_path = path.join(module_path, 'graphql/types')

            '''DEBUG PRINT'''
            # print("path: ", types_path)

            if path.exists(types_path):
                valid_paths.append(types_path)

                '''DEBUG PRINT'''
                # print("Valid path: ", types_path)

        '''DEBUG PRINT'''
        # print("All valid paths:")
        # for valid_path in valid_paths:
        #     print(valid_path)

        extension_file_paths = []
        # If doctypes given, only check for those doctypes; 
        # if --only-folder is true, skip all checks
        # otherwise include all files ending in _extension.graphql
        if len(given_doctypes) != 0 and not only_folders:

            '''DEBUG PRINT'''
            # print("Got doctype option(s):", given_doctypes)

            for i in given_doctypes:
                given_doctypes.append(frappe.scrub(
                    given_doctypes.pop() + "_extension.graphql"))

            '''DEBUG PRINT'''
            # print(given_doctypes)

            # For all files in all valid_paths, return the path+filename if:
            # 1. It's a file (listdir also lists the directories)
            # 2. It's one of the given doctypes
            # 3. It has _extension in its name
            for valid_path in valid_paths:
                extension_file_paths.extend([path.join(valid_path, name)
                                             for name in listdir(valid_path)
                                             if (isfile(join(valid_path, name))
                                                 and (name in given_doctypes)
                                                 and ("_extension" in name)
                                                 )
                                             ])
        else:
            for valid_path in valid_paths:
                extension_file_paths.extend([path.join(valid_path, name)
                                             for name in listdir(valid_path)
                                             if (isfile(join(valid_path, name))
                                                 and ("_extension" in name)
                                                 )
                                             ])

        '''DEBUG PRINT'''
        # print("All final files to operate on:")
        # for file in extension_file_paths:
        #     print(file)

        if extension_file_paths == []:
            print("Found no _extension files to operate on. Exiting...")
            exit()

        make_extension_dirs(extension_file_paths, only_folders)

    finally:
        frappe.destroy()


graphql.add_command(generate_resolvers)
commands = [graphql]
