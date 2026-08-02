import React from "react";
import { createRoot } from "react-dom/client";
import PortfolioDashboard from "./portfolio_dashboard.jsx";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <PortfolioDashboard />
  </React.StrictMode>
);
