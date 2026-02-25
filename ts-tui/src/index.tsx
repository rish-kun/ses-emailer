#!/usr/bin/env tsx
/**
 * SES Email TUI — Entry point
 */

import React from "react";
import { render } from "ink";
import { App } from "./App.js";
import { ToastProvider } from "./contexts/ToastContext.js";
import { shutdownApi } from "./api.js";

// Clear screen on load and set background to true black
process.stdout.write("\x1b[40m\x1b[39m\x1b[2J\x1b[3J\x1b[H");

const { waitUntilExit } = render(
    <ToastProvider>
        <App />
    </ToastProvider>
);

waitUntilExit().then(async () => {
    // Reset terminal colors and clear screen on exit
    process.stdout.write("\x1b[0m\x1b[2J\x1b[3J\x1b[H");
    // Tell the API to shut down before we exit
    await shutdownApi();
    process.exit(0);
});
