1. How To Run (requirement python 3.10+
git clone
cd SEEK - Techical Assessment

python -m venv .venv
source .venv/Script/activate

pip install -r requirement.txt

uvicorn app.main:app --reload

2. Design Overview
HTTP request -> endpoint -> service -> crud -> store -> store -> crud -> service -> endpoint -> HTTP Response

3. Assumption
- no authentication
- no frontend
- in-memory storage
- ids 32 characters with hex strings
- timestamp is timezone
- status is boolean, not string
- job created with open/true status
- job cannot be reopened after being closed
- delete job and application is not applied
- get list of jobs with no status considered get list both status
- there is no check for duplicates if the same email applied the same application

4. What I Would Improve with more time
- I will replace the in-memory storage with Postgres by using SQLAlchemy since I am familiar with the database
- Implement duplicate checks for apply application
- Both the application and job get_lists need to have 3 attributes of pagination, which are offset, limit, and page_number
- Add a status for the application if the application has been reviewed, submitted, rejected, or offered
