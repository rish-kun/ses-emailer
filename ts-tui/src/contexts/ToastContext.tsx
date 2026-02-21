import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { Box, Text } from "ink";

export type ToastType = "error" | "info" | "success";

interface ToastContextType {
    showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export const useToast = () => {
    const ctx = useContext(ToastContext);
    if (!ctx) throw new Error("useToast must be used within ToastProvider");
    return ctx;
};

class ErrorBoundary extends React.Component<{ children: ReactNode; onError: (err: Error) => void }, { hasError: boolean }> {
    constructor(props: any) {
        super(props);
        this.state = { hasError: false };
    }
    static getDerivedStateFromError() {
        return { hasError: true };
    }
    componentDidCatch(error: Error) {
        this.props.onError(error);
        setTimeout(() => this.setState({ hasError: false }), 4000);
    }
    render() {
        if (this.state.hasError) {
            return (
                <Box padding={1} borderColor="red" borderStyle="single">
                    <Text color="red">A rendering error occurred in this component.</Text>
                </Box>
            );
        }
        return this.props.children;
    }
}

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toast, setToast] = useState<{ message: string; type: ToastType } | null>(null);

    const showToast = (message: string, type: ToastType = "info") => {
        setToast({ message, type });
    };

    useEffect(() => {
        if (toast) {
            const timer = setTimeout(() => setToast(null), 5000);
            return () => clearTimeout(timer);
        }
    }, [toast]);

    useEffect(() => {
        const handleUncaught = (error: Error) => {
            showToast(error.message || "Unknown error", "error");
        };
        const handleRejection = (reason: any) => {
            showToast(reason?.message || "Unhandled promise rejection", "error");
        };
        process.on("uncaughtException", handleUncaught);
        process.on("unhandledRejection", handleRejection);
        return () => {
            process.off("uncaughtException", handleUncaught);
            process.off("unhandledRejection", handleRejection);
        };
    }, []);

    const borderColor = toast?.type === "error" ? "red" : toast?.type === "success" ? "green" : "blue";
    const icon = toast?.type === "error" ? "✖ " : toast?.type === "success" ? "✔ " : "ℹ ";

    return (
        <ToastContext.Provider value={{ showToast }}>
            <ErrorBoundary onError={(err) => showToast(err.message, "error")}>
                <Box flexDirection="column" flexGrow={1}>
                    {children}
                </Box>
            </ErrorBoundary>

            {toast && (
                <Box alignSelf="flex-end" marginBottom={1}>
                    <Box
                        borderStyle="round"
                        borderColor={borderColor}
                        paddingX={1}
                    >
                        <Text color={toast.type === "error" ? "red" : "white"}>
                            {icon}{toast.message}
                        </Text>
                    </Box>
                </Box>
            )}
        </ToastContext.Provider>
    );
}
