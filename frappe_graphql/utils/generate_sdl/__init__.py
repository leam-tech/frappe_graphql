import os
import frappe

from .doctype import get_doctype_sdl

IGNORED_DOCTYPES = [
    "Installed Application",
    "Installed Applications",
]

SDL_PREDEFINED_DOCTYPES = [
    # uploadFile
    "File",

    # Owner, Modified By
    "User",

    # User
    "Gender", "Has Role", "Role Profile", "Role", "Language",

    # File.attached_to_doctype
    "DocType", "Module Def", "DocField", "DocPerm"
]


def make_doctype_sdl_files(target_dir, app=None, modules=[], doctypes=[],
                           ignore_custom_fields=False, disable_enum_selectdf=False):
    specific_doctypes = doctypes or []
    doctypes = get_doctypes(
        app=app,
        modules=modules,
        doctypes=doctypes
    )

    options = frappe._dict(
        disable_enum_selectdf=disable_enum_selectdf,
        ignore_custom_fields=ignore_custom_fields
    )

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    def write_file(filename, contents):
        target_file = os.path.join(
            target_dir, f"{frappe.scrub(filename)}.graphql")
        with open(target_file, "w") as f:
            f.write(contents)

    for doctype in doctypes:
        if doctype not in specific_doctypes and \
                (doctype in IGNORED_DOCTYPES or doctype in SDL_PREDEFINED_DOCTYPES):
            continue
        sdl = get_doctype_sdl(doctype=doctype, options=options)
        write_file(doctype, sdl)


def get_doctypes(app=None, modules=None, doctypes=[]):
    modules = list(modules or [])
    doctypes = list(doctypes or [])
    if app:
        if app not in frappe.get_installed_apps():
            raise Exception("App {} is not installed in this site".format(app))

        modules.extend([x.name for x in frappe.get_all(
            "Module Def",
            {"app_name": app}
        )])

    if modules:
        for module in modules:
            if not frappe.db.exists("Module Def", module):
                raise Exception("Invalid Module: " + module)

        doctypes.extend([x.name for x in frappe.get_all(
            "DocType",
            {"module": ["IN", modules]}
        )])

    if doctypes:
        for dt in doctypes:
            if not frappe.db.exists("DocType", dt):
                raise Exception("Invalid DocType: " + dt)
    else:
        doctypes = [x.name for x in frappe.get_all("DocType")]

    return doctypes
