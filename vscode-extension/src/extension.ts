import * as vscode from 'vscode';
import * as http from 'http';
import * as https from 'https';

// Track duration per language (in seconds)
let languageDurations: { [language: string]: { duration: number, lastFile: string } } = {};
let trackingInterval: NodeJS.Timeout | undefined;
let syncInterval: NodeJS.Timeout | undefined;

export function activate(context: vscode.ExtensionContext) {
    console.log('DevBrain extension is now active!');

    // Command to configure API Key
    let connectCmd = vscode.commands.registerCommand('devbrain.connect', async () => {
        const apiKey = await vscode.window.showInputBox({ 
            prompt: 'Enter your DevBrain API Key (or JWT Token)',
            ignoreFocusOut: true 
        });
        
        if (apiKey) {
            await vscode.workspace.getConfiguration('devbrain').update('apiKey', apiKey, true);
            vscode.window.showInformationMessage('DevBrain API Key saved!');
        }
    });
    context.subscriptions.push(connectCmd);

    // Track when a file is opened (passive event)
    vscode.workspace.onDidOpenTextDocument((doc) => {
        // We only respond to actual files on disk
        if (doc.uri.scheme === 'file') {
            console.log(`Opened ${doc.fileName} (${doc.languageId})`);
        }
    });

    // 1. Time Tracking (tick every minute)
    trackingInterval = setInterval(() => {
        // Only track if VS Code is focused and there is an active editor
        if (vscode.window.state.focused && vscode.window.activeTextEditor) {
            const doc = vscode.window.activeTextEditor.document;
            if (doc.uri.scheme === 'file') {
                const lang = doc.languageId;
                const fileName = doc.fileName.split(/[/\\]/).pop() || 'Unknown File';
                
                if (!languageDurations[lang]) {
                    languageDurations[lang] = { duration: 0, lastFile: fileName };
                }
                
                languageDurations[lang].duration += 60; // Add 60 seconds
                languageDurations[lang].lastFile = fileName;
            }
        }
    }, 60 * 1000); // Check every 60 seconds

    // 2. Sync to Backend (every 5 minutes)
    syncInterval = setInterval(() => {
        syncEvents();
    }, 5 * 60 * 1000); // Emit every 5 minutes
    
    // Attempt sync on deactivation
    context.subscriptions.push({
        dispose: () => {
            syncEvents();
            if (trackingInterval) clearInterval(trackingInterval);
            if (syncInterval) clearInterval(syncInterval);
        }
    });
}

function syncEvents() {
    const config = vscode.workspace.getConfiguration('devbrain');
    const apiUrl = config.get<string>('apiUrl', 'http://127.0.0.1:8001/api/events/vscode');
    const apiKey = config.get<string>('apiKey', '');

    if (!apiKey) {
        console.warn('DevBrain: No API key configured. Skipping sync.');
        return;
    }

    const payloadLanguages = Object.keys(languageDurations);
    if (payloadLanguages.length === 0) return;

    for (const lang of payloadLanguages) {
        const data = languageDurations[lang];
        if (data.duration <= 0) continue;

        const payload = JSON.stringify({
            event_type: 'coding',
            tool: 'vscode',
            language: lang,
            duration: data.duration,
            file_name: data.lastFile
        });

        // Clear local tracking once payload is prepared
        delete languageDurations[lang];

        sendRequest(apiUrl, apiKey, payload);
    }
}

function sendRequest(url: string, token: string, payload: string) {
    const isHttps = url.startsWith('https');
    const client = isHttps ? https : http;
    const { URL } = require('url');
    const parsedUrl = new URL(url);

    const options = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port,
        path: parsedUrl.pathname + parsedUrl.search,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'Content-Length': Buffer.byteLength(payload)
        }
    };

    const req = client.request(options, (res: any) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
            console.log(`DevBrain: Synced coding stats successfully.`);
        } else {
            console.error(`DevBrain: Failed to sync stats. Status code: ${res.statusCode}`);
        }
    });

    req.on('error', (e: any) => {
        console.error(`DevBrain: Request error: ${e.message}`);
    });

    req.write(payload);
    req.end();
}

export function deactivate() {
    if (trackingInterval) clearInterval(trackingInterval);
    if (syncInterval) clearInterval(syncInterval);
}
