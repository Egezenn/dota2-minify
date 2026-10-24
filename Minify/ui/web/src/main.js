import "./app.css";
import App from "./App.svelte";

if (!window.pywebview) {
  const api = new Proxy(
    {},
    {
      get: (_target, method) => async (...args) => {
        const response = await fetch("/api", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ method, args }),
        });
        const payload = await response.json();
        if (!response.ok || payload.error) {
          throw new Error(payload.error || `API request failed: ${response.status}`);
        }
        return payload.result;
      },
    },
  );
  window.pywebview = { api };
}

const target = document.getElementById("app");
if (!target) throw new Error("Missing #app element");

const app = new App({ target });

export default app;
