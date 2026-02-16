import React from "react";
import { createRoot } from "react-dom/client";
// streamlit-component-lib does not export StreamlitProvider; do not import it
import DocumentOutline from "./DocumentOutline";
import "./DocumentOutline.css";

const container = document.getElementById("root");
if (container) {
  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <DocumentOutline />
    </React.StrictMode>
  );
}