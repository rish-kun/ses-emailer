/**
 * History screen — polished campaign list with stats and detail.
 */

import React, { useState, useEffect, useCallback } from "react";
import { Box, Text, useInput } from "ink";
import { Spinner, Alert } from "@inkjs/ui";
import {
    listCampaigns,
    getStats,
    getCampaignDetail,
    getRetryUrl,
    getAuthHeaders,
} from "../api.js";
import { SectionBox } from "../components/SectionBox.js";
import { KeyHint } from "../components/KeyHint.js";
import { FormField } from "../components/FormField.js";
import type { Screen } from "../App.js";

interface Props {
    setScreen: (s: Screen) => void;
}

interface Campaign {
    id: string;
    subject: string;
    sender: string;
    sent_count: number;
    failed_count: number;
    last_sent: string | null;
    email_ids: string[];
}

export function HistoryScreen({ setScreen }: Props) {
    const [loading, setLoading] = useState(true);
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [selectedIdx, setSelectedIdx] = useState(0);
    const [search, setSearch] = useState("");
    const [searchActive, setSearchActive] = useState(false);
    const [stats, setStats] = useState<Record<string, unknown> | null>(null);
    const [detail, setDetail] = useState<Record<string, unknown> | null>(null);
    const [showDetail, setShowDetail] = useState(false);
    const [error, setError] = useState("");
    const [retrying, setRetrying] = useState(false);
    const [retryStatus, setRetryStatus] = useState("");

    const loadData = useCallback(async (query = "") => {
        setLoading(true);
        try {
            const [camRes, statRes] = await Promise.all([
                listCampaigns(query),
                getStats(),
            ]);
            setCampaigns(camRes.campaigns || []);
            setStats(statRes);
            setSelectedIdx(0);
        } catch (err) {
            setError(String(err));
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const loadDetail = useCallback(async (id: string) => {
        try {
            const res = await getCampaignDetail(id);
            setDetail(res);
            setShowDetail(true);
        } catch (err) {
            setError(String(err));
        }
    }, []);

    const retryFailed = useCallback(async (id: string) => {
        setRetrying(true);
        setRetryStatus("Starting retry…");
        try {
            const response = await fetch(getRetryUrl(id), {
                method: "POST",
                headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
            });
            if (!response.ok || !response.body) {
                setRetryStatus(`Retry failed: HTTP ${response.status}`);
                setRetrying(false);
                return;
            }
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let eventType = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";
                for (const line of lines) {
                    if (line.startsWith("event: ")) {
                        eventType = line.slice(7).trim();
                    } else if (line.startsWith("data: ")) {
                        const data = JSON.parse(line.slice(6).trim() || "{}");
                        if (eventType === "start") {
                            setRetryStatus(
                                data.total_recipients > 0
                                    ? `Retrying ${data.total_recipients} recipient(s)…`
                                    : "Nothing to retry."
                            );
                        } else if (eventType === "complete") {
                            setRetryStatus(
                                `Retry done: ${data.total_sent} sent, ${data.total_failed} failed`
                            );
                        } else if (eventType === "error") {
                            setRetryStatus(`Retry error: ${data.error}`);
                        }
                        eventType = "";
                    }
                }
            }
        } catch (err) {
            setRetryStatus(`Retry error: ${err}`);
        }
        setRetrying(false);
        // Refresh detail + list so retried failures drop off.
        await loadDetail(id);
        await loadData(search);
    }, [loadDetail, loadData, search]);

    useInput((input, key) => {
        if (key.escape) {
            if (showDetail) {
                setShowDetail(false);
                setDetail(null);
            } else if (searchActive) {
                setSearchActive(false);
            } else {
                setScreen("home");
            }
            return;
        }

        if (searchActive) return; // TextInput handles keys

        if (showDetail) {
            if ((input === "y" || input === "r") && detail && !retrying) {
                const camp = detail["campaign"] as Campaign;
                const failed =
                    (detail["failed_records"] as Array<Record<string, unknown>>) || [];
                const unretried = failed.filter((f) => !f["retried"]).length;
                if (camp && unretried > 0) retryFailed(camp.id);
            }
            return;
        }

        if (!showDetail) {
            if (key.upArrow && selectedIdx > 0) setSelectedIdx((i) => i - 1);
            if (key.downArrow && selectedIdx < campaigns.length - 1)
                setSelectedIdx((i) => i + 1);
            if (key.return && campaigns[selectedIdx]) {
                setRetryStatus("");
                loadDetail(campaigns[selectedIdx].id);
            }
            if (input === "/" && !searchActive) setSearchActive(true);
            if (input === "r") loadData(search);
        }
    });

    if (loading) {
        return (
            <Box flexDirection="column" alignItems="center" paddingY={2}>
                <Spinner label="Loading history..." />
            </Box>
        );
    }

    // Detail view
    if (showDetail && detail) {
        const camp = detail["campaign"] as Campaign;
        const body = (detail["body"] as string) || "";
        const failed = (detail["failed_records"] as Array<Record<string, unknown>>) || [];
        const sent = (detail["sent_records"] as Array<Record<string, unknown>>) || [];
        const unretried = failed.filter((f) => !f["retried"]).length;

        return (
            <Box flexDirection="column">
                <Text bold color="magenta">📋 Campaign Detail</Text>

                <SectionBox title={camp.subject} titleColor="cyan" borderColor="cyan">
                    <Box flexDirection="column" paddingY={0}>
                        <Box gap={3}>
                            <Box><Text dimColor>Sender: </Text><Text>{camp.sender}</Text></Box>
                            <Box><Text dimColor>Last: </Text><Text>{camp.last_sent?.slice(0, 16) || "—"}</Text></Box>
                        </Box>
                        <Box gap={3} marginTop={0}>
                            <Text color="green" bold>✓ {sent.length} sent</Text>
                            <Text color={failed.length > 0 ? "red" : "gray"} bold>
                                ✗ {failed.length} failed
                            </Text>
                        </Box>
                    </Box>
                </SectionBox>

                <SectionBox title="Body Preview" borderColor="gray">
                    <Box paddingY={0}>
                        <Text>{body.slice(0, 500)}{body.length > 500 ? "..." : ""}</Text>
                    </Box>
                </SectionBox>

                {failed.length > 0 && (
                    <SectionBox
                        title={`Failed Recipients (${failed.length}${unretried > 0 ? `, ${unretried} not retried` : ", all retried"})`}
                        borderColor="red"
                    >
                        <Box flexDirection="column" paddingY={0}>
                            {failed.slice(0, 8).map((f, i) => (
                                <Box key={i}>
                                    <Text color={f["retried"] ? "yellow" : "red"}>
                                        {f["retried"] ? "↻ " : "✗ "}
                                    </Text>
                                    <Text>{f["recipient"] as string}</Text>
                                    <Text dimColor> — {f["error"] as string}</Text>
                                </Box>
                            ))}
                            {failed.length > 8 && (
                                <Text dimColor>...and {failed.length - 8} more</Text>
                            )}
                        </Box>
                    </SectionBox>
                )}

                {(retrying || retryStatus) && (
                    <Box marginTop={1}>
                        {retrying ? (
                            <Spinner label={retryStatus || "Retrying…"} />
                        ) : (
                            <Text color="cyan">{retryStatus}</Text>
                        )}
                    </Box>
                )}

                <Box marginTop={1}>
                    <KeyHint
                        hints={
                            unretried > 0 && !retrying
                                ? [
                                      { key: "Y", label: `Retry ${unretried} failed` },
                                      { key: "Esc", label: "Back to list" },
                                  ]
                                : [{ key: "Esc", label: "Back to list" }]
                        }
                    />
                </Box>
            </Box>
        );
    }

    return (
        <Box flexDirection="column">
            <Text bold color="magenta">📜 Email History</Text>

            {/* Stats */}
            {stats && (
                <Box gap={3} marginY={1}>
                    <Box><Text dimColor>Sent: </Text><Text color="green" bold>{stats["total_sent"] as number}</Text></Box>
                    <Box><Text dimColor>Failed: </Text><Text color="red" bold>{stats["total_failed"] as number}</Text></Box>
                    <Box><Text dimColor>Recipients: </Text><Text color="cyan" bold>{stats["unique_recipients"] as number}</Text></Box>
                    <Box><Text dimColor>Success: </Text><Text color="yellow" bold>{stats["success_rate"] as number}%</Text></Box>
                </Box>
            )}

            {/* Search */}
            <Box marginBottom={1}>
                <FormField
                    label="Search"
                    value={search}
                    placeholder="Filter by subject or sender..."
                    isActive={searchActive}
                    onChange={setSearch}
                    onSubmit={() => {
                        setSearchActive(false);
                        loadData(search);
                    }}
                    labelWidth={10}
                />
            </Box>

            {/* Campaign table */}
            <SectionBox title={`Campaigns (${campaigns.length})`} borderColor="blue">
                <Box flexDirection="column" paddingY={0}>
                    {/* Header */}
                    <Box marginBottom={0}>
                        <Box width={3}><Text dimColor> </Text></Box>
                        <Box width={30}><Text bold dimColor>Subject</Text></Box>
                        <Box width={10}><Text bold dimColor>Sent</Text></Box>
                        <Box width={10}><Text bold dimColor>Failed</Text></Box>
                        <Box width={18}><Text bold dimColor>Last Sent</Text></Box>
                    </Box>

                    {campaigns.length === 0 ? (
                        <Text dimColor>No campaigns found</Text>
                    ) : (
                        campaigns.slice(0, 15).map((c, i) => (
                            <Box key={c.id}>
                                <Box width={3}>
                                    <Text bold color={i === selectedIdx ? "cyan" : undefined}>
                                        {i === selectedIdx ? "▸ " : "  "}
                                    </Text>
                                </Box>
                                <Box width={30}>
                                    <Text color={i === selectedIdx ? "cyan" : undefined} bold={i === selectedIdx}>
                                        {c.subject.slice(0, 28)}{c.subject.length > 28 ? "…" : ""}
                                    </Text>
                                </Box>
                                <Box width={10}>
                                    <Text color="green">{c.sent_count}</Text>
                                </Box>
                                <Box width={10}>
                                    <Text color={c.failed_count > 0 ? "red" : "gray"}>{c.failed_count}</Text>
                                </Box>
                                <Box width={18}>
                                    <Text dimColor>{c.last_sent ? c.last_sent.slice(0, 16) : "—"}</Text>
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
                        { key: "Enter", label: "Detail" },
                        { key: "/", label: "Search" },
                        { key: "R", label: "Refresh" },
                        { key: "Esc", label: "Back" },
                    ]}
                />
            </Box>

            {error && (
                <Box marginTop={1}>
                    <Alert variant="error">{error}</Alert>
                </Box>
            )}
        </Box>
    );
}
