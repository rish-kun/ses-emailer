/**
 * KeyHint — Displays keyboard shortcut hints in a consistent style.
 */

import React from "react";
import { Box, Text } from "ink";

interface KeyHintProps {
    hints: Array<{ key: string; label: string }>;
}

export function KeyHint({ hints }: KeyHintProps) {
    return (
        <Box gap={1} flexWrap="wrap">
            {hints.map((h, i) => (
                <Box key={i}>
                    <Text dimColor>[</Text>
                    <Text color="yellow" bold>
                        {h.key}
                    </Text>
                    <Text dimColor>] {h.label}</Text>
                    {i < hints.length - 1 && <Text dimColor> │</Text>}
                </Box>
            ))}
        </Box>
    );
}
