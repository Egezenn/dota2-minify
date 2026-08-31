"""Plugin SDK for Dota 2 Minify plugins.

Provides helper utilities and decorators to simplify plugin backend API development.
"""

import inspect
from typing import Any, Callable, Dict, Optional


class PluginRouter:
    """Helper router class for registering and dispatching plugin API endpoints.

    Usage:
        from core.plugin_sdk import PluginRouter

        router = PluginRouter()

        @router.route("play_sound")
        def play_sound(params: Dict[str, Any]):
            return {"status": "playing", "path": params.get("path")}

        def handle_api(action: str, params: Dict[str, Any] = None) -> Any:
            return router.dispatch(action, params)
    """

    def __init__(self) -> None:
        self._routes: Dict[str, Callable] = {}

    def route(self, action_name: Optional[Any] = None) -> Callable:
        """Decorator to register a handler function for an action name.

        Can be used as:
            @router.route("action_name")
            def my_handler(params): ...

        or as:
            @router.route
            def my_action(params): ...
        """
        if callable(action_name):
            # Used as `@router.route` without parentheses
            func = action_name
            name = func.__name__
            self._routes[name] = func
            return func

        def decorator(func: Callable) -> Callable:
            name = action_name if action_name is not None else func.__name__
            self._routes[name] = func
            return func

        return decorator

    def dispatch(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Dispatches an action to its registered handler function."""
        handler = self._routes.get(action)
        if not handler:
            return {"error": f"Unknown action '{action}'"}

        params = params or {}
        sig = inspect.signature(handler)
        if len(sig.parameters) == 0:
            return handler()
        return handler(params)

    def get_registered_actions(self) -> list:
        """Returns a list of all registered action names."""
        return list(self._routes.keys())
