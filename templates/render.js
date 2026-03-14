#!/usr/bin/env bun
import { render } from '@react-email/render';
import { join, dirname } from 'path';

const templateName = process.argv[2];
const templatesDir = dirname(import.meta.url.replace('file://', ''));

if (!templateName) {
    console.error(JSON.stringify({ error: 'Template name required' }));
    process.exit(1);
}

async function renderTemplate() {
    const templatePath = join(templatesDir, `${templateName}.tsx`);
    
    try {
        const module = await import(templatePath);
        const Template = module.default;
        const html = await render(Template());
        console.log(JSON.stringify({ html }));
    } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        console.error(JSON.stringify({ error: message }));
        process.exit(1);
    }
}

renderTemplate();