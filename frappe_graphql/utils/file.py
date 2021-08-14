import frappe
from frappe.utils import cint
from frappe.handler import ALLOWED_MIMETYPES


def make_file_document(
        file_key, doctype=None, docname=None, fieldname=None, is_private=None,
        ignore_permissions=False):
    user = None
    if not ignore_permissions and frappe.session.user == 'Guest':
        if frappe.get_system_settings('allow_guests_to_upload_files'):
            ignore_permissions = True
        else:
            raise frappe.PermissionError("Guest uploads are not allowed")
    else:
        user = frappe.get_doc("User", frappe.session.user)

    files = frappe.request.files
    content = None
    filename = None

    if file_key in files:
        file = files[file_key]
        content = file.stream.read()
        filename = file.filename

    frappe.local.uploaded_file = content
    frappe.local.uploaded_filename = filename

    if frappe.session.user == 'Guest' or (user and not user.has_desk_access()):
        import mimetypes
        filetype = mimetypes.guess_type(filename)[0]
        if filetype not in ALLOWED_MIMETYPES:
            frappe.throw(frappe._("You can only upload JPG, PNG, PDF, or Microsoft documents."))

    ret = frappe.get_doc({
        "doctype": "File",
        "attached_to_doctype": doctype,
        "attached_to_name": docname,
        "attached_to_field": fieldname,
        "file_name": filename,
        "is_private": cint(is_private),
        "content": content
    })
    ret.save(ignore_permissions=ignore_permissions)
    return ret
