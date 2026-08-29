# RecoverAI — AI Payment Recovery Agent

RecoverAI is an AI-powered payment recovery system that analyzes failed payment transactions and recommends suitable recovery actions.

## Features

* Payment recovery probability prediction
* XGBoost-based machine learning model
* Customer payment history analysis
* AI-assisted recovery decisions
* Recovery action recommendations
* Automated customer messaging
* SQLite database integration
* Razorpay TEST payment integration
* Razorpay webhook support
* Streamlit interactive dashboard
* FastAPI backend

## Tech Stack

* Python
* Pandas
* NumPy
* Scikit-learn
* XGBoost
* Joblib
* Streamlit
* FastAPI
* SQLite
* Razorpay
* Google Gemini

## Project Structure

```text
RecoverAI/
│
├── app.py
├── api.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Machine Learning Model

RecoverAI uses an XGBoost classification model to predict the probability of recovering a failed payment.

The model uses features such as:

* Transaction amount
* Payment method
* Failure reason
* Previous successful payments
* Previous failed payments
* Customer age
* Previous recovery attempts
* Transaction hour

## Streamlit Application

The Streamlit interface provides an interactive way to enter payment information and view the recovery prediction and recommended action.

Run the application with:

```bash
streamlit run app.py
```

## FastAPI Backend

RecoverAI also provides a FastAPI backend for payment recovery and Razorpay webhook integration.

Run the API with:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check

```text
GET /health
```

### Payment Recovery

```text
POST /recover
```

### Razorpay Webhook

```text
POST /razorpay/webhook
```

## Razorpay Integration

The project uses Razorpay TEST mode for payment and webhook testing.

The webhook integration updates the RecoverAI database based on payment events such as successful or failed payments.

## Security

Sensitive information such as API keys, Razorpay credentials, webhook secrets, ngrok tokens, passwords, databases, and trained model files should not be uploaded to GitHub.

Use environment variables or secure secret management for sensitive credentials.

## Project Status

RecoverAI is a prototype AI payment recovery system developed for educational and project demonstration purposes.
