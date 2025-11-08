"""Navigation controller for AI backend dashboard.

Provides vim-style keyboard navigation (j/k) for table movement.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..widgets import ServiceTable

logger = logging.getLogger(__name__)


class NavigationController:
    """Handles vim-style keyboard navigation for service table.

    Attributes:
        table: ServiceTable widget to navigate
    """

    def __init__(self, table: ServiceTable) -> None:
        """Initialize navigation controller.

        Args:
            table: ServiceTable widget to control
        """
        self.table = table

    def move_next(self) -> None:
        """Move cursor to next row (vim: 'j')."""
        try:
            if self.table.cursor_coordinate.row < self.table.row_count - 1:
                self.table.move_cursor(row=self.table.cursor_coordinate.row + 1)
        except Exception as e:
            logger.debug(f"Error moving to next row: {e}")

    def move_previous(self) -> None:
        """Move cursor to previous row (vim: 'k')."""
        try:
            if self.table.cursor_coordinate.row > 0:
                self.table.move_cursor(row=self.table.cursor_coordinate.row - 1)
        except Exception as e:
            logger.debug(f"Error moving to previous row: {e}")
