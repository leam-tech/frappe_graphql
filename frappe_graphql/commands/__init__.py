import click
import frappe
from frappe_graphql.utils.generate_sdl import make_doctype_sdl_files
from frappe.commands import pass_context, get_site


@click.group()
def graphql():
    pass


@click.command("generate_sdl")
@pass_context
def generate_sdl(context):
    site = get_site(context=context)
    try:
        frappe.init(site=site)
        frappe.connect()

        target_dir = frappe.get_site_path("doctype_sdls")
        make_doctype_sdl_files(target_dir=target_dir)
    finally:
        frappe.destroy()


graphql.add_command(generate_sdl)
commands = [graphql]
