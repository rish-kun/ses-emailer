/**
 * Client-side mail-merge helpers, mirroring sending/personalize.py.
 * Used for live preview and to decide when personalization applies.
 */

const TOKEN_RE = /\{\{\s*([\w .\-]+?)\s*\}\}/g;

/** Unique {{field}} names referenced across the given texts, in order. */
export function extractFields(...texts: string[]): string[] {
    const seen: string[] = [];
    for (const text of texts) {
        for (const match of (text || "").matchAll(TOKEN_RE)) {
            const name = match[1].trim();
            if (!seen.includes(name)) seen.push(name);
        }
    }
    return seen;
}

/** True if any text contains at least one {{token}}. */
export function hasTokens(...texts: string[]): boolean {
    return texts.some((t) => TOKEN_RE.test(t || ""));
}

/** Substitute {{token}} occurrences from fields (case-insensitive; unknown → ""). */
export function render(template: string, fields: Record<string, string>): string {
    if (!template) return template;
    const lookup: Record<string, string> = {};
    for (const [k, v] of Object.entries(fields)) {
        lookup[k.trim().toLowerCase()] = v == null ? "" : String(v);
    }
    return template.replace(TOKEN_RE, (_m, name: string) => lookup[name.trim().toLowerCase()] ?? "");
}
