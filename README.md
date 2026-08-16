# LinkPlease – Automation API

LinkPlease is a backend automation service built with **FastAPI** and **MongoDB**.

It receives webhook events, matches them against user-defined keyword rules, creates direct-message jobs, processes those jobs through the PseudoGram API, and tracks delivery status and statistics.

## 🚀 Features

- Create keyword-based automation rules
- Receive and validate webhook events
- HMAC-SHA256 webhook signature verification
- Store events and rules in MongoDB
- Create DM jobs for matching events
- Retry failed DM jobs
- Track job status and attempts
- Prevent duplicate processing
- Check PseudoGram DM delivery status
- View automation statistics
- Swagger API documentation
- MongoDB Atlas support for deployment

## 🛠️ Tech Stack

- **Python 3.11**
- **FastAPI**
- **Uvicorn**
- **MongoDB**
- **PyMongo**
- **HTTPX**
- **python-dotenv**
- **MongoDB Atlas**
- **PseudoGram API**

## 📁 Project Structure

```text
LinkPlease/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── pseudogram.py
│   ├── rules.py
│   ├── stats.py
│   ├── webhook.py
│   └── worker.py
│
├── .env
├── .gitignore
├── FAILURES.md
├── README.md
├── requirements.txt
└── test_webhook.py

pip install -r requirements.txt

py -3.11 -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install fastapi uvicorn pymongo httpx python-dotenv

----

python -m pip install --no-cache-dir fastapi uvicorn pymongo httpx python-dotenv

python -m pip install --no-cache-dir fastapi uvicorn pymongo httpx python-dotenv

uvicorn app.main:app --reload

