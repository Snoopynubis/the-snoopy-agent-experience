from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import List

from controller.mcp_tools import MCPTool, MCP_TOOLS

logger = logging.getLogger(__name__)


@dataclass
class MCPClient:
    """Bridges our static tool definitions with the official MCP client library."""

    _tool_module_name: str = "mcp.types"
    _tool_class_name: str = "Tool"

    def __post_init__(self) -> None:
        self._tool_cls = self._load_tool_class()
        if self._tool_cls is None:
            logger.warning(
                "mcp[cli] is not importable; defaulting to internal MCP tool metadata."
            )

    def build_manifest(self, tool_specs: List[MCPTool] | None = None) -> List[object]:
        specs = tool_specs or MCP_TOOLS
        if self._tool_cls is None:
            return specs  # fall back to plain dataclasses
        return [self._tool_cls(name=tool.name, description=tool.summary) for tool in specs]

    def _load_tool_class(self):
        try:
            module = importlib.import_module(self._tool_module_name)
            return getattr(module, self._tool_class_name)
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.debug("Unable to import %s.%s: %s", self._tool_module_name, self._tool_class_name, exc)
            return None


__all__ = ["MCPClient"]
