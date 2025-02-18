Open a terminal or command prompt and navigate to your local Git repository.
cd path/to/your/repo


Before creating a new branch, ensure you’re currently on the main branch (or the branch from which you want to create the new branch).
git checkout main


It's a good practice to pull the latest changes from the remote main branch to ensure you're working with the most up-to-date code.
git pull origin main


Now that you're on the main branch and have the latest changes, you can create a new branch. Use the following command, replacing new-branch-name with your desired branch name.
git checkout -b new-branch-name


To confirm that the new branch has been created and that you’re on it, you can use the following command:
git branch


If you want to push your new branch to GitHub, use this command:
git push -u origin new-branch-name


to run the the project file:
cd chatbot_platform


Run the server:
python manage.py runserver
