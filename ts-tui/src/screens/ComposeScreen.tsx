/**
 * Compose screen — Tabbed composition with FilePicker to reduce clutter.
 */

import React, { useState, useCallback } from "react";
import * as os from "os";
import * as fs from "fs";
import * as path from "path";
import { exec } from "child_process";
import { Box, Text, useInput } from "ink";
import { Alert, Spinner, Select } from "@inkjs/ui";
// @ts-ignore - ink-tab has no type declarations
import { Tabs, Tab } from "ink-tab";
import { uploadExcel, createDraft } from "../api.js";
import { FormField } from "../components/FormField.js";
import { SectionBox } from "../components/SectionBox.js";
import { KeyHint } from "../components/KeyHint.js";
import { FilePicker } from "../components/FilePicker.js";
import type { Screen, ComposeData } from "../App.js";

interface Props {
    setScreen: (s: Screen) => void;
    goToSend: (data: ComposeData) => void;
    initialData: ComposeData | null;
}

type TabView = "recipients" | "content" | "attachments" | "preview";
type OverlayView = "filepicker_excel" | "filepicker_attach";

const TAB_ORDER: TabView[] = ["recipients", "content", "attachments", "preview"];

export function ComposeScreen({ setScreen, goToSend, initialData }: Props) {
    // Navigation
    const [activeTab, setActiveTab] = useState<TabView>("recipients");
    const [overlay, setOverlay] = useState<OverlayView | null>(null);

    // Forms state
    const [activeField, setActiveField] = useState<string>("recipient_input");

    // Recipients
    const [recipients, setRecipients] = useState<string[]>(initialData?.recipients || []);
    const [recipientInput, setRecipientInput] = useState("");
    const [excelPath, setExcelPath] = useState("");
    const [excelColumn, setExcelColumn] = useState("0");
    const [loadingExcel, setLoadingExcel] = useState(false);

    // Content
    const [subject, setSubject] = useState(initialData?.subject || "");
    const [body, setBody] = useState(initialData?.body || "");
    const [emailType, setEmailType] = useState<"html" | "text">(initialData?.emailType || "html");

    // Attachments
    const [attachments, setAttachments] = useState<string[]>(initialData?.attachments || []);

    // UI
    const [message, setMessage] = useState("");
    const [messageType, setMessageType] = useState<"success" | "error">("success");
    const [savingDraft, setSavingDraft] = useState(false);

    // Actions
    const addRecipient = useCallback(
        (email: string) => {
            const cleaned = email
                .split(/[,;\n]/)
                .map((s) => s.trim().toLowerCase())
                .filter((s) => s && s.includes("@") && !recipients.includes(s));
            if (cleaned.length > 0) {
                setRecipients((prev) => [...prev, ...cleaned]);
                setRecipientInput("");
                setMessage(`Added ${cleaned.length} recipient(s)`);
                setMessageType("success");
            }
        },
        [recipients]
    );

    const handleLoadExcel = useCallback(async (path: string, col: string) => {
        if (!path.trim()) return;
        setLoadingExcel(true);
        try {
            const result = await uploadExcel(path.trim(), parseInt(col) || 0);
            const newEmails = (result.recipients as string[]).filter(
                (e: string) => !recipients.includes(e)
            );
            setRecipients((prev) => [...prev, ...newEmails]);
            setMessage(`Loaded ${result.count} emails (${newEmails.length} new)`);
            setMessageType("success");
        } catch (err) {
            setMessage(`Excel error: ${err}`);
            setMessageType("error");
        }
        setLoadingExcel(false);
    }, [recipients]);

    const handleSaveDraft = useCallback(async () => {
        setSavingDraft(true);
        try {
            await createDraft({
                name: subject || "Untitled Draft",
                subject,
                body,
                recipients,
                attachments,
                email_type: emailType,
            });
            setMessage("Draft saved!");
            setMessageType("success");
        } catch (err) {
            setMessage(`Save error: ${err}`);
            setMessageType("error");
        }
        setSavingDraft(false);
    }, [subject, body, recipients, attachments, emailType]);

    const handleBrowserPreview = useCallback(() => {
        if (!body.trim()) {
            setMessage("No HTML body to preview");
            setMessageType("error");
            return;
        }
        const tmpFile = path.join(os.tmpdir(), `ses-emailer-preview-${Date.now()}.html`);
        const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Email Preview: ${subject || "(no subject)"}</title></head><body>${body}</body></html>`;
        try {
            fs.writeFileSync(tmpFile, html, "utf-8");
            const opener = process.platform === "win32" ? "start" : process.platform === "darwin" ? "open" : "xdg-open";
            exec(`${opener} "${tmpFile}"`);
            setMessage(`Opened preview in browser`);
            setMessageType("success");
        } catch (err) {
            setMessage(`Preview error: ${err}`);
            setMessageType("error");
        }
    }, [body, subject]);

    const handleSend = useCallback(() => {
        if (recipients.length === 0) {
            setMessage("Add at least one recipient");
            setMessageType("error");
            return;
        }
        if (!subject.trim()) {
            setMessage("Enter a subject line");
            setMessageType("error");
            return;
        }
        if (!body.trim()) {
            setMessage("Enter the email body");
            setMessageType("error");
            return;
        }
        goToSend({ recipients, subject, body, emailType, attachments });
    }, [recipients, subject, body, emailType, attachments, goToSend]);

    // Handle tab change from ink-tab
    const handleTabChange = useCallback((name: string) => {
        setActiveTab(name as TabView);
        setMessage("");
        if (name === "recipients") setActiveField("recipient_input");
        if (name === "content") setActiveField("subject");
    }, []);

    // HOOKS MUST BE AT TOP LEVEL
    useInput((input, key) => {
        // Overlay escape
        if (key.escape) {
            if (overlay === "filepicker_excel") {
                setOverlay(null);
                return;
            }
            if (overlay === "filepicker_attach") {
                setOverlay(null);
                return;
            }
            // Esc goes back to home
            setScreen("home");
            return;
        }

        // Skip if overlay is active
        if (overlay) return;

        // Field cycling logic within a tab
        if (key.tab) {
            let fields: string[] = [];
            if (activeTab === "recipients") fields = ["recipient_input", "excel_column"];
            if (activeTab === "content") fields = ["subject", "body_type", "body"];

            if (fields.length > 0) {
                const idx = fields.indexOf(activeField);
                if (key.shift) {
                    const prev = idx > 0 ? idx - 1 : fields.length - 1;
                    setActiveField(fields[prev]);
                } else {
                    const next = idx < fields.length - 1 ? idx + 1 : 0;
                    setActiveField(fields[next]);
                }
            }
        }

        // Body type toggle when body_type pseudo-field is focused
        if (activeField === "body_type" && (key.leftArrow || key.rightArrow)) {
            setEmailType((prev) => (prev === "html" ? "text" : "html"));
        }

        // Global composition shortcuts
        if (key.ctrl && input === "s") handleSaveDraft();
        if (key.ctrl && input === "e") handleSend();
    });

    // ── Header ──
    const header = (
        <Box marginBottom={1} justifyContent="space-between">
            <Text bold color="magenta">✉ Compose Email</Text>
            <Box gap={2}>
                <Text dimColor>To: </Text>
                <Text color="cyan">{recipients.length}</Text>
                <Text dimColor> Attach: </Text>
                <Text color="yellow">{attachments.length}</Text>
            </Box>
        </Box>
    );

    // ── FilePicker overlays ──
    if (overlay === "filepicker_excel") {
        return (
            <Box flexDirection="column">
                {header}
                <FilePicker
                    title="Select Excel File"
                    onSelect={(path) => {
                        setExcelPath(path);
                        setOverlay(null);
                        handleLoadExcel(path, excelColumn);
                    }}
                    onCancel={() => setOverlay(null)}
                />
            </Box>
        );
    }

    if (overlay === "filepicker_attach") {
        return (
            <Box flexDirection="column">
                {header}
                <FilePicker
                    title="Select Attachment"
                    onSelect={(path) => {
                        if (!attachments.includes(path)) {
                            setAttachments([...attachments, path]);
                            setMessage(`Added ${path}`);
                            setMessageType("success");
                        }
                        setOverlay(null);
                    }}
                    onCancel={() => setOverlay(null)}
                />
            </Box>
        );
    }

    // ── Tab content renderers ──
    const renderTabContent = () => {
        if (activeTab === "recipients") {
            return (
                <SectionBox title={`Recipients (${recipients.length})`} borderColor="green">
                    <Box flexDirection="column" gap={0} paddingY={1}>
                        <FormField
                            label="Add Email(s)"
                            value={recipientInput}
                            placeholder="user@example.com (comma-separated)"
                            isActive={activeField === "recipient_input"}
                            onChange={setRecipientInput}
                            onSubmit={() => addRecipient(recipientInput)}
                        />

                        <Box marginTop={1} marginBottom={1}>
                            <Text bold dimColor>── Excel Import ──</Text>
                        </Box>

                        <FormField
                            label="Column Index"
                            value={excelColumn}
                            placeholder="0"
                            isActive={activeField === "excel_column"}
                            onChange={setExcelColumn}
                            onSubmit={() => null}
                        />

                        <Box marginTop={1}>
                            <Text dimColor>Currently selected: {excelPath || "None"}</Text>
                        </Box>

                        <Box marginTop={1} width={30}>
                            <Select
                                options={[
                                    { label: "Browse for Excel File...", value: "browse" },
                                    { label: "Load currently selected", value: "load" },
                                    { label: "Clear all recipients", value: "clear" },
                                ]}
                                onChange={(val) => {
                                    if (val === "browse") setOverlay("filepicker_excel");
                                    if (val === "load") handleLoadExcel(excelPath, excelColumn);
                                    if (val === "clear") { setRecipients([]); setMessage("Recipients cleared"); }
                                }}
                            />
                        </Box>

                        {loadingExcel && <Box marginTop={1}><Spinner label="Loading Excel file..." /></Box>}
                    </Box>
                </SectionBox>
            );
        }

        if (activeTab === "content") {
            return (
                <SectionBox title="Email Content" borderColor="blue">
                    <Box flexDirection="column" gap={0} paddingY={1}>
                        <FormField
                            label="Subject"
                            value={subject}
                            placeholder="Enter your email subject..."
                            isActive={activeField === "subject"}
                            onChange={setSubject}
                            onSubmit={() => null}
                        />

                        <Box marginTop={1} flexDirection="column">
                            <Box marginBottom={0}>
                                <Text bold color={activeField === "body_type" ? "cyan" : "white"}>
                                    Body Type:{" "}
                                </Text>
                                <Text color={activeField === "body_type" ? "cyan" : "white"}>
                                    (Tab to focus, ←/→ to change)
                                </Text>
                            </Box>
                            <Box gap={2} marginTop={0}>
                                <Text
                                    color={emailType === "html" ? "green" : "gray"}
                                    bold={emailType === "html"}
                                >
                                    {emailType === "html" ? "● HTML" : "○ HTML"}
                                </Text>
                                <Text
                                    color={emailType === "text" ? "green" : "gray"}
                                    bold={emailType === "text"}
                                >
                                    {emailType === "text" ? "● Plain Text" : "○ Plain Text"}
                                </Text>
                            </Box>
                        </Box>

                        <Box marginTop={1}>
                            <FormField
                                label="Body"
                                value={body}
                                placeholder={emailType === "html" ? "<h1>Hello</h1><p>Your content...</p>" : "Enter your email body here..."}
                                isActive={activeField === "body"}
                                onChange={setBody}
                                onSubmit={() => { }}
                            />
                        </Box>

                        {body && (
                            <Box marginTop={1}>
                                <Text dimColor>{body.length} characters · {emailType.toUpperCase()}</Text>
                            </Box>
                        )}
                    </Box>
                </SectionBox>
            );
        }

        if (activeTab === "attachments") {
            return (
                <SectionBox title={`Attachments (${attachments.length})`} borderColor="yellow">
                    <Box flexDirection="column" gap={0} paddingY={1}>
                        <Box width={30} marginBottom={1}>
                            <Select
                                options={[
                                    { label: "Add Attachment...", value: "add" },
                                    ...attachments.map((a, i) => ({ label: `❌ Remove ${a.split('/').pop()}`, value: `RM_${i}` })),
                                ]}
                                onChange={(val) => {
                                    if (val === "add") setOverlay("filepicker_attach");
                                    if (val.startsWith("RM_")) {
                                        const idx = parseInt(val.replace("RM_", ""));
                                        setAttachments(attachments.filter((_, i) => i !== idx));
                                    }
                                }}
                            />
                        </Box>

                        {attachments.length > 0 && (
                            <Box flexDirection="column">
                                <Text bold dimColor>Current attachments:</Text>
                                {attachments.map((a, i) => (
                                    <Text key={i} color="yellow">  📎 {a}</Text>
                                ))}
                            </Box>
                        )}
                    </Box>
                </SectionBox>
            );
        }

        if (activeTab === "preview") {
            return (
                <SectionBox title="Email Preview" borderColor="magenta">
                    <Box flexDirection="column" paddingY={1}>
                        <Box><Box width={16}><Text dimColor>To:</Text></Box><Text bold>{recipients.length} recipients</Text></Box>
                        <Box><Box width={16}><Text dimColor>Subject:</Text></Box><Text bold>{subject || "—"}</Text></Box>
                        <Box><Box width={16}><Text dimColor>Format:</Text></Box><Text>{emailType.toUpperCase()}</Text></Box>
                        <Box><Box width={16}><Text dimColor>Attachments:</Text></Box><Text>{attachments.length > 0 ? attachments.length : "None"}</Text></Box>

                        <Box marginTop={1} flexDirection="column" borderStyle="single" borderColor="gray" paddingX={1} paddingY={1}>
                            <Text dimColor bold>Body Preview:</Text>
                            <Text>{body || "(empty)"}</Text>
                        </Box>

                        <Box marginTop={1} flexDirection="column">
                            <Box><Text color={recipients.length > 0 ? "green" : "red"}>{recipients.length > 0 ? " ✓" : " ✗"} Recipients added</Text></Box>
                            <Box><Text color={subject.trim() ? "green" : "red"}>{subject.trim() ? " ✓" : " ✗"} Subject line set</Text></Box>
                            <Box><Text color={body.trim() ? "green" : "red"}>{body.trim() ? " ✓" : " ✗"} Body content written</Text></Box>
                        </Box>

                        {emailType === "html" && (
                            <Box marginTop={1}>
                                <Select
                                    options={[
                                        { label: "🌐 Preview in Browser", value: "browser_preview" },
                                    ]}
                                    onChange={(val) => {
                                        if (val === "browser_preview") handleBrowserPreview();
                                    }}
                                />
                            </Box>
                        )}
                    </Box>
                </SectionBox>
            );
        }

        return null;
    };

    return (
        <Box flexDirection="column">
            {header}

            {message && <Box marginBottom={1}><Alert variant={messageType}>{message}</Alert></Box>}

            {/* ── Tabular Navigation ── */}
            <Box marginBottom={1}>
                <Tabs
                    onChange={handleTabChange}
                    defaultValue={activeTab}
                    keyMap={{
                        useTab: false,
                        useNumbers: true,
                        previous: [],
                        next: [],
                    }}
                >
                    <Tab name="recipients">{`Recipients (${recipients.length})`}</Tab>
                    <Tab name="content">{`Content${subject ? " ✓" : ""} [${emailType.toUpperCase()}]`}</Tab>
                    <Tab name="attachments">{`Attachments (${attachments.length})`}</Tab>
                    <Tab name="preview">Preview</Tab>
                </Tabs>
            </Box>

            {/* ── Active Tab Content ── */}
            {renderTabContent()}

            {/* ── Footer Hints ── */}
            <Box marginTop={1}>
                {savingDraft ? (
                    <Spinner label="Saving draft..." />
                ) : (
                    <KeyHint hints={[
                        { key: "←→", label: "Switch Tab" },
                        { key: "Ctrl+E", label: "Send" },
                        { key: "Ctrl+S", label: "Save Draft" },
                        { key: "Esc", label: "Back" },
                    ]} />
                )}
            </Box>
        </Box>
    );
}
