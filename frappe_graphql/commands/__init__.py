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
@click.option("--doctype", "-dt", multiple=True,
              help="Doctype to generate sdls for. You can specify multiple")
@pass_context
def generate_sdl(context, output_dir=None, doctype=None):
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
        make_doctype_sdl_files(target_dir=target_dir, doctypes=list(doctype))
    finally:
        frappe.destroy()


graphql.add_command(generate_sdl)
commands = [graphql]
