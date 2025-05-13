these is the code deployed on APP RUNNER AWS
clone the repo using https://github.com/amal-lahchim-ofoundation/app.git
🔧 Local Setup Instructions
1.  Create and activate a virtual environment:
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
2. 📦 Install dependencies:

pip install -r requirements.txt

3. 🛠️ Add your .env file with the following:

OPENAI_API_KEY=sk-...
FIREBASE_DATABASE_URL=https://your-app.firebaseio.com/
MY_SECRET_API_KEY=...
GG_PROJECT_ID=your-google-project-id
GG_TOPIC_ID=audio-transcriptions
GG_SUBSCRIPTION_ID=...
PUBSUB_KEY_B64=base64_of_your_service_account_key.json
🚀 Running the App

python python.py



