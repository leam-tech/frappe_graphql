# Resolver Role Permissions

You can make use of `REQUIRE_ROLES` wrapper function to validate the Roles' of logged in User.
```py
from frappe_graphql import REQUIRE_ROLES

@REQUIRE_ROLES(role="Guest")
def ping_resolver(obj, info, **kwargs):
    return "pong
```

- You can pass in multiple roles:
    ```py
    from frappe_graphql import REQUIRE_ROLES

    @REQUIRE_ROLES(role=["Accounts User", "Accounts Manager"])
    def ping_resolver(obj, info, **kwargs):
        return "pong
    ```
- You can control the exception raised. `frappe.PermissionError` is raised by default
    ```py
    from frappe_graphql import REQUIRE_ROLES

    @REQUIRE_ROLES(role="Accounts User", exc=MyCustomException)
    def ping_resolver(obj, info, **kwargs):
        return "pong
    ```