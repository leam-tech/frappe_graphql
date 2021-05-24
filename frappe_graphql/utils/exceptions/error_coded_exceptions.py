import frappe
from typing import List


class GQLExecutionUserError(Exception):
    error_code = "UNKNOWN_ERROR"
    message = "Unknown Error"

    def as_dict(self):
        return frappe._dict(
            error_code=self.error_code,
            message=self.message
        )


class GQLExecutionUserErrorMultiple(Exception):
    errors: List[GQLExecutionUserError] = []

    def __init__(self, errors: List[GQLExecutionUserError] = []):
        self.errors = errors

    def as_dict_list(self):
        return [
            frappe._dict(error_code=x.error_code, message=x.message)
            for x in self.errors
        ]


def ERROR_CODED_EXCEPTIONS():
    def inner(func):
        def wrapper(*args, **kwargs):
            try:
                response = func(*args, **kwargs)
                response["error_codes"] = []
                return response
            except GQLExecutionUserError as e:
                return frappe._dict(
                    errors=[e.as_dict()]
                )
            except GQLExecutionUserErrorMultiple as e:
                return e.as_dict_list()

        return wrapper

    return inner
