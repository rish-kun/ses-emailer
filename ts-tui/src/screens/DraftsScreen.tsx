/**
 * Drafts screen — polished draft list with management.
 * Pressing Enter shows a preview; from preview, Enter loads into compose.
 */

import React, { useState, useEffect, useCallback } from "react";
import { Box, Text, useInput, useStdout } from "ink";
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

    // Preview state
    const [previewDraft, setPreviewDraft] = useState<Record<string, unknown> | null>(null);
    const [previewLoading, setPreviewLoading] = useState(false);
    const [bodyScrollOffset, setBodyScrollOffset] = useState(0);

    const { stdout } = useStdout();
    // Reserve lines for header, metadata section, key hints, etc.
    const terminalHeight = stdout?.rows ?? 24;
    const bodyViewportHeight = Math.max(5, terminalHeight - 18);

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

    const handlePreview = useCallback(async () => {
        const draft = drafts[selectedIdx];
        if (!draft) return;
        setPreviewLoading(true);
        try {
            const full = await getDraft(draft.id);
            setPreviewDraft(full);
            setBodyScrollOffset(0);
        } catch (err) {
            setMessage(`Error loading draft: ${err}`);
            setMessageType("error");
        }
        setPreviewLoading(false);
    }, [drafts, selectedIdx]);

    const handleConfirmLoad = useCallback(() => {
        if (!previewDraft) return;
        loadDraft(previewDraft);
    }, [previewDraft, loadDraft]);

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
        // ─── Preview mode ───────────────────────────────────────
        if (previewDraft) {
            if (key.escape) {
                setPreviewDraft(null);
                setBodyScrollOffset(0);
                return;
            }
            if (key.return) {
                handleConfirmLoad();
                return;
            }
            // Scroll body
            const bodyLines = ((previewDraft["body"] as string) || "").split("\n");
            const maxOffset = Math.max(0, bodyLines.length - bodyViewportHeight);
            if (key.upArrow) setBodyScrollOffset((o) => Math.max(0, o - 1));
            if (key.downArrow) setBodyScrollOffset((o) => Math.min(maxOffset, o + 1));
            return;
        }

        // ─── List mode ─────────────────────────────────────────
        if (key.escape) setScreen("home");
        if (key.upArrow && selectedIdx > 0) setSelectedIdx((i) => i - 1);
        if (key.downArrow && selectedIdx < drafts.length - 1) setSelectedIdx((i) => i + 1);
        if (key.return) handlePreview();
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

    // ─── Preview view ───────────────────────────────────────────
    if (previewLoading) {
        return (
            <Box flexDirection="column" alignItems="center" paddingY={2}>
                <Spinner label="Loading draft preview..." />
            </Box>
        );
    }

    if (previewDraft) {
        const name = (previewDraft["name"] as string) || "Untitled";
        const subject = (previewDraft["subject"] as string) || "—";
        const sender = (previewDraft["sender"] as string) || "—";
        const recipients = (previewDraft["recipients"] as string[]) || [];
        const body = (previewDraft["body"] as string) || "";
        const emailType = (previewDraft["email_type"] as string) || "html";
        const attachments = (previewDraft["attachments"] as string[]) || [];

        const bodyLines = body.split("\n");
        const totalBodyLines = bodyLines.length;
        const visibleLines = bodyLines.slice(bodyScrollOffset, bodyScrollOffset + bodyViewportHeight);
        const canScrollUp = bodyScrollOffset > 0;
        const canScrollDown = bodyScrollOffset + bodyViewportHeight < totalBodyLines;

        return (
            <Box flexDirection="column">
                <Text bold color="magenta">📝 Draft Preview</Text>

                <SectionBox title={`"${name}"`} titleColor="cyan" borderColor="cyan">
                    <Box flexDirection="column" paddingY={0}>
                        <Box>
                            <Box width={16}><Text dimColor>Subject:</Text></Box>
                            <Text>{subject}</Text>
                        </Box>
                        <Box>
                            <Box width={16}><Text dimColor>From:</Text></Box>
                            <Text>{sender}</Text>
                        </Box>
                        <Box>
                            <Box width={16}><Text dimColor>To:</Text></Box>
                            <Text>
                                {recipients.length > 0 ? recipients.join(", ") : "—"}
                            </Text>
                        </Box>
                        <Box>
                            <Box width={16}><Text dimColor>Type:</Text></Box>
                            <Text>{emailType.toUpperCase()}</Text>
                        </Box>
                        {attachments.length > 0 && (
                            <Box>
                                <Box width={16}><Text dimColor>Attachments:</Text></Box>
                                <Text>{attachments.length} file{attachments.length !== 1 ? "s" : ""}</Text>
                            </Box>
                        )}
                    </Box>
                </SectionBox>

                <SectionBox
                    title={`Body${totalBodyLines > bodyViewportHeight ? ` (${bodyScrollOffset + 1}–${Math.min(bodyScrollOffset + bodyViewportHeight, totalBodyLines)} of ${totalBodyLines} lines)` : ""}`}
                    borderColor="gray"
                >
                    <Box flexDirection="column" height={bodyViewportHeight}>
                        {canScrollUp && (
                            <Text dimColor>  ▲ scroll up</Text>
                        )}
                        {visibleLines.length > 0 ? (
                            visibleLines.map((line, i) => (
                                <Text key={bodyScrollOffset + i}>{line || " "}</Text>
                            ))
                        ) : (
                            <Text dimColor>(empty body)</Text>
                        )}
                        {canScrollDown && (
                            <Text dimColor>  ▼ scroll down</Text>
                        )}
                    </Box>
                </SectionBox>

                <Box marginTop={1}>
                    <KeyHint
                        hints={[
                            { key: "↑↓", label: "Scroll Body" },
                            { key: "Enter", label: "Load into Compose" },
                            { key: "Esc", label: "Back to List" },
                        ]}
                    />
                </Box>
            </Box>
        );
    }

    // ─── List view ──────────────────────────────────────────────
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
                        { key: "Enter", label: "Preview" },
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
