# 🏫 Outing & Leave Management System

A web-based Student Management System built with **Python Flask** and **SQLite** for managing hostel outings and college leave requests.

---

## 📌 Features

### 🎓 Student Portal
- Register and Login securely
- Apply for **Hostel Outing** with destination, reason, and time
- Apply for **College Leave** with dates, type, and reason
- View status of all requests (Pending / Approved / Rejected)
- 🔔 In-app notifications when request is Approved or Rejected

### 🛡️ Admin Dashboard
- View all outing and leave requests from students
- Approve or Reject requests with one click
- 🔔 In-app notifications when a new request is submitted

---

## 🛠️ Tech Stack

| Technology | Usage |
|---|---|
| Python 3 | Backend logic |
| Flask | Web framework |
| SQLite | Database |
| HTML + CSS | Frontend |
| Jinja2 | Template engine |

---

## 📁 Project Structure
```
outing-leave-management/
├── app.py                  ← Main Flask application
├── database.db             ← SQLite database (auto-created)
├── templates/
│   ├── login.html          ← Login page
│   ├── register.html       ← Student registration
│   ├── dashboard.html      ← Student dashboard
│   ├── outing_form.html    ← Outing request form
│   ├── leave_form.html     ← Leave request form
│   └── admin.html          ← Admin dashboard
└── static/
    └── style.css           ← Stylesheet
```

---

## 🚀 How to Run

### 1. Clone the repository
```bash
git clone https://github.com/dishanthreddy2006-del/outing-leave-management.git
cd outing-leave-management
```

### 2. Install dependencies
```bash
pip install flask
```

### 3. Run the app
```bash
python3 app.py
```

### 4. Open in browser
```
http://127.0.0.1:5000
```

---

## 🔐 Default Admin Credentials

| Field | Value |
|---|---|
| Roll No | admin |
| Password | admin123 |

---

## 📸 Modules

- **Login & Register** — Secure student authentication
- **Outing Management** — Apply and track hostel outing requests
- **Leave Management** — Apply and track college leave requests
- **Admin Panel** — Manage and respond to all requests
- **Notifications** — Real-time in-app alerts for both students and admin

---

## 👨‍💻 Author

**C Dishanth Reddy**  
B.E Computer Science Engineering  
NIE Mysuru  
GitHub: [@dishanthreddy2006-del](https://github.com/dishanthreddy2006-del)

---

## 📄 License

This project is open source and available for educational purposes.
