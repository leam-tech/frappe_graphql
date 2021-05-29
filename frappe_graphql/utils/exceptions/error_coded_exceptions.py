import frappe
from typing import List


class GQLExecutionUserError(Exception):
    error_code = "UNKNOWN_ERROR"
    message = "Unknown Error"
    additional_data = frappe._dict()

    def as_dict(self):
        return frappe._dict(
            error_code=self.error_code,
            message=self.message,
            **self.additional_data
        )


class GQLExecutionUserErrorMultiple(Exception):
    errors: List[GQLExecutionUserError] = []

    def __init__(self, errors: List[GQLExecutionUserError] = []):
        self.errors = errors

    def as_dict_list(self):
        return [
            x.as_dict()
            for x in self.errors
        ]


def ERROR_CODED_EXCEPTIONS(error_key="errors"):
    def inner(func):
        def wrapper(*args, **kwargs):
            try:
                response = func(*args, **kwargs)
                response[error_key] = []
                return response
            except GQLExecutionUserError as e:
                return frappe._dict({
                    error_key: [e.as_dict()]
                })
            except GQLExecutionUserErrorMultiple as e:
                return frappe._dict({
                    error_key: e.as_dict_list()
                })

        return wrapper

    return inner
