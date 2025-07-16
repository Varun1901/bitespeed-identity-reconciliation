# 🛠️ Bitespeed Identity Reconciliation API

This is a **FastAPI + SQLite** implementation of the [Bitespeed Backend Task](https://bitespeed.notion.site/).  
It reconciles a customer's identity across multiple purchases based on email & phone number.

---

## 🚀 Hosted API

- **Base URL:** `https://<your-render-url>`  
- **Endpoints:**
  - `POST /identify` → Identify & link customer contacts
  - `GET /contacts` → Debug endpoint showing all stored contacts
  - `GET /docs` → Swagger UI to test APIs

---

## ✅ API Usage

### 1️⃣ Identify a Contact

**POST** `/identify`

#### Request Body (JSON)
```json
{
  "email": "lorraine@hillvalley.edu",
  "phoneNumber": "123456"
}
```

#### Example Response
```json
{
  "contact": {
    "primaryContatctId": 1,
    "emails": ["lorraine@hillvalley.edu"],
    "phoneNumbers": ["123456"],
    "secondaryContactIds": []
  }
}
```

---

### 2️⃣ Debug All Contacts

**GET** `/contacts`  
Lists all rows in the database.

---

## 🛠️ Tech Stack

- **FastAPI** → Backend framework  
- **SQLite + SQLAlchemy** → Database  
- **Uvicorn** → ASGI server  
- **Render.com** → Hosting (free tier)

---

## 🖥️ Run Locally

### 1️⃣ Clone this repo
```bash
git clone https://github.com/<your-username>/bitespeed-identity-reconciliation.git
cd bitespeed-identity-reconciliation
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Run the server
```bash
uvicorn main:app --reload
```

### 4️⃣ Open in browser
- Swagger Docs → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
- Debug Contacts → [http://127.0.0.1:8000/contacts](http://127.0.0.1:8000/contacts)

---

## ✅ Test Cases

### Case 1: New Primary
```json
{
  "email": "lorraine@hillvalley.edu",
  "phoneNumber": "123456"
}
```

### Case 2: Same Phone, New Email → Creates Secondary
```json
{
  "email": "mcfly@hillvalley.edu",
  "phoneNumber": "123456"
}
```

### Case 3: New Primary
```json
{
  "email": "biffsucks@hillvalley.edu",
  "phoneNumber": "717171"
}
```

### Case 4: Merge Primaries
```json
{
  "email": "lorraine@hillvalley.edu",
  "phoneNumber": "717171"
}
```

---

## 📜 License

MIT
