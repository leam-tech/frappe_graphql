def pre_load_schemas():
    """
    Can be called in https://docs.gunicorn.org/en/stable/settings.html#pre-fork
    to pre-load the all sites schema's on all workers.
    """
    from frappe.utils import get_sites
    from frappe import init_site, init, connect, get_installed_apps, destroy
    with init_site():
        sites = get_sites()

    for site in sites:
        import frappe
        frappe.local.initialised = False
        init(site=site)
        connect(site)
        if "frappe_graphql" not in get_installed_apps():
            continue
        try:
            from frappe_graphql import get_schema
            get_schema()
        except Exception:
            print(f"Failed to build schema for site {site}")
        finally:
            destroy()
