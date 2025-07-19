// static/js/dashboard.js

// Function to show the modal and populate the textarea with iframe code
// Updated to accept chatWidgetBaseUrl dynamically
function showEmbedModal(slug, chatWidgetBaseUrl) { // Added chatWidgetBaseUrl parameter
    const actualSlug = String(slug || '');

    // Use the dynamically passed base URL
    const chatWidgetUrl = `${chatWidgetBaseUrl}${actualSlug}/`;

    // Generate a simple iframe code snippet. Styles for embedding are kept minimal here.
    const iframeCodeString = `<iframe src="${chatWidgetUrl}" width="400" height="550" frameborder="0" title="CAPI Studio" style="border: 1px solid #ccc; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);"></iframe>`;

    // Set the value of the textarea
    const embedCodeTextarea = document.getElementById('embedCode');
    if (embedCodeTextarea) {
        embedCodeTextarea.value = iframeCodeString.trim();
    } else {
        console.error("Embed code textarea not found!");
        return;
    }

    // Display the modal
    const embedModal = document.getElementById('embedModal');
    if (embedModal) {
        embedModal.style.display = 'flex';
    } else {
        console.error("Embed modal not found!");
    }
}

// Function to close the modal
function closeEmbedModal() {
    const embedModal = document.getElementById('embedModal');
    if (embedModal) {
        embedModal.style.display = 'none';
        // Optional: Clear the textarea when closing
        const embedCodeTextarea = document.getElementById('embedCode');
        if (embedCodeTextarea) {
            embedCodeTextarea.value = '';
        }
    }
}

// Function to copy the embed code to clipboard
function copyEmbedCode() {
    const embedCodeTextarea = document.getElementById('embedCode');
    if (!embedCodeTextarea) {
        console.error("Embed code textarea not found for copying!");
        return;
    }

    embedCodeTextarea.select(); // Select the text
    embedCodeTextarea.setSelectionRange(0, 99999); // For mobile devices

    try {
        navigator.clipboard.writeText(embedCodeTextarea.value);
        // Provide user feedback
        alert('Iframe code copied to clipboard!');
        // Optionally close modal after copy
        // closeEmbedModal();
    } catch (err) {
        console.error('Failed to copy text:', err);
        alert('Failed to copy code. Please copy manually from the text area.');
    }
}

// Optional: Close modal if user clicks outside of the content area
window.addEventListener('click', function(event) {
    const modalOverlay = document.getElementById('embedModal');
    if (modalOverlay && event.target === modalOverlay) { // Check if target is the overlay itself
        closeEmbedModal();
    }
});

// Optional: Add event listener for Escape key to close modal
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' || event.key === 'Esc') {
        const modalOverlay = document.getElementById('embedModal');
        if (modalOverlay && modalOverlay.style.display === 'flex') {
            closeEmbedModal();
        }
    }
});