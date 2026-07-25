/**
 * Jobs screen — monitor scheduled / queued send jobs with live progress.
 *
 * Jobs run in the API's background worker, so this screen simply polls their
 * state; closing and reopening it (or the whole TUI) never loses a running send.
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import { Box, Text, useInput } from "ink";
import { Spinner, Alert, ProgressBar } from "@inkjs/ui";
import { listJobs, cancelJob, type Job } from "../api.js";
import { SectionBox } from "../components/SectionBox.js";
import { KeyHint } from "../components/KeyHint.js";
import type { Screen } from "../App.js";

interface Props {
    setScreen: (s: Screen) => void;
}

const STATUS_COLOR: Record<string, string> = {
    scheduled: "yellow",
    pending: "cyan",
    running: "blue",
    completed: "green",
    failed: "red",
    canceled: "gray",
};

const ACTIVE = new Set(["scheduled", "pending", "running"]);

function statusLabel(job: Job): string {
    if (job.status === "scheduled" && job.scheduled_at) {
        return `scheduled → ${job.scheduled_at.slice(0, 16)}`;
    }
    return job.status;
}

export function JobsScreen({ setScreen }: Props) {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedIdx, setSelectedIdx] = useState(0);
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const idxRef = useRef(0);
    idxRef.current = selectedIdx;

    const load = useCallback(async () => {
        try {
            const res = await listJobs(50);
            setJobs(res.jobs);
            setError("");
        } catch (err) {
            setError(String(err));
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        load();
        const timer = setInterval(load, 2000); // live refresh
        return () => clearInterval(timer);
    }, [load]);

    const handleCancel = useCallback(async (job: Job) => {
        if (!ACTIVE.has(job.status)) return;
        try {
            await cancelJob(job.id);
            setMessage(`Canceled "${job.name}"`);
            await load();
        } catch (err) {
            setMessage(`Cancel failed: ${err}`);
        }
    }, [load]);

    useInput((input, key) => {
        if (key.escape) {
            setScreen("home");
            return;
        }
        if (key.upArrow) setSelectedIdx((i) => Math.max(0, i - 1));
        if (key.downArrow) setSelectedIdx((i) => Math.min(jobs.length - 1, i + 1));
        if (input === "r") load();
        if (input === "c" && jobs[idxRef.current]) handleCancel(jobs[idxRef.current]);
    });

    if (loading) {
        return (
            <Box flexDirection="column" alignItems="center" paddingY={2}>
                <Spinner label="Loading jobs..." />
            </Box>
        );
    }

    const active = jobs.filter((j) => ACTIVE.has(j.status)).length;

    return (
        <Box flexDirection="column">
            <Text bold color="magenta">🗓  Send Queue</Text>

            <Box gap={3} marginY={1}>
                <Box><Text dimColor>Total: </Text><Text bold>{jobs.length}</Text></Box>
                <Box><Text dimColor>Active: </Text><Text color="cyan" bold>{active}</Text></Box>
            </Box>

            {message && <Box marginBottom={1}><Alert variant="info">{message}</Alert></Box>}

            <SectionBox title={`Jobs (${jobs.length})`} borderColor="blue">
                <Box flexDirection="column" paddingY={0}>
                    {jobs.length === 0 ? (
                        <Text dimColor>
                            No jobs yet. Schedule or queue a send from Compose (Ctrl+J).
                        </Text>
                    ) : (
                        jobs.slice(0, 12).map((job, i) => {
                            const selected = i === selectedIdx;
                            const pct = job.total > 0
                                ? Math.round(((job.sent + job.failed) / job.total) * 100)
                                : 0;
                            return (
                                <Box key={job.id} flexDirection="column" marginBottom={selected ? 1 : 0}>
                                    <Box>
                                        <Box width={3}>
                                            <Text bold color={selected ? "cyan" : undefined}>
                                                {selected ? "▸ " : "  "}
                                            </Text>
                                        </Box>
                                        <Box width={28}>
                                            <Text bold={selected} color={selected ? "cyan" : undefined}>
                                                {job.name.slice(0, 26) || "(untitled)"}
                                            </Text>
                                        </Box>
                                        <Box width={22}>
                                            <Text color={STATUS_COLOR[job.status] || "white"}>
                                                {statusLabel(job)}
                                            </Text>
                                        </Box>
                                        <Box width={16}>
                                            <Text dimColor>
                                                {job.sent}/{job.total}
                                                {job.failed > 0 ? ` (${job.failed}✗)` : ""}
                                            </Text>
                                        </Box>
                                    </Box>
                                    {selected && job.status === "running" && (
                                        <Box marginLeft={3} width={40}>
                                            <ProgressBar value={pct} />
                                        </Box>
                                    )}
                                    {selected && job.error && (
                                        <Box marginLeft={3}>
                                            <Text color="red">{job.error.slice(0, 60)}</Text>
                                        </Box>
                                    )}
                                </Box>
                            );
                        })
                    )}
                </Box>
            </SectionBox>

            <Box marginTop={1}>
                <KeyHint
                    hints={[
                        { key: "↑↓", label: "Navigate" },
                        { key: "C", label: "Cancel" },
                        { key: "R", label: "Refresh" },
                        { key: "Esc", label: "Back" },
                    ]}
                />
            </Box>

            {error && (
                <Box marginTop={1}><Alert variant="error">{error}</Alert></Box>
            )}
        </Box>
    );
}
