// Admin panel: upload + embed + book list.

document.addEventListener('DOMContentLoaded', function () {
    const uploadForm = document.getElementById('upload-form');
    const booksDiv = document.getElementById('books');

    async function loadBooks() {
        try {
            const res = await fetch('/admin/books');
            if (!res.ok) return;
            const books = await res.json();
            booksDiv.innerHTML = '';
            books.forEach(function (book) {
                const div = document.createElement('div');
                div.className = 'book-item';
                div.innerHTML =
                    '<strong>' + book.book_name + '</strong> — ' + book.author_name +
                    ' (' + book.fiqha + ', rank ' + book.rank + ')' +
                    '<div class="status">Status: ' + book.status +
                    (book.error_message ? ' — ' + book.error_message : '') + '</div>';
                booksDiv.appendChild(div);
            });
        } catch (e) {
            console.error('Failed to load books', e);
        }
    }

    uploadForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const formData = new FormData(uploadForm);

        try {
            const uploadRes = await fetch('/admin/upload', {
                method: 'POST',
                body: formData
            });
            if (!uploadRes.ok) {
                const err = await uploadRes.json();
                alert('Upload failed: ' + (err.detail || 'error'));
                return;
            }
            const book = await uploadRes.json();

            const embedRes = await fetch('/admin/embed/' + book.id, {
                method: 'POST'
            });
            if (!embedRes.ok) {
                const err = await embedRes.json();
                alert('Embedding failed: ' + (err.detail || 'error'));
            } else {
                alert('Book uploaded and embedded successfully.');
            }
            uploadForm.reset();
            loadBooks();
        } catch (err) {
            console.error(err);
            alert('An error occurred.');
        }
    });

    loadBooks();
});