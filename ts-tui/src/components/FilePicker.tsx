import React, { useState, useEffect } from "react";
import { Box, Text } from "ink";
import { Select } from "@inkjs/ui";
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

    useEffect(() => {
        try {
            const dirents = fs.readdirSync(currentPath, { withFileTypes: true });
            const dirs = dirents
                .filter((d) => d.isDirectory() && !d.name.startsWith("."))
                .sort((a, b) => a.name.localeCompare(b.name))
                .map((d) => ({ label: `📁 ${d.name}`, value: `DIR_${d.name}` }));

            const files = dirents
                .filter((d) => d.isFile() && !d.name.startsWith("."))
                .sort((a, b) => a.name.localeCompare(b.name))
                .map((d) => ({ label: `📄 ${d.name}`, value: `FILE_${d.name}` }));

            const newItems = [];
            if (currentPath !== "/") {
                newItems.push({ label: "📁 .. (Up a dir)", value: "DIR_.." });
            }

            if (allowDirs) {
                newItems.push({ label: "✅ Select this directory", value: "SELECT_DIR" });
            }

            newItems.push(...dirs, ...files, { label: "❌ Cancel", value: "CANCEL" });
            setItems(newItems);
        } catch (e) {
            setItems([
                { label: "❌ Error reading directory", value: "ERROR" },
                { label: "📁 .. (Up a dir)", value: "DIR_.." },
                { label: "❌ Cancel", value: "CANCEL" }
            ]);
        }
    }, [currentPath, allowDirs]);

    return (
        <Box flexDirection="column" paddingY={1}>
            <Text bold color="yellow">{title}</Text>
            <Text dimColor>Path: {currentPath}</Text>

            <Box marginTop={1} width="100%">
                <Select
                    visibleOptionCount={15}
                    options={items}
                    onChange={(val) => {
                        if (val === "CANCEL") {
                            onCancel();
                        } else if (val === "ERROR") {
                            // do nothing
                        } else if (val === "SELECT_DIR") {
                            onSelect(currentPath);
                        } else if (val.startsWith("DIR_")) {
                            const name = val.replace("DIR_", "");
                            setCurrentPath(path.resolve(currentPath, name));
                        } else if (val.startsWith("FILE_")) {
                            const name = val.replace("FILE_", "");
                            onSelect(path.join(currentPath, name));
                        }
                    }}
                />
            </Box>
        </Box>
    );
}
