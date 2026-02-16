from dataclasses import dataclass
from typing import Any, Literal, NotRequired, TypeAlias
from typing_extensions import TypedDict, Annotated

#schemas for all datastructures used in the Agent


# schema for todo item
@dataclass
class Todo:
    """Structure for a single todo item."""

    #subtask description
    subtask: str

    #status of the todo item
    status: Literal["pending", "in_progress", "completed"]


# schema for next todo item
@dataclass
class NextTodo:
    """Schema for the next todo item to be addressed."""

    # The next todo item
    subtask: str

    instructions: str = None  # Optional instructions for the todo item

