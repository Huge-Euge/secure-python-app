"""
A module implementing a basic Result type to hold Success or Error for actions which can fail
"""

from dataclasses import dataclass, field
from typing import Any, Union


@dataclass(frozen=True)
class Result:
    """
    A container class for Success and Error types
    Not meant to be used directly
    """

    @dataclass(frozen=True)
    class Error:
        """
        Error message wrapper for results
        """

        message: str

    @dataclass(frozen=True)
    class Success:
        """
        Success value wrapper for results
        """

        value: Any = field(default=True, compare=False)

    Type = Union[Success, Error]


ManyResults = Union[Result.Success, list[Result.Error]]


def merge_many_results(many_one: ManyResults, many_two: ManyResults) -> ManyResults:
    """
    Combine two instances of ManyResults objects,
    Concatenate them if they're a list of Result.Error.
    """
    if isinstance(many_one, Result.Success):
        return many_two
    if isinstance(many_two, Result.Success):
        return many_one
    return many_one + many_two
