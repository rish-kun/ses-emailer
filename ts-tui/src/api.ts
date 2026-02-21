/**
 * API client for communicating with the SES Email FastAPI backend.
 */

import axios, { type AxiosInstance, type AxiosRequestConfig } from "axios";

const apiUrl = process.env["API_URL"] || "http://127.0.0.1:8787";
const apiToken = process.env["API_TOKEN"] || "";

const client: AxiosInstance = axios.create({
    baseURL: apiUrl,
    headers: { Authorization: `Bearer ${apiToken}` },
    timeout: 30000,
});

// ── Config ──────────────────────────────────────────────────────────

export async function getConfig() {
    const { data } = await client.get("/api/config");
    return data;
}

export async function updateConfig(body: Record<string, unknown>) {
    const { data } = await client.put("/api/config", body);
    return data;
}

export async function listProfiles() {
    const { data } = await client.get("/api/config/profiles");
    return data as { active_profile: string; profiles: string[] };
}

export async function createProfile(name: string, copyFrom?: string) {
    const { data } = await client.post("/api/config/profiles", {
        name,
        copy_from: copyFrom,
    });
    return data;
}

export async function deleteProfile(name: string) {
    const { data } = await client.delete(`/api/config/profiles/${name}`);
    return data;
}

export async function activateProfile(name: string) {
    const { data } = await client.post(
        `/api/config/profiles/${name}/activate`
    );
    return data;
}

// ── Email ───────────────────────────────────────────────────────────

export interface SendRequest {
    recipients: string[];
    subject: string;
    body: string;
    email_type?: string;
    attachments?: string[];
}

/**
 * Returns the SSE URL for the send endpoint.
 * The TUI will consume this via EventSource or fetch streaming.
 */
export function getSendUrl() {
    return `${apiUrl}/api/emails/send`;
}

export function getAuthHeaders() {
    return { Authorization: `Bearer ${apiToken}` };
}

export async function uploadExcel(filePath: string, columnIndex = 0) {
    const fs = await import("fs");
    const path = await import("path");
    const FormData = (await import("form-data")).default;

    const form = new FormData();
    form.append("file", fs.createReadStream(filePath));
    form.append("column_index", String(columnIndex));

    const { data } = await client.post("/api/emails/upload-excel", form, {
        headers: { ...form.getHeaders() },
    });
    return data;
}

export async function compareRecipients(
    recipients: string[],
    emailId?: string,
    emailIds?: string[]
) {
    const { data } = await client.post("/api/emails/compare", {
        recipients,
        email_id: emailId,
        email_ids: emailIds,
    });
    return data;
}

export async function listFiles() {
    const { data } = await client.get("/api/files");
    return data;
}

// ── History ─────────────────────────────────────────────────────────

export async function listCampaigns(search = "") {
    const { data } = await client.get("/api/history", {
        params: search ? { search } : {},
    });
    return data;
}

export async function getCampaignDetail(id: string) {
    const { data } = await client.get(`/api/history/${id}`);
    return data;
}

export async function getStats() {
    const { data } = await client.get("/api/history/stats");
    return data;
}

// ── Drafts ──────────────────────────────────────────────────────────

export async function listDrafts() {
    const { data } = await client.get("/api/drafts");
    return data;
}

export async function getDraft(id: number) {
    const { data } = await client.get(`/api/drafts/${id}`);
    return data;
}

export async function createDraft(body: Record<string, unknown>) {
    const { data } = await client.post("/api/drafts", body);
    return data;
}

export async function updateDraft(id: number, body: Record<string, unknown>) {
    const { data } = await client.put(`/api/drafts/${id}`, body);
    return data;
}

export async function deleteDraft(id: number) {
    const { data } = await client.delete(`/api/drafts/${id}`);
    return data;
}

// ── DB / Health ─────────────────────────────────────────────────────

export async function healthCheck() {
    const { data } = await client.get("/health");
    return data;
}

export async function checkCredentials() {
    const { data } = await client.get("/api/db/check");
    return data;
}

export async function getDbStats() {
    const { data } = await client.get("/api/db/stats");
    return data;
}

// ── Lifecycle ────────────────────────────────────────────────────────

/** Tell the API server to shut itself down. Fire-and-forget; errors are ignored. */
export async function shutdownApi(): Promise<void> {
    try {
        await client.post("/shutdown", null, { timeout: 3000 });
    } catch {
        // Ignore — server may already be gone or unreachable
    }
}
