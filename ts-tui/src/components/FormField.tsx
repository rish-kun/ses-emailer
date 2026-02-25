import React, { useState, useRef, useEffect, useCallback } from "react";
import { Box, Text, useInput } from "ink";
import { TextInput } from "@inkjs/ui";

interface FormFieldProps {
    label: string;
    value: string;
    placeholder?: string;
    isActive: boolean;
    onChange: (value: string) => void;
    onSubmit?: () => void;
    labelWidth?: number;
    isPassword?: boolean;
}

export function FormField({
    label,
    value,
    placeholder = "",
    isActive,
    onChange,
    onSubmit,
    labelWidth = 20,
    isPassword = false,
}: FormFieldProps) {
    const onChangeRef = useRef(onChange);
    const onSubmitRef = useRef(onSubmit);
    const ignoreNextChange = useRef(false);
    const [remountKey, setRemountKey] = useState(0);

    // Intercept Ctrl+S (which ink-text-input sometimes treats as an 's' character)
    useInput((input, key) => {
        if (isActive && key.ctrl && input === "s") {
            ignoreNextChange.current = true;
            setRemountKey((k) => k + 1); // Wipe internal TextInput state on next render
        }
    });

    useEffect(() => {
        onChangeRef.current = onChange;
        onSubmitRef.current = onSubmit;
    }, [onChange, onSubmit]);

    const stableOnChange = useCallback((val: string) => {
        if (ignoreNextChange.current) {
            ignoreNextChange.current = false;
            return; // Drop the polluted string from reaching the parent state
        }
        onChangeRef.current(val);
    }, []);

    const stableOnSubmit = useCallback(() => {
        onSubmitRef.current?.();
    }, []);

    return (
        <Box>
            {/* Focus indicator */}
            <Text color={isActive ? "cyan" : undefined}>
                {isActive ? "▸ " : "  "}
            </Text>

            {/* Label */}
            <Box width={labelWidth}>
                <Text color={isActive ? "cyan" : "gray"} bold={isActive}>
                    {label}
                </Text>
            </Box>

            {/* Input */}
            <Box flexGrow={1}>
                {isActive ? (
                    <TextInput
                        key={remountKey}
                        defaultValue={value}
                        placeholder={placeholder}
                        onChange={stableOnChange}
                        onSubmit={stableOnSubmit}
                    />
                ) : (
                    <Text color="white">
                        {isPassword && value ? "•".repeat(value.length) : value || (
                            <Text dimColor>{placeholder}</Text>
                        )}
                    </Text>
                )}
            </Box>
        </Box>
    );
}
