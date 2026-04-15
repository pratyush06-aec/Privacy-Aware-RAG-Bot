import os
from flask import Flask, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from openfga_sdk import OpenFgaClient

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")

fga_client = OpenFgaClient(
    api_url=os.getenv("FGA_API_URL"),
    store_id=os.getenv("FGA_STORE_ID"),
    authorization_model_id=os.getenv("FGA_MODEL_ID"),
    client_id=os.getenv("FGA_CLIENT_ID"),
    client_secret=os.getenv("FGA_CLIENT_SECRET")
)

oauth = OAuth(app)

auth0 = oauth.register(
    "auth0",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f'https://{os.getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

documents = [
    {
        "id": "salary_data",
        "text": "Confidential: The salary structure for employees varies by role. Managers earn between $80,000 and $120,000 annually, while engineers earn between $60,000 and $100,000. Bonuses are performance-based."
    },
    {
        "id": "company_policy",
        "text": "All employees must adhere to company policies including attendance, code of conduct, and data security. Violations may result in disciplinary action."
    },
    {
        "id": "budget_q4",
        "text": "The Q4 budget allocation includes $1 million for operations, $500,000 for marketing, and $300,000 for research and development."
    },
    {
        "id": "hr_guidelines",
        "text": "HR guidelines include onboarding procedures, leave policies, and employee grievance handling mechanisms. All HR records must remain confidential."
    },
    {
        "id": "engineering_roadmap",
        "text": "The engineering roadmap focuses on scaling backend systems, improving API performance, and migrating services to a microservices architecture."
    },
    {
        "id": "legal_contracts",
        "text": "Legal contracts include vendor agreements, employee NDAs, and compliance documents. Access is restricted to legal and executive teams."
    },
    {
        "id": "marketing_strategy",
        "text": "The marketing strategy for the next quarter includes digital campaigns, influencer partnerships, and regional brand expansion."
    },
    {
        "id": "sales_report",
        "text": "The sales report shows a 15% increase in revenue compared to last quarter, driven by new enterprise clients and improved retention."
    }
]

def check_access(user, document):
    try:
        response = fga_client.check(
            user=f"user:{user}",
            relation="viewer",
            object=f"document:{document}"
        )
        return response["allowed"]
    except Exception as e:
        print("FGA Error:", e)
        return False
    
def get_allowed_docs(user):
    allowed_docs = []

    for doc in documents:
        if check_access(user, doc["id"]):
            allowed_docs.append(doc)

    return allowed_docs

def rag_query(user, query):
    allowed_docs = get_allowed_docs(user)

    if not allowed_docs:
        return "❌ No access to any documents."

    context = " ".join([doc["text"] for doc in allowed_docs])

    # Simple mock LLM
    return f"Answer based on accessible data:\n{context}"
    
# Home route
@app.route("/")
def home():
    user = session.get("user")
    return f"Hello {user['name']}" if user else "Not logged in ❌"

# Login route
@app.route("/login")
def login():
    return auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

# Callback route
@app.route("/callback")
def callback():
    token = auth0.authorize_access_token()
    session["user"] = token["userinfo"]
    return redirect("/")

# Logout route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        f"https://{os.getenv('AUTH0_DOMAIN')}/v2/logout?"
        f"returnTo=http://localhost:5000&client_id={os.getenv('AUTH0_CLIENT_ID')}"
    )

if __name__ == "__main__":
    app.run(debug=True)