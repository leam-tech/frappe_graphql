from os import getcwd, path
import click
import frappe
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
@click.option("--disable-enum-select-fields", is_flag=True, default=False,
              help="Disable generating GQLEnums for Frappe Select DocFields")
@click.option("--include_default_childdoctype_queries", is_flag=True, default=False,
              help="Include default queries for Child DocTypes (not recommended)")
@pass_context
def generate_sdl(
    context, output_dir=None, app=None, module=None, doctype=None,
    ignore_custom_fields=False, disable_enum_select_fields=False, include_default_childdoctype_queries=False
):
    site = get_site(context=context)
    try:
        frappe.init(site=site)
        frappe.connect()
        target_dir = frappe.get_site_path("doctype_sdls")
        if output_dir:
            if not path.isabs(output_dir):
                target_dir = path.abspath(
                    path.join(getcwd(), "../apps", output_dir))
            else:
                target_dir = output_dir
        target_dir = path.abspath(target_dir)
        print("Generating in Directory: " + target_dir)
        make_doctype_sdl_files(
            target_dir=target_dir,
            app=app,
            modules=list(module),
            doctypes=list(doctype),
            ignore_custom_fields=ignore_custom_fields,
            disable_enum_select_fields=disable_enum_select_fields,
            include_default_childdoctype_queries=include_default_childdoctype_queries
        )
    finally:
        frappe.destroy()


graphql.add_command(generate_sdl)
commands = [graphql]
