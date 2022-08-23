## Access Field Linked Documents in nested queries

All Link fields return respective doc. Add `__name` suffix to the link field name to get the link name.

### Query

```gql
{
  ToDo(limit_page_length: 1) {
    name
    priority
    description
    assigned_by__name
    assigned_by {
      full_name
      roles {
        role__name
        role {
          name
          creation
        }
      }
    }
  }
}
```

### Result

```json
{
    "data": {
        "ToDo": [
            {
                "name": "ae6f39845b",
                "priority": "Low",
                "description": "<div class=\"ql-editor read-mode\"><p>Do this</p></div>",
                "assigned_by__name": "Administrator",
                "assigned_by": {
                    "full_name": "Administrator",
                    "roles": [
                        {
                            "role__name": "System Manager",
                            "role": {
                                "name": "System Manager",
                                "creation": "2021-02-02 08:34:42.170306",
                            }
                        }
                    ]
                }
            }
            ...
        ]
    }
}
```
