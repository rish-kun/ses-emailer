/**
 * Send screen — batch sending with SSE progress and polished UI.
 */

import React, { useState, useCallback } from "react";
import { Box, Text, useInput } from "ink";
import { ProgressBar, Spinner, Alert } from "@inkjs/ui";
import { getSendUrl, getAuthHeaders } from "../api.js";
import { SectionBox } from "../components/SectionBox.js";
import { KeyHint } from "../components/KeyHint.js";
import type { Screen, ComposeData } from "../App.js";

interface Props {
    setScreen: (s: Screen) => void;
    composeData: ComposeData | null;
}

type SendState = "ready" | "sending" | "complete" | "error";

export function SendScreen({ setScreen, composeData }: Props) {
    const [state, setState] = useState<SendState>("ready");
    const [totalRecipients, setTotalRecipients] = useState(0);
    const [totalBatches, setTotalBatches] = useState(0);
    const [currentBatch, setCurrentBatch] = useState(0);
    const [totalSent, setTotalSent] = useState(0);
    const [totalFailed, setTotalFailed] = useState(0);
    const [batchProgress, setBatchProgress] = useState(0);
    const [logs, setLogs] = useState<string[]>([]);
    const [waitingSeconds, setWaitingSeconds] = useState(0);
    const [errorMsg, setErrorMsg] = useState("");

    const addLog = useCallback((msg: string) => {
        const time = new Date().toLocaleTimeString();
        setLogs((prev) => [...prev.slice(-50), `[${time}] ${msg}`]);
    }, []);

    const startSending = useCallback(async () => {
        if (!composeData) return;
        setState("sending");
        addLog("Starting email send...");

        try {
            const url = getSendUrl();
            const headers = getAuthHeaders();

            const response = await fetch(url, {
                method: "POST",
                headers: { ...headers, "Content-Type": "application/json" },
                body: JSON.stringify({
                    recipients: composeData.recipients,
                    subject: composeData.subject,
                    body: composeData.body,
                    email_type: composeData.emailType,
                    attachments: composeData.attachments,
                }),
            });

            if (!response.ok || !response.body) {
                setErrorMsg(`HTTP ${response.status}`);
                setState("error");
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                let eventType = "";
                let eventData = "";

                for (const line of lines) {
                    if (line.startsWith("event: ")) {
                        eventType = line.slice(7).trim();
                    } else if (line.startsWith("data: ")) {
                        eventData = line.slice(6).trim();
                        if (eventType && eventData) {
                            handleSSE(eventType, eventData);
                            eventType = "";
                            eventData = "";
                        }
                    }
                }
            }

            setState("complete");
            addLog("All batches processed.");
        } catch (err) {
            setErrorMsg(String(err));
            setState("error");
            addLog(`Error: ${err}`);
        }
    }, [composeData, addLog]);

    const handleSSE = useCallback(
        (event: string, dataStr: string) => {
            try {
                const data = JSON.parse(dataStr);
                switch (event) {
                    case "start":
                        setTotalRecipients(data.total_recipients);
                        setTotalBatches(data.total_batches);
                        addLog(`Sending to ${data.total_recipients} recipients in ${data.total_batches} batches`);
                        break;
                    case "batch_start":
                        setCurrentBatch(data.batch);
                        addLog(`Batch ${data.batch}/${data.total_batches} (${data.batch_size} emails)`);
                        break;
                    case "batch_complete":
                        setTotalSent(data.total_sent);
                        setTotalFailed(data.total_failed);
                        setBatchProgress(Math.round((data.batch / (totalBatches || 1)) * 100));
                        addLog(`✓ Batch ${data.batch}: sent ${data.sent} (ID: ${data.message_id})`);
                        break;
                    case "batch_error":
                        setTotalSent(data.total_sent);
                        setTotalFailed(data.total_failed);
                        addLog(`✗ Batch ${data.batch}: FAILED ${data.failed} — ${data.error}`);
                        break;
                    case "waiting":
                        setWaitingSeconds(data.seconds_remaining);
                        break;
                    case "complete":
                        setTotalSent(data.total_sent);
                        setTotalFailed(data.total_failed);
                        setBatchProgress(100);
                        setState("complete");
                        addLog(`✓ Complete: ${data.total_sent} sent, ${data.total_failed} failed`);
                        break;
                    case "error":
                        setErrorMsg(data.error);
                        setState("error");
                        addLog(`✗ Error: ${data.error}`);
                        break;
                }
            } catch { }
        },
        [addLog, totalBatches]
    );

    useInput((input, key) => {
        if (key.escape) setScreen("home");
        if (input === "s" && state === "ready") startSending();
    });

    if (!composeData) {
        return (
            <Box flexDirection="column" paddingY={2}>
                <Alert variant="error" title="No Data">
                    No compose data — go back and compose an email first.
                </Alert>
                <Box marginTop={1}>
                    <KeyHint hints={[{ key: "Esc", label: "Go back" }]} />
                </Box>
            </Box>
        );
    }

    return (
        <Box flexDirection="column">
            <Text bold color="magenta">📨 Send Email</Text>

            {/* Summary */}
            <SectionBox title="Email Summary" titleColor="magenta" borderColor="magenta">
                <Box paddingY={0} gap={3}>
                    <Box>
                        <Text dimColor>Subject: </Text>
                        <Text bold>{composeData.subject}</Text>
                    </Box>
                    <Box>
                        <Text dimColor>To: </Text>
                        <Text bold color="cyan">{composeData.recipients.length} recipients</Text>
                    </Box>
                    {composeData.attachments.length > 0 && (
                        <Box>
                            <Text dimColor>📎 </Text>
                            <Text>{composeData.attachments.length} files</Text>
                        </Box>
                    )}
                </Box>
            </SectionBox>

            {/* Progress */}
            {state !== "ready" && (
                <SectionBox title="Progress" borderColor="blue">
                    <Box flexDirection="column" paddingY={1}>
                        <Box gap={2} marginBottom={1}>
                            <Text dimColor>Batch</Text>
                            <Text bold>{currentBatch}/{totalBatches}</Text>
                        </Box>
                        <ProgressBar value={batchProgress} />
                        <Box gap={4} marginTop={1}>
                            <Text color="green">✓ Sent: {totalSent}</Text>
                            <Text color="red">✗ Failed: {totalFailed}</Text>
                            <Text dimColor>
                                Total: {totalRecipients}
                            </Text>
                            {waitingSeconds > 0 && (
                                <Text color="yellow">⏱ {waitingSeconds}s</Text>
                            )}
                        </Box>
                    </Box>
                </SectionBox>
            )}

            {/* Status */}
            <Box marginY={1}>
                {state === "ready" && (
                    <Alert variant="info" title="Ready">
                        Press S to start sending to {composeData.recipients.length} recipients
                    </Alert>
                )}
                {state === "sending" && <Spinner label="Sending emails..." />}
                {state === "complete" && (
                    <Alert variant="success" title="Complete">
                        Sent {totalSent} emails, {totalFailed} failed
                    </Alert>
                )}
                {state === "error" && (
                    <Alert variant="error" title="Error">
                        {errorMsg}
                    </Alert>
                )}
            </Box>

            {/* Activity log */}
            <SectionBox title="Activity Log" borderColor="gray">
                <Box flexDirection="column" paddingY={0} minHeight={4}>
                    {logs.length === 0 ? (
                        <Text dimColor>Waiting to start...</Text>
                    ) : (
                        logs.slice(-10).map((log, i) => (
                            <Text key={i} dimColor>{log}</Text>
                        ))
                    )}
                </Box>
            </SectionBox>

            <Box marginTop={1}>
                <KeyHint
                    hints={
                        state === "ready"
                            ? [{ key: "S", label: "Start" }, { key: "Esc", label: "Back" }]
                            : [{ key: "Esc", label: "Back to Home" }]
                    }
                />
            </Box>
        </Box>
    );
}
