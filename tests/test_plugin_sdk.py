from core.plugin_sdk import PluginRouter


def test_plugin_router_decorator():
    router = PluginRouter()

    @router.route("ping")
    def handle_ping(params):
        return {"reply": "pong", "echo": params.get("msg")}

    @router.route
    def hello(params):
        return {"greeting": f"Hello {params.get('name')}"}

    @router.route("no_args")
    def no_args_handler():
        return {"ok": True}

    assert "ping" in router.get_registered_actions()
    assert "hello" in router.get_registered_actions()
    assert "no_args" in router.get_registered_actions()

    # Dispatch ping
    res1 = router.dispatch("ping", {"msg": "hi"})
    assert res1 == {"reply": "pong", "echo": "hi"}

    # Dispatch hello
    res2 = router.dispatch("hello", {"name": "World"})
    assert res2 == {"greeting": "Hello World"}

    # Dispatch no_args
    res3 = router.dispatch("no_args")
    assert res3 == {"ok": True}

    # Dispatch unknown action
    res4 = router.dispatch("unknown_action")
    assert "error" in res4
