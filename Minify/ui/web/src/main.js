import "./app.css";
import App from "./App.svelte";

if (window.location.protocol === "http:" || window.location.protocol === "https:") {
  const favicon = document.createElement("link");
  favicon.rel = "icon";
  favicon.href = "/favicon.ico";
  favicon.type = "image/x-icon";
  document.head.appendChild(favicon);
}

if (!window.pywebview && (window.location.protocol === "http:" || window.location.protocol === "https:")) {
  const api = /** @type {NonNullable<Window["pywebview"]>["api"]} */ (
    new Proxy(
      {},
      {
        get:
          (_target, method) =>
          /** @param {...any} args */
          async (...args) => {
            const body = JSON.stringify({ method, args });
            let response;
            // The app-mode browser can drop the first requests while it is still
            // starting up ("TypeError: Failed to fetch"), so retry network errors.
            for (let attempt = 0; ; attempt++) {
              try {
                response = await fetch("/api", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body,
                });
                break;
              } catch (err) {
                if (!(err instanceof TypeError) || attempt >= 9) throw err;
                await new Promise((resolve) => setTimeout(resolve, 100 * (attempt + 1)));
              }
            }
            const payload = await response.json();
            if (!response.ok || payload.error) {
              throw new Error(payload.error || `API request failed: ${response.status}`);
            }
            return payload.result;
          },
      },
    )
  );
  window.pywebview = { api };
}

const target = document.getElementById("app");
if (!target) throw new Error("Missing #app element");

const app = new App({ target });

export default app;
