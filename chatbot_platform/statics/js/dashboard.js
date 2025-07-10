
// Function to show the modal and populate the textarea dengan iframe code
function showEmbedModal(slug) {
    const actualSlug = String(slug || '');

    // The URL needs to point to the DEPLOYED Cloud Run URL, not localhost
    const chatWidgetUrl = `https://chatbot-api-platform-29773676777.us-central1.run.app/chat/${actualSlug}/`;

    // Generate a VERY simple iframe code snippet. No hardcoded styles for positioning.
    const iframeCodeString = `<iframe src="${chatWidgetUrl}" width="400" height="550" frameborder="0" title="CAPI Studio" style="border: 1px solid #ccc; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);"></iframe>`;
    // Set the value of the textarea
    document.getElementById('embedCode').value = iframeCodeString.trim(); // Use trim() for clean formatting

    // Display the modal
    document.getElementById('embedModal').style.display = 'flex';
}

// Function to close the modal
function closeEmbedModal() {
    document.getElementById('embedModal').style.display = 'none';
    // Optional: Clear the textarea when closing
    document.getElementById('embedCode').value = '';
}