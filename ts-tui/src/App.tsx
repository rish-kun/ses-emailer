/**
 * Main App component — router + layout shell.
 */

import React, { useState, useCallback } from "react";
import { Box, Text, useApp, useInput, useStdout } from "ink";
import { HomeScreen } from "./screens/HomeScreen.js";
import { ConfigScreen } from "./screens/ConfigScreen.js";
import { ComposeScreen } from "./screens/ComposeScreen.js";
import { SendScreen } from "./screens/SendScreen.js";
import { HistoryScreen } from "./screens/HistoryScreen.js";
import { DraftsScreen } from "./screens/DraftsScreen.js";

export type Screen =
    | "home"
    | "config"
    | "compose"
    | "send"
    | "history"
    | "drafts";

export interface ComposeData {
    recipients: string[];
    subject: string;
    body: string;
    emailType: "html" | "text";
    attachments: string[];
}

export function App() {
    const { exit } = useApp();
    const [screen, setScreen] = useState<Screen>("home");
    const [composeData, setComposeData] = useState<ComposeData | null>(null);

    // Global key bindings
    useInput((input, key) => {
        if (key.ctrl && input === "q") {
            exit();
        }
        if (key.ctrl && input === "h") {
            console.clear();
            setScreen("home");
        }
    });

    const goToSend = useCallback((data: ComposeData) => {
        setComposeData(data);
        console.clear();
        setScreen("send");
    }, []);

    const loadDraft = useCallback((_draft: Record<string, unknown>) => {
        setComposeData({
            recipients: (_draft["recipients"] as string[]) || [],
            subject: (_draft["subject"] as string) || "",
            body: (_draft["body"] as string) || "",
            emailType: (_draft["email_type"] as "html" | "text") || "html",
            attachments: (_draft["attachments"] as string[]) || [],
        });
        console.clear();
        setScreen("compose");
    }, []);

    const renderScreen = () => {
        switch (screen) {
            case "home":
                return <HomeScreen setScreen={setScreen} />;
            case "config":
                return <ConfigScreen setScreen={setScreen} />;
            case "compose":
                return (
                    <ComposeScreen
                        setScreen={setScreen}
                        goToSend={goToSend}
                        initialData={composeData}
                    />
                );
            case "send":
                return <SendScreen setScreen={setScreen} composeData={composeData} />;
            case "history":
                return <HistoryScreen setScreen={setScreen} />;
            case "drafts":
                return <DraftsScreen setScreen={setScreen} loadDraft={loadDraft} />;
        }
    };

    return (
        <Box flexDirection="column" width="100%" minHeight={20}>
            {/* Header */}
            <Box
                borderStyle="single"
                borderColor="cyan"
                paddingX={1}
                justifyContent="space-between"
            >
                <Text bold color="cyan">
                    SES Email Sender
                </Text>
                <Text dimColor>
                    Ctrl+H Home │ Ctrl+Q Quit
                </Text>
            </Box>

            {/* Screen content */}
            <Box flexDirection="column" flexGrow={1} paddingX={1} paddingY={1}>
                {renderScreen()}
            </Box>
        </Box>
    );
}
