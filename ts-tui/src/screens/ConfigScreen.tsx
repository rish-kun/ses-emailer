/**
 * Config screen — Redesigned with a master menu and sub-screens to reduce clutter.
 */

import React, { useState, useEffect, useCallback } from "react";
import { Box, Text, useInput } from "ink";
import { TextInput, Spinner, Alert, Select } from "@inkjs/ui";
import {
    getConfig,
    updateConfig,
    listProfiles,
    createProfile,
    deleteProfile,
    activateProfile,
} from "../api.js";
import { FormField } from "../components/FormField.js";
import { SectionBox } from "../components/SectionBox.js";
import { KeyHint } from "../components/KeyHint.js";
import type { Screen } from "../App.js";

interface Props {
    setScreen: (s: Screen) => void;
}

type MenuOption = "menu" | "profiles" | "aws" | "sender" | "batch" | "recipients";

export function ConfigScreen({ setScreen }: Props) {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    // Navigation
    const [view, setView] = useState<MenuOption>("menu");

    // Config state
    const [profiles, setProfiles] = useState<string[]>([]);
    const [activeProfile, setActiveProfile] = useState("default");

    // Forms state
    const [activeField, setActiveField] = useState<string>("");
    const [awsFields, setAwsFields] = useState({ access_key: "", secret_key: "", region: "", source_email: "" });
    const [senderFields, setSenderFields] = useState({ sender_name: "", reply_to: "", default_to: "" });
    const [batchFields, setBatchFields] = useState({ batch_size: "50", delay: "60" });
    const [testRecipients, setTestRecipients] = useState("");

    // Create profile
    const [showNewProfile, setShowNewProfile] = useState(false);

    const [message, setMessage] = useState("");
    const [messageType, setMessageType] = useState<"success" | "error">("success");

    const loadConfig = useCallback(async () => {
        setLoading(true);
        try {
            const [cfgRes, profRes] = await Promise.all([getConfig(), listProfiles()]);
            setActiveProfile(cfgRes.active_profile);
            setProfiles(profRes.profiles);

            const aws = cfgRes.config.aws || {};
            setAwsFields({
                access_key: aws.access_key_id || "",
                secret_key: aws.secret_access_key || "",
                region: aws.region || "us-east-1",
                source_email: aws.source_email || "",
            });

            const sender = cfgRes.config.sender || {};
            setSenderFields({
                sender_name: sender.sender_name || "",
                reply_to: sender.reply_to || "",
                default_to: sender.default_to || "",
            });

            const batch = cfgRes.config.batch || {};
            setBatchFields({
                batch_size: String(batch.batch_size || 50),
                delay: String(batch.delay_seconds || 60),
            });

            setTestRecipients((cfgRes.config.test_recipients || []).join("\n"));
        } catch (err) {
            setMessage(`Error loading config: ${err}`);
            setMessageType("error");
        }
        setLoading(false);
    }, []);

    useEffect(() => {
        loadConfig();
    }, [loadConfig]);

    const handleSave = useCallback(async () => {
        setSaving(true);
        setMessage("");
        try {
            await updateConfig({
                aws: {
                    access_key_id: awsFields.access_key,
                    secret_access_key: awsFields.secret_key,
                    region: awsFields.region,
                    source_email: awsFields.source_email,
                },
                sender: {
                    sender_name: senderFields.sender_name,
                    reply_to: senderFields.reply_to,
                    default_to: senderFields.default_to,
                },
                batch: {
                    batch_size: parseInt(batchFields.batch_size) || 50,
                    delay_seconds: parseFloat(batchFields.delay) || 60,
                },
                test_recipients: testRecipients
                    .split(/[\n,]/)
                    .map((s) => s.trim())
                    .filter(Boolean),
            });
            setMessage("✓ Configuration saved successfully!");
            setMessageType("success");
            setView("menu");
        } catch (err) {
            setMessage(`Save failed: ${err}`);
            setMessageType("error");
        }
        setSaving(false);
    }, [awsFields, senderFields, batchFields, testRecipients]);

    const handleMenuSelect = (value: string) => {
        if (value === "back") {
            setScreen("home");
            return;
        }
        setView(value as MenuOption);
        setMessage("");

        // Auto-focus first field based on view
        if (value === "aws") setActiveField("access_key");
        if (value === "sender") setActiveField("sender_name");
        if (value === "batch") setActiveField("batch_size");
        if (value === "recipients") setActiveField("test_recipients");
    };

    // HOOKS MUST BE BEFORE CONDITIONAL RETURNS!
    useInput((input, key) => {
        if (key.escape) {
            if (showNewProfile) {
                setShowNewProfile(false);
                return;
            }
            if (view !== "menu") {
                setView("menu");
                setActiveField("");
                return;
            }
            setScreen("home");
            return;
        }

        if (view === "menu") return;

        if (view === "profiles") {
            if (input === 'n' && !showNewProfile) {
                setShowNewProfile(true);
            }
            return;
        }

        if (showNewProfile) return;

        // Field cycling logic
        if (key.tab) {
            let fields: string[] = [];
            if (view === "aws") fields = ["access_key", "secret_key", "region", "source_email"];
            if (view === "sender") fields = ["sender_name", "reply_to", "default_to"];
            if (view === "batch") fields = ["batch_size", "delay"];
            if (view === "recipients") fields = ["test_recipients"];

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

        if (key.ctrl && input === "s") {
            handleSave();
        }
    });

    if (loading) {
        return <Box paddingY={2}><Spinner label="Loading configuration..." /></Box>;
    }

    // Common Header
    const header = (
        <Box marginBottom={1}>
            <Text bold color="magenta">⚙ Settings</Text>
            <Text> — Profile: </Text>
            <Text bold color="cyan">{activeProfile}</Text>
        </Box>
    );

    // Main Menu View
    if (view === "menu") {
        return (
            <Box flexDirection="column">
                {header}

                {message && (
                    <Box marginBottom={1}><Alert variant={messageType}>{message}</Alert></Box>
                )}

                <SectionBox title="Settings Menu" borderColor="blue">
                    <Box flexDirection="column" paddingY={1} width={40}>
                        <Select
                            options={[
                                { label: "Manage Profiles", value: "profiles" },
                                { label: "AWS Credentials", value: "aws" },
                                { label: "Sender Settings", value: "sender" },
                                { label: "Batch Settings", value: "batch" },
                                { label: "Test Recipients", value: "recipients" },
                                { label: "Back to Home", value: "back" }
                            ]}
                            onChange={handleMenuSelect}
                        />
                    </Box>
                </SectionBox>

                <Box marginTop={1}>
                    <KeyHint hints={[
                        { key: "↑↓", label: "Select" },
                        { key: "Enter", label: "Open" },
                        { key: "Esc", label: "Back" },
                    ]} />
                </Box>
            </Box>
        );
    }

    // Profile Manager View
    if (view === "profiles") {
        return (
            <Box flexDirection="column">
                {header}

                <SectionBox title="Manage Profiles" borderColor="yellow">
                    <Box flexDirection="column" paddingY={1}>
                        <Box marginBottom={1}>
                            <Text dimColor>Select a profile to activate, or press N to create new.</Text>
                        </Box>

                        {!showNewProfile && (
                            <Box width={30}>
                                <Select
                                    options={[
                                        ...profiles.map(p => ({
                                            label: `${p === activeProfile ? "●" : "○"} ${p}`,
                                            value: `ACTIVATE_${p}`
                                        })),
                                        ...profiles.filter(p => p !== "default").map(p => ({
                                            label: `❌ Delete '${p}'`,
                                            value: `DELETE_${p}`
                                        }))
                                    ]}
                                    onChange={async (val) => {
                                        if (val.startsWith("ACTIVATE_")) {
                                            const name = val.replace("ACTIVATE_", "");
                                            if (name === activeProfile) return;
                                            try {
                                                await activateProfile(name);
                                                await loadConfig();
                                                setMessage(`Activated ${name}`);
                                                setMessageType("success");
                                            } catch (e) { setMessage(String(e)); setMessageType("error"); }
                                        } else if (val.startsWith("DELETE_")) {
                                            const name = val.replace("DELETE_", "");
                                            try {
                                                await deleteProfile(name);
                                                await loadConfig();
                                                setMessage(`Deleted ${name}`);
                                                setMessageType("success");
                                            } catch (e) { setMessage(String(e)); setMessageType("error"); }
                                        }
                                    }}
                                />
                            </Box>
                        )}

                        {showNewProfile && (
                            <Box marginTop={1} flexDirection="column">
                                <Text color="yellow">New profile name:</Text>
                                <TextInput
                                    placeholder="e.g. staging"
                                    onSubmit={async (val) => {
                                        if (!val.trim()) {
                                            setShowNewProfile(false);
                                            return;
                                        }
                                        try {
                                            await createProfile(val.trim());
                                            await loadConfig();
                                            setMessage(`Created ${val}`);
                                            setMessageType("success");
                                            setShowNewProfile(false);
                                        } catch (e) { setMessage(String(e)); setMessageType("error"); }
                                    }}
                                />
                                <Box marginTop={1}>
                                    <Text dimColor>Press Enter to save, Esc to cancel.</Text>
                                </Box>
                            </Box>
                        )}

                        {message && (
                            <Box marginTop={1}><Alert variant={messageType}>{message}</Alert></Box>
                        )}
                    </Box>
                </SectionBox>

                <Box marginTop={1}>
                    <KeyHint hints={[
                        { key: "N", label: "New Profile" },
                        { key: "Esc", label: "Back to Menu" },
                    ]} />
                </Box>
            </Box>
        );
    }

    // Generic Form Render Generator
    const renderFormFields = () => {
        const focusNext = () => null; // Dummy, handled by useInput

        if (view === "aws") {
            return (
                <SectionBox title="AWS Credentials" borderColor="cyan">
                    <Box flexDirection="column" gap={0} paddingY={1}>
                        <FormField
                            label="Access Key ID" value={awsFields.access_key} isActive={activeField === "access_key"}
                            onChange={(v) => setAwsFields({ ...awsFields, access_key: v })} onSubmit={focusNext}
                        />
                        <FormField
                            label="Secret Key" value={awsFields.secret_key} isActive={activeField === "secret_key"} isPassword
                            onChange={(v) => setAwsFields({ ...awsFields, secret_key: v })} onSubmit={focusNext}
                        />
                        <FormField
                            label="Region" value={awsFields.region} isActive={activeField === "region"}
                            onChange={(v) => setAwsFields({ ...awsFields, region: v })} onSubmit={focusNext}
                        />
                        <FormField
                            label="Source Email" value={awsFields.source_email} isActive={activeField === "source_email"}
                            onChange={(v) => setAwsFields({ ...awsFields, source_email: v })} onSubmit={focusNext}
                        />
                    </Box>
                </SectionBox>
            );
        }

        if (view === "sender") {
            return (
                <SectionBox title="Sender Settings" borderColor="cyan">
                    <Box flexDirection="column" gap={0} paddingY={1}>
                        <FormField
                            label="Display Name" value={senderFields.sender_name} isActive={activeField === "sender_name"}
                            onChange={(v) => setSenderFields({ ...senderFields, sender_name: v })} onSubmit={focusNext}
                        />
                        <FormField
                            label="Reply-To Email" value={senderFields.reply_to} isActive={activeField === "reply_to"}
                            onChange={(v) => setSenderFields({ ...senderFields, reply_to: v })} onSubmit={focusNext}
                        />
                        <FormField
                            label="Default TO" value={senderFields.default_to} isActive={activeField === "default_to"}
                            onChange={(v) => setSenderFields({ ...senderFields, default_to: v })} onSubmit={focusNext}
                        />
                    </Box>
                </SectionBox>
            );
        }

        if (view === "batch") {
            return (
                <SectionBox title="Batch Settings" borderColor="cyan">
                    <Box flexDirection="column" gap={0} paddingY={1}>
                        <FormField
                            label="Batch Size" value={batchFields.batch_size} isActive={activeField === "batch_size"}
                            onChange={(v) => setBatchFields({ ...batchFields, batch_size: v })} onSubmit={focusNext}
                        />
                        <FormField
                            label="Delay (seconds)" value={batchFields.delay} isActive={activeField === "delay"}
                            onChange={(v) => setBatchFields({ ...batchFields, delay: v })} onSubmit={focusNext}
                        />
                    </Box>
                </SectionBox>
            );
        }

        if (view === "recipients") {
            return (
                <SectionBox title="Test Recipients" borderColor="cyan">
                    <Box flexDirection="column" gap={0} paddingY={1}>
                        <Text dimColor>Enter test recipients (comma separated):</Text>
                        <Box marginTop={1}>
                            <FormField
                                label="Recipients" value={testRecipients} isActive={activeField === "test_recipients"}
                                onChange={setTestRecipients} onSubmit={focusNext}
                            />
                        </Box>
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

            {renderFormFields()}

            <Box marginTop={1}>
                <Text dimColor>
                    <Text color="yellow">Tab</Text> next field │ <Text color="yellow">Shift+Tab</Text> prev field
                </Text>
            </Box>

            <Box marginTop={1}>
                {saving ? (
                    <Spinner label="Saving..." />
                ) : (
                    <KeyHint hints={[
                        { key: "Ctrl+S", label: "Save & Exit" },
                        { key: "Esc", label: "Cancel & Menu" },
                    ]} />
                )}
            </Box>
        </Box>
    );
}
