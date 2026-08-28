---------------
🧠 CAPI Studio
--------------

A Django-based chatbot platform allowing users to upload knowledge base files, generate vector embeddings, and interact with AI-powered chat widgets.


------------
Note:
------------

If you are using this repo from 07-07-2025 to {present date}, make sure to use your own models and DBs. 

------------------------------
📄 License
------------------------------

This project is under a custom proprietary license.  
Please see the LICENSE file for complete terms, including rules on usage, confidentiality, and future commercial rights.

------------------------------
🚀 Getting Started
------------------------------

🛠️ Prerequisites:
- Python 3.10+
- pip
- Git
- SQLite (included with Python)

------------------------------
🧭 Clone the Repository
------------------------------

git clone https://github.com/safvan041/CP.git
cd chatbot-platform

------------------------------
🛠️ Project Setup
------------------------------

🔀 Create a New Branch:

#do not push anything on main#

# Step 1: Ensure you're on latest branch
git checkout fix-deploy

# Step 2: Pull the latest updates
git pull origin fix-deploy

# Step 3: Create a new feature branch
git checkout -b your-feature-branch-name

# Step 4: Confirm current branch
git branch

# Step 5: Push to GitHub
git push -u origin your-feature-branch-name

▶️ Run the Project Locally


Visit http://127.0.0.1:8000 in your browser.

------------------------------
📚 Document Processing
------------------------------

Knowledge-base uploads support `.txt`, `.pdf`, and `.docx` files up to 50 MB. The `.doc` extension is accepted by the form but is not currently readable by the document parser; convert legacy Word files to `.docx` first.

Processing is started from the dashboard after upload:

1. Upload the document.
2. Select the processing/embed action for that knowledge base.
3. Wait for the status to change from `processing` to `completed`.

The processor reads text incrementally instead of loading a complete 50 MB document into one embedding request. Text is split into 4,000-character chunks with 400 characters of overlap. Embeddings are sent to the NVIDIA API in batches of eight, and each chunk is stored in the local FAISS index. This supports 1,000+ page text-based PDFs and DOCX files, subject to available disk space, memory, API limits, and processing time.

Vector files are stored locally in `chatbot_platform/faiss_data/kb_<id>/`. Ensure this directory is writable and is persisted between deployments; otherwise uploaded knowledge bases must be embedded again after a redeployment. Processing is synchronous, so large documents can take several minutes and the browser should remain connected until it finishes.

Scanned PDFs without an embedded text layer produce little or no usable content. Run OCR on those files before uploading. If processing fails, inspect the knowledge-base error message and application logs, then retry after correcting the document or API configuration.

------------------------------
📁 Example Folder Structure (it is diffrent that orignal, cross check it once)
------------------------------

chatbot_platform/
├── core/                # DB models, embeddings, utils
├── webapp/              # Views, forms, URLs
├── statics/             # CSS, JS, Images
├── templates/           # HTML files
├── media/               # Uploaded files
├── manage.py
├── requirements.txt
└── README.txt


------------------------------
📬 Contact
------------------------------

For licensing or collaboration or if you get stuch with anything in the app, contact:

Email: safwanbakkar.dev@hotmail.com  
GitHub: https://github.com/safvan041
