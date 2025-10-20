"""
Utility functions to help concatenate Results
"""

from returns.result import Result, Success, Failure


def merge_results(
    a: Result[None, list[str]], b: Result[None, list[str]]
) -> Result[None, list[str]]:
    if isinstance(a, Success) and isinstance(b, Success):
        return a
    if isinstance(a, Failure) and isinstance(b, Failure):
        return Failure(a.failure() + b.failure())
    if isinstance(a, Success) and isinstance(b, Failure):
        return b
    return a
