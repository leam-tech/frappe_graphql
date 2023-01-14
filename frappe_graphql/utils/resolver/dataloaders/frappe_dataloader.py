from graphql_sync_dataloaders import SyncDataLoader


class FrappeDataloader(SyncDataLoader):
    def dispatch_queue(self):
        """
        We hope to clear the cache after each batch load
        This is helpful when we ask for the same Document consecutively
        with Updates in between in a single request

        Eg:
        - get_doctype_dataloader("User").load("Administrator")
        - frappe.db.set_value("User", "Administrator", "first_name", "New Name")
        - get_doctype_dataloader("User").load("Administrator")

        If we do not clear the cache, the second load will return the old value
        """
        super().dispatch_queue()
        self._cache = {}
