import React, { useState, useEffect } from "react";
import { Box, Text } from "ink";
import { Select, TextInput } from "@inkjs/ui";
import fs from "fs";
import path from "path";

interface FilePickerProps {
    onSelect: (filePath: string) => void;
    onCancel: () => void;
    title?: string;
    allowDirs?: boolean;
}

export function FilePicker({ onSelect, onCancel, title = "Select File", allowDirs = false }: FilePickerProps) {
    const [currentPath, setCurrentPath] = useState(process.cwd());
    const [items, setItems] = useState<{ label: string; value: string }[]>([]);
    const [searchQuery, setSearchQuery] = useState("");

    useEffect(() => {
        try {
            const dirents = fs.readdirSync(currentPath, { withFileTypes: true });
            const filterFn = (name: string) => !searchQuery || name.toLowerCase().includes(searchQuery.toLowerCase());

            const dirs = dirents
                .filter((d) => d.isDirectory() && !d.name.startsWith(".") && filterFn(d.name))
                .sort((a, b) => a.name.localeCompare(b.name))
                .map((d) => ({ label: `📁 ${d.name}`, value: `DIR_${path.join(currentPath, d.name)}` }));

            const files = dirents
                .filter((d) => d.isFile() && !d.name.startsWith(".") && filterFn(d.name))
                .sort((a, b) => a.name.localeCompare(b.name))
                .map((d) => ({ label: `📄 ${d.name}`, value: `FILE_${path.join(currentPath, d.name)}` }));

            const newItems = [];
            if (currentPath !== "/") {
                newItems.push({ label: "📁 .. (Up a dir)", value: `DIR_${path.resolve(currentPath, "..")}` });
            }

            if (allowDirs) {
                newItems.push({ label: "✅ Select this directory", value: "SELECT_DIR" });
            }

            newItems.push(...dirs, ...files);

            if (newItems.length === 0) {
                newItems.push({ label: "⚠️ No results found", value: "NO_RESULTS" });
            }

            newItems.push({ label: "❌ Cancel", value: "CANCEL" });
            setItems(newItems);
        } catch (e) {
            setItems([
                { label: "❌ Error reading directory", value: "ERROR" },
                { label: "📁 .. (Up a dir)", value: `DIR_${path.resolve(currentPath, "..")}` },
                { label: "❌ Cancel", value: "CANCEL" }
            ]);
        }
    }, [currentPath, allowDirs, searchQuery]);

    return (
        <Box flexDirection="column" paddingY={1}>
            <Text bold color="yellow">{title}</Text>
            <Text dimColor>Path: {currentPath}</Text>

            <Box marginTop={1} flexDirection="column">
                <Text bold dimColor>Search (Tab to results):</Text>
                <TextInput
                    key={currentPath}
                    placeholder="Type to filter..."
                    onChange={setSearchQuery}
                />
            </Box>

            <Box marginTop={1} width="100%">
                <Select
                    visibleOptionCount={15}
                    options={items}
                    onChange={(val) => {
                        if (val === "CANCEL") {
                            onCancel();
                        } else if (val === "ERROR" || val === "NO_RESULTS") {
                            // do nothing
                        } else if (val === "SELECT_DIR") {
                            onSelect(currentPath);
                        } else if (val.startsWith("DIR_")) {
                            const name = val.substring(4);
                            setCurrentPath(name);
                            setSearchQuery(""); // clear search when navigating
                        } else if (val.startsWith("FILE_")) {
                            const name = val.substring(5);
                            onSelect(name);
                        }
                    }}
                />
            </Box>
        </Box>
    );
}
