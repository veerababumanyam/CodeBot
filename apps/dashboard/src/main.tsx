import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

function App(): JSX.Element {
  return (
    <div>
      <h1>CodeBot Dashboard</h1>
      <p>Multi-agent autonomous software development platform</p>
    </div>
  );
}

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
