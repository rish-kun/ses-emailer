/**
 * Home screen — polished main menu with logo and navigation.
 */

import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import { Spinner, Alert } from "@inkjs/ui";
import { healthCheck, checkCredentials, getStats } from "../api.js";
import { SectionBox } from "../components/SectionBox.js";
import type { Screen } from "../App.js";

interface Props {
    setScreen: (s: Screen) => void;
}

const LOGO = `
╔═══════════════════════════════════════════════════════════╗
║   ███████ ███████ ███████   ███    ███  █████  ██ ██      ║
║   ██      ██      ██        ████  ████ ██   ██ ██ ██      ║
║   ███████ █████   ███████   ██ ████ ██ ███████ ██ ██      ║
║        ██ ██           ██   ██  ██  ██ ██   ██ ██ ██      ║
║   ███████ ███████ ███████   ██      ██ ██   ██ ██ ██████  ║
║              AWS SES Email Sender v2.0                    ║
╚═══════════════════════════════════════════════════════════╝`;

export function HomeScreen({ setScreen }: Props) {
    const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
    const [configured, setConfigured] = useState(false);
    const [stats, setStats] = useState<Record<string, unknown> | null>(null);
    const [statusMsg, setStatusMsg] = useState("");

    useEffect(() => {
        (async () => {
            try {
                await healthCheck();
                const creds = await checkCredentials();
                setConfigured(creds.is_configured);
                try {
                    const s = await getStats();
                    setStats(s);
                } catch { }
                setStatus("ok");
            } catch (err) {
                setStatus("error");
                setStatusMsg(String(err));
            }
        })();
    }, []);

    useInput((input) => {
        const k = input.toLowerCase();
        if (k === "c") setScreen("compose");
        if (k === "s") setScreen("config");
        if (k === "h") setScreen("history");
        if (k === "d") setScreen("drafts");
    });

    return (
        <Box flexDirection="column" alignItems="center">
            <Text color="cyan" bold>{LOGO}</Text>

            <Box marginY={1}>
                <Text color="gray" italic>
                    Send bulk emails efficiently with AWS SES
                </Text>
            </Box>

            {/* Status */}
            <Box marginBottom={1} flexDirection="column" alignItems="center">
                {status === "loading" && <Spinner label="Connecting to API..." />}
                {status === "ok" && !configured && (
                    <Alert variant="warning" title="Setup Required">
                        Press S to configure your AWS credentials
                    </Alert>
                )}
                {status === "ok" && configured && (
                    <Text color="green">✓ API connected • AWS configured</Text>
                )}
                {status === "error" && (
                    <Alert variant="error" title="Connection Error">
                        {statusMsg || "Could not reach API"}
                    </Alert>
                )}
            </Box>

            {/* Quick stats */}
            {stats && (
                <Box gap={3} marginBottom={1}>
                    <Box>
                        <Text dimColor>Sent: </Text>
                        <Text color="green" bold>{stats["total_sent"] as number}</Text>
                    </Box>
                    <Box>
                        <Text dimColor>Campaigns: </Text>
                        <Text color="cyan" bold>{stats["total_campaigns"] as number}</Text>
                    </Box>
                    <Box>
                        <Text dimColor>Recipients: </Text>
                        <Text color="yellow" bold>{stats["unique_recipients"] as number}</Text>
                    </Box>
                </Box>
            )}

            {/* Menu */}
            <SectionBox title="Navigation" borderColor="blue">
                <Box flexDirection="column" paddingY={0}>
                    <MenuItem hotkey="C" label="Compose Email" desc="Create a new email" color="blue" />
                    <MenuItem hotkey="D" label="Drafts" desc="View saved drafts" color="yellow" />
                    <MenuItem hotkey="S" label="Settings" desc="Configure AWS & profiles" color="green" />
                    <MenuItem hotkey="H" label="History" desc="View sent campaigns" color="magenta" />
                </Box>
            </SectionBox>

            <Box marginTop={1}>
                <Text dimColor>
                    Press the highlighted key to navigate │ Ctrl+Q to quit
                </Text>
            </Box>
        </Box>
    );
}

function MenuItem({
    hotkey,
    label,
    desc,
    color,
}: {
    hotkey: string;
    label: string;
    desc: string;
    color: string;
}) {
    return (
        <Box gap={1}>
            <Text> [</Text>
            <Text bold color={color}>{hotkey}</Text>
            <Text>]</Text>
            <Text bold> {label}</Text>
            <Text dimColor> — {desc}</Text>
        </Box>
    );
}
