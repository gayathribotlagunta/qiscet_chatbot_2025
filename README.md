# qiscet_chatbot_2025
Chatbot Project
A simple, AI-powered chatbot deployed as a containerized web service on Google Cloud Run. This project demonstrates how to build a basic chatbot using Python and deploy it on a scalable, serverless platform.

🚀 Features:
Natural Language Interaction: Communicates with users in a conversational manner.

Scalable: Deployed on Google Cloud Run, allowing it to scale automatically to handle traffic.

Containerized: Packaged as a Docker image for consistent and portable deployment.

Cost-Effective: Pay-per-use model on Cloud Run ensures you only pay for what you use.

🛠️ Technologies Used:
Python: The core language for the chatbot logic.

Flask: A micro-framework used to create the web application.

Google Cloud Run: The fully managed, serverless platform for deployment.

Docker: Used to containerize the application for easy deployment.

Google Cloud Artifact Registry: Used to store the Docker image.

📦 Project Structure:
my_chatbot/
├── bot.py             # The main chatbot application file
├── requirements.txt   # Lists all Python dependencies
├── Dockerfile         # The blueprint for building the Docker image
└── templates/
    └── index.html     # The HTML page for the chatbot's UI
