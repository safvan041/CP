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
- PostgreSQL (for production)
- Google Cloud SDK (optional, for deployment)

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

------------------------------
▶️ Run the Project Locally
------------------------------

-> cd chatbot_platform
-> Activate or chnage USE_CLOUD_DB = False
-> python manage.py migrate
-> python manage.py runserver

Visit http://127.0.0.1:8000 in your browser.

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
☁️ Deployment on Google Cloud
------------------------------

This app supports deployment on Google Cloud Run using Cloud Build.
Make Sure To Use Your Own Cloud SQL, Instance, And Other Things...(Check Cloudbuild File To Get An Idea About That).
It integrates with:

- Cloud SQL for database
- Cloud Storage for file uploads

To deploy:

gcloud builds submit --config cloudbuild.yaml

------------------------------
📬 Contact
------------------------------

For licensing or collaboration or if you get stuck with anything in the app, contact:

Email: safwanbakkar.dev@hotmail.com  
GitHub: https://github.com/safvan041
