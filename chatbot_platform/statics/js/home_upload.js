// static/js/home_upload.js

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const submitBtn = document.getElementById('submit-upload-btn');
    const fileInput = document.getElementById('id_files'); // Get the file input element
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    const messagesContainer = document.querySelector('.message-container');

    if (!uploadForm || !submitBtn || !fileInput) {
        console.error("home_upload.js: Required form elements not found!");
        return;
    }

    // Helper function to show messages
    function showMessage(type, text) {
        if (messagesContainer) {
            messagesContainer.innerHTML = `<ul class="messages"><li class="message ${type}">${text}</li></ul>`;
        }
    }

    // Helper function to convert File to Base64
    function fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file); // Reads as Base64 encoded data URL
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    }

    // --- Handle form submission via fetch API ---
    uploadForm.addEventListener('submit', async function(event) {
        event.preventDefault(); // Stop default form submission
        showMessage('info', 'Uploading and processing files...');

        const title = uploadForm.querySelector('[name="title"]').value.trim();
        const files = fileInput.files;

        if (!title) {
            showMessage('error', 'Please enter a title for the Knowledge Base.');
            return;
        }
        if (files.length === 0) {
            showMessage('error', 'Please select at least one file to upload.');
            return;
        }

        const filesData = [];
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            try {
                const base64Content = await fileToBase64(file);
                filesData.push({
                    filename: file.name,
                    content_type: file.type || 'application/octet-stream', // Fallback for unknown types
                    base64_content: base64Content.split(',')[1] // Get only Base64 part (after "data:mime/type;base64,")
                });
            } catch (error) {
                console.error("Error reading file:", file.name, error);
                showMessage('error', `Failed to read file: ${file.name}. Error: ${error.message}`);
                return; // Stop processing if any file fails
            }
        }

        const payload = {
            title: title,
            files: filesData,
            csrfmiddlewaretoken: csrfToken // Include CSRF token in JSON payload
        };

        try {
            const response = await fetch(uploadForm.action || window.location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json', // IMPORTANT: Sending JSON
                    'X-CSRFToken': csrfToken // Also send CSRF in header for good measure
                },
                body: JSON.stringify(payload)
            });

            const responseData = await response.json(); // Expect JSON response from server

            if (response.ok) {
                if (responseData.redirect_url) {
                    showMessage('success', responseData.message || 'Upload successful! Redirecting...');
                    window.location.href = responseData.redirect_url; // Handle redirects
                } else {
                    // This case is for validation errors returned as JSON, or success messages
                    // Assuming Django view sends JsonResponse with errors if form is invalid
                    if (responseData.errors) {
                        let errorMsgs = [];
                        for (const field in responseData.errors) {
                            responseData.errors[field].forEach(error => {
                                errorMsgs.push(`${field === '__all__' ? '' : field.charAt(0).toUpperCase() + field.slice(1)}: ${error}`);
                            });
                        }
                        showMessage('error', `Upload failed: ${errorMsgs.join('; ')}`);
                    } else {
                        showMessage('success', responseData.message || 'Upload successful!');
                        // Optional: Clear form or redirect as per design
                        // uploadForm.reset();
                    }
                }
            } else {
                // Server returned non-2xx status (e.g., 400, 500)
                const errorDetail = responseData.error || `Server responded with status ${response.status}.`;
                showMessage('error', `Upload failed: ${errorDetail}`);
                console.error("Server error during upload:", responseData);
            }
        } catch (error) {
            console.error("Network or parsing error:", error);
            showMessage('error', `An unexpected error occurred: ${error.message}`);
        }
    });
});