"""Application handlers package.

Importing this package executes the handler modules, which populates the
module-level registry via the `@command_handler` / `@query_handler` decorators.
"""

from application.handlers import get_order, place_order

__all__ = ["get_order", "place_order"]
