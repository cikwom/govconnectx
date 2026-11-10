import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./state/AuthContext";
import { ThemeProvider } from "./state/ThemeContext";
import { LanguageProvider } from "./state/LanguageContext";
import App from "./App";
import "./styles.css";
ReactDOM.createRoot(document.getElementById("root")!).render(<React.StrictMode><BrowserRouter><ThemeProvider><LanguageProvider><AuthProvider><App /></AuthProvider></LanguageProvider></ThemeProvider></BrowserRouter></React.StrictMode>);
