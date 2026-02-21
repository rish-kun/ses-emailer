/**
 * Drafts screen — polished draft list with management.
 */

import React, { useState, useEffect, useCallback } from "react";
import { Box, Text, useInput } from "ink";
import { Spinner, Alert } from "@inkjs/ui";
import { listDrafts, getDraft, deleteDraft } from "../api.js";
import { SectionBox } from "../components/SectionBox.js";
import { KeyHint } from "../components/KeyHint.js";
import type { Screen } from "../App.js";

interface Props {
    setScreen: (s: Screen) => void;
    loadDraft: (draft: Record<string, unknown>) => void;
}

interface Draft {
    id: number;
    name: string;
    subject: string;
    created_at: string;
    updated_at: string;
}

export function DraftsScreen({ setScreen, loadDraft }: Props) {
    const [loading, setLoading] = useState(true);
    const [drafts, setDrafts] = useState<Draft[]>([]);
    const [selectedIdx, setSelectedIdx] = useState(0);
    const [message, setMessage] = useState("");
    const [messageType, setMessageType] = useState<"success" | "error">("success");

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const res = await listDrafts();
            setDrafts(res.drafts || []);
        } catch (err) {
            setMessage(String(err));
            setMessageType("error");
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    const handleLoad = useCallback(async () => {
        const draft = drafts[selectedIdx];
        if (!draft) return;
        try {
            const full = await getDraft(draft.id);
            loadDraft(full);
        } catch (err) {
            setMessage(`Error loading draft: ${err}`);
            setMessageType("error");
        }
    }, [drafts, selectedIdx, loadDraft]);

    const handleDelete = useCallback(async () => {
        const draft = drafts[selectedIdx];
        if (!draft) return;
        try {
            await deleteDraft(draft.id);
            setMessage(`Deleted "${draft.name}"`);
            setMessageType("success");
            load();
        } catch (err) {
            setMessage(`Error: ${err}`);
            setMessageType("error");
        }
    }, [drafts, selectedIdx, load]);

    useInput((input, key) => {
        if (key.escape) setScreen("home");
        if (key.upArrow && selectedIdx > 0) setSelectedIdx((i) => i - 1);
        if (key.downArrow && selectedIdx < drafts.length - 1) setSelectedIdx((i) => i + 1);
        if (key.return) handleLoad();
        if (input === "d" || key.delete) handleDelete();
        if (input === "r") load();
    });

    if (loading) {
        return (
            <Box flexDirection="column" alignItems="center" paddingY={2}>
                <Spinner label="Loading drafts..." />
            </Box>
        );
    }

    return (
        <Box flexDirection="column">
            <Text bold color="magenta">📝 Drafts</Text>

            <SectionBox title={`Saved Drafts (${drafts.length})`} borderColor="yellow">
                <Box flexDirection="column" paddingY={0}>
                    {/* Header */}
                    <Box marginBottom={0}>
                        <Box width={3}><Text dimColor> </Text></Box>
                        <Box width={25}><Text bold dimColor>Name</Text></Box>
                        <Box width={25}><Text bold dimColor>Subject</Text></Box>
                        <Box width={18}><Text bold dimColor>Updated</Text></Box>
                    </Box>

                    {drafts.length === 0 ? (
                        <Box paddingY={1}>
                            <Text dimColor>No drafts saved yet. Compose an email and press Ctrl+S to save a draft.</Text>
                        </Box>
                    ) : (
                        drafts.map((d, i) => (
                            <Box key={d.id}>
                                <Box width={3}>
                                    <Text bold color={i === selectedIdx ? "cyan" : undefined}>
                                        {i === selectedIdx ? "▸ " : "  "}
                                    </Text>
                                </Box>
                                <Box width={25}>
                                    <Text
                                        color={i === selectedIdx ? "cyan" : undefined}
                                        bold={i === selectedIdx}
                                    >
                                        {d.name.slice(0, 23)}{d.name.length > 23 ? "…" : ""}
                                    </Text>
                                </Box>
                                <Box width={25}>
                                    <Text dimColor>
                                        {d.subject.slice(0, 23)}{d.subject.length > 23 ? "…" : ""}
                                    </Text>
                                </Box>
                                <Box width={18}>
                                    <Text dimColor>
                                        {d.updated_at ? d.updated_at.slice(0, 16) : "—"}
                                    </Text>
                                </Box>
                            </Box>
                        ))
                    )}
                </Box>
            </SectionBox>

            <Box marginTop={1}>
                <KeyHint
                    hints={[
                        { key: "↑↓", label: "Navigate" },
                        { key: "Enter", label: "Load" },
                        { key: "D", label: "Delete" },
                        { key: "R", label: "Refresh" },
                        { key: "Esc", label: "Back" },
                    ]}
                />
            </Box>

            {message && (
                <Box marginTop={1}>
                    <Alert variant={messageType}>{message}</Alert>
                </Box>
            )}
        </Box>
    );
}
