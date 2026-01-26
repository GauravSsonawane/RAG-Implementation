// verify.js - End-to-End verification script
// This script calls the backend /verify endpoint and logs the result.
// It can be extended to perform UI checks with Playwright.

import fetch from 'node-fetch';

async function run() {
    try {
        const resp = await fetch('http://localhost:8002/verify');
        if (!resp.ok) {
            console.error('Backend verification failed with status', resp.status);
            process.exit(1);
        }
        const data = await resp.json();
        console.log('Backend verification result:', data);
        if (data.files_ok && data.citation_ok) {
            console.log('All checks passed.');
            process.exit(0);
        } else {
            console.error('Verification failed:', data);
            process.exit(1);
        }
    } catch (err) {
        console.error('Error during verification:', err);
        process.exit(1);
    }
}

run();
