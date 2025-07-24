// static/js/dashboard.js

// Existing functions for embed modal (retained from your code)
function showEmbedModal(slug, chatWidgetBaseUrl) {
    const actualSlug = String(slug || '');
    const chatWidgetUrl = `${chatWidgetBaseUrl}${actualSlug}/`;
    const iframeCodeString = `<iframe src="${chatWidgetUrl}" width="400" height="550" frameborder="0" title="CAPI Studio" style="border: 1px solid #ccc; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);"></iframe>`;
    const embedCodeTextarea = document.getElementById('embedCode');
    if (embedCodeTextarea) { embedCodeTextarea.value = iframeCodeString.trim(); } else { console.error("Embed code textarea not found!"); return; }
    const embedModal = document.getElementById('embedModal');
    if (embedModal) { embedModal.style.display = 'flex'; } else { console.error("Embed modal not found!"); }
}

function closeEmbedModal() {
    const embedModal = document.getElementById('embedModal');
    if (embedModal) { embedModal.style.display = 'none'; }
    const embedCodeTextarea = document.getElementById('embedCode');
    if (embedCodeTextarea) { embedCodeTextarea.value = ''; }
}

function copyEmbedCode() {
    const embedCodeTextarea = document.getElementById('embedCode');
    if (!embedCodeTextarea) { console.error("Embed code textarea not found for copying!"); return; }
    embedCodeTextarea.select();
    embedCodeTextarea.setSelectionRange(0, 99999); // For mobile devices
    try {
        navigator.clipboard.writeText(embedCodeTextarea.value);
        alert('Iframe code copied to clipboard!');
    } catch (err) {
        console.error('Failed to copy text:', err);
        alert('Failed to copy code. Please copy manually from the text area.');
    }
}

window.addEventListener('click', function(event) {
    const modalOverlay = document.getElementById('embedModal');
    if (modalOverlay && event.target === modalOverlay) { closeEmbedModal(); }
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' || event.key === 'Esc') {
        const modalOverlay = document.getElementById('embedModal');
        if (modalOverlay && modalOverlay.style.display === 'flex') { closeEmbedModal(); }
    }
});


// --- NEW POLLING LOGIC ---
document.addEventListener('DOMContentLoaded', function() {
    console.log("Dashboard JS: DOMContentLoaded fired. Script starting.");
    const kbElements = document.querySelectorAll('li.knowledge-base-item[data-kb-id]'); 
    const pollingInterval = 5000; // Poll every 5 seconds (adjust as needed)

    let activePolls = {}; // To keep track of polling intervals for each KB

    function updateKbCard(kbElement, statusData) {
        console.log(`updateKbCard called for KB ${kbElement.dataset.kbId}. New status received: ${statusData.status}.`);
        const kbId = kbElement.dataset.kbId;
        const statusBadge = document.getElementById(`kb-status-${kbId}`);
        const buttonsDiv = document.getElementById(`kb-buttons-${kbId}`);
        const errorMsgP = document.getElementById(`kb-error-${kbId}`);

        // 1. Update status badge
        if (statusBadge) {
            statusBadge.textContent = statusData.status_display;
            statusBadge.className = 'status-badge'; // Reset classes
            statusBadge.classList.add(`status-${statusData.status}`); // Add new status class
            kbElement.dataset.kbStatus = statusData.status; // IMPORTANT: Update dataset status for next poll cycle
            console.log(`KB ${kbId} badge updated to: ${statusData.status_display} (Dataset: ${kbElement.dataset.kbStatus}).`);
        } else {
            console.warn(`KB ${kbId} statusBadge element not found!`);
        }


        // 2. Update buttons based on status
        if (buttonsDiv) {
            let newButtonsHtml = '';
            // Get CSRF token from a hidden input in the existing delete form (assuming it's the first one on page)
            const csrfTokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
            const csrfToken = csrfTokenInput ? csrfTokenInput.value : '';

            // Safely get KB Title for delete button confirmation
            const kbTitleElement = kbElement.querySelector('.card-title');
            const kbTitle = kbTitleElement ? kbTitleElement.textContent.trim() : 'this Knowledge Base';
            console.log(`KB ${kbId} title for delete confirmation: '${kbTitle}'.`);


            if (statusData.status === 'uploaded' || statusData.status === 'failed') {
                newButtonsHtml = `<a href="/proceed/${kbId}/" class="btn btn-proceed" onclick="this.classList.add('disable'); this.innerText='Starting...'">Proceed & Embed</a>`;
            } else if (statusData.status === 'processing') {
                newButtonsHtml = `<button class="btn btn-processing" disabled>Embedding In Progress...</button>`;
            } else if (statusData.status === 'completed') {
                const widgetSlug = statusData.widget_slug;
                console.log(`KB ${kbId} status is completed. Widget Slug: ${widgetSlug}.`);
                const chatWidgetBaseUrl = window.location.protocol + '//' + window.location.host + '/chat/'; 
                newButtonsHtml = `
                    <a href="${chatWidgetBaseUrl}${widgetSlug}/" class="btn btn-test" target="_blank">Test Widget</a>
                    <button class="btn btn-api" onclick="showEmbedModal('${widgetSlug}', '${chatWidgetBaseUrl}')">Get Widget API</button>
                `;
            }
            // Reconstruct the delete button form always
            const deleteFormHtml = `
                <form action="/delete/${kbId}/" method="post" class="ms-auto"
                    onsubmit="return confirm('Are you sure you want to delete this Knowledge Base: \\'${kbTitle}\\'? This action cannot be undone.');">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                    <button type="submit" class="btn btn-danger">Delete</button>
                </form>
            `;
            // Set innerHTML to update buttons
            buttonsDiv.innerHTML = newButtonsHtml + deleteFormHtml;
            console.log(`KB ${kbId} buttons updated to reflect status: ${statusData.status}.`);
        } else {
            console.warn(`KB ${kbId} buttonsDiv element not found!`);
        }

        // 3. Update error message
        if (errorMsgP) {
            if (statusData.status === 'failed' && statusData.error_message) {
                errorMsgP.textContent = `Error: ${statusData.error_message}`;
                errorMsgP.style.display = 'block';
                console.log(`KB ${kbId} error message updated.`);
            } else {
                errorMsgP.textContent = '';
                errorMsgP.style.display = 'none';
            }
        } else {
            console.warn(`KB ${kbId} errorMsgP element not found!`);
        }
    }

    async function pollKbStatus(kbElement) {
        const kbId = kbElement.dataset.kbId;
        const currentStatus = kbElement.dataset.kbStatus; 
        console.log(`Polling for KB ${kbId}. Current status (dataset): ${currentStatus}.`);

        if (currentStatus === 'processing' || currentStatus === 'uploaded' || currentStatus === 'failed') {
            try {
                const response = await fetch(`/api/kb_status/${kbId}/`); 
                const data = await response.json();
                console.log(`API response for KB ${kbId}:`, data);

                if (response.ok) {
                    // Check if status has actually changed from the last known state
                    if (kbElement.dataset.kbStatus !== data.status) {
                        console.log(`KB ${kbId} status change detected: ${kbElement.dataset.kbStatus} -> ${data.status}. Updating UI.`);
                        updateKbCard(kbElement, data); // Update the UI
                    } else {
                        console.log(`KB ${kbId} status is still ${data.status}. No UI update needed.`);
                    }
                    
                    // Stop polling if status is completed or failed
                    if (data.status === 'completed' || data.status === 'failed') {
                        clearInterval(activePolls[kbId]);
                        delete activePolls[kbId];
                        console.log(`Polling stopped for KB ${kbId}. Final Status: ${data.status}.`);
                        
                        // Show a success/error message on the main message container
                        const mainMessagesDiv = document.querySelector('.message-container .messages');
                        if (mainMessagesDiv) {
                            // Select specific li by data-kb-id to prevent duplicates
                            const existingMsg = mainMessagesDiv.querySelector(`li[data-kb-id="${kbId}"]`); 
                            if (!existingMsg) { // Only add if not already present
                                const kbTitle = kbElement.querySelector('.card-title').textContent; 
                                if (data.status === 'completed') {
                                    mainMessagesDiv.innerHTML += `<li class="message success" data-kb-id="${kbId}">Knowledge Base '${kbTitle}' embedded successfully!</li>`;
                                } else if (data.status === 'failed') {
                                    mainMessagesDiv.innerHTML += `<li class="message error" data-kb-id="${kbId}">Knowledge Base '${kbTitle}' failed to embed: ${data.error_message || 'Unknown error.'}</li>`;
                                }
                            } else {
                                console.log(`KB ${kbId} message already exists in main message container, not adding duplicate.`);
                            }
                        }
                    }
                } else {
                    console.error(`Error polling status for KB ${kbId}: ${data.error || 'Unknown error'}. Status: ${response.status}.`);
                }
            } catch (error) {
                console.error(`Network error during polling for KB ${kbId}:`, error);
            }
        } else {
            // If KB is already completed or not in a polling state, ensure its polling is stopped
            if (activePolls[kbId]) {
                clearInterval(activePolls[kbId]);
                delete activePolls[kbId];
                console.log(`Polling stopped for KB ${kbId} (status: ${currentStatus}).`);
            }
        }
    }

    // Initialize polling for all relevant KB cards on page load
    if (kbElements.length === 0) {
        console.log("Dashboard JS: No Knowledge Base cards found to poll.");
    }
    kbElements.forEach(kbElement => {
        const initialStatus = kbElement.dataset.kbStatus;
        const kbId = kbElement.dataset.kbId;
        
        console.log(`KB ${kbId}: Initial status detected: ${initialStatus}.`);

        if (initialStatus === 'processing' || initialStatus === 'uploaded' || initialStatus === 'failed') {
            console.log(`KB ${kbId}: Starting polling loop.`);
            pollKbStatus(kbElement); // Run once immediately
            activePolls[kbId] = setInterval(() => pollKbStatus(kbElement), pollingInterval);
        } else {
            console.log(`KB ${kbId}: Status '${initialStatus}' does not require polling.`);
        }
    });
});