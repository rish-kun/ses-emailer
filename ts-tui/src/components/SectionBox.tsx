/**
 * SectionBox — A visually distinct container with a title header.
 */

import React from "react";
import { Box, Text } from "ink";

interface SectionBoxProps {
    title: string;
    titleColor?: string;
    children: React.ReactNode;
    borderColor?: string;
}

export function SectionBox({
    title,
    titleColor = "cyan",
    children,
    borderColor = "gray",
}: SectionBoxProps) {
    return (
        <Box
            flexDirection="column"
            borderStyle="round"
            borderColor={borderColor}
            paddingX={1}
            paddingY={0}
        >
            <Box marginBottom={0}>
                <Text bold color={titleColor}>
                    {title}
                </Text>
            </Box>
            {children}
        </Box>
    );
}
