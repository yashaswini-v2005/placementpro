# 🚀 PlacementPro – The Integrated Campus Career Suite

PlacementPro is a role-based web application designed to automate and modernize campus placement management.  
It replaces manual Excel sheets and WhatsApp notifications with a structured, intelligent, and scalable system.

---

## 🎯 Problem Statement

Campus placements are often managed using:
- Excel sheets for eligibility filtering
- WhatsApp groups for announcements
- Manual tracking for applications and interviews

This leads to:
- Errors in eligibility filtering
- Information overload
- Lack of transparency
- No structured analytics

PlacementPro solves these problems using automation and intelligent workflows.

---

## 🏗 System Architecture

Browser  
⬇  
Flask Backend (Controller)  
⬇  
Business Logic Modules  
⬇  
SQLite Database  
⬇  
Dynamic Role-Based Dashboards  

---

## 👥 User Roles

### 🏢 TPO (Training & Placement Officer)
- Create placement drives
- Set eligibility criteria (CGPA, backlogs, branch)
- Automatic eligible student filtering
- Interview scheduling (conflict prevention)
- Application status updates
- Placement analytics dashboard

---

### 🎓 Student
- Personalized eligible drive feed
- Resume Wizard (auto-generate PDF)
- Application tracking
- Skill Gap Analysis
- Resume Quality Score
- Notifications & PlacementBot

---

### 👨‍💼 Alumni
- Post job referrals
- Approve or reject referral requests
- Add mentorship slots
- Accept mentorship requests
- Connect with students

---

## 🤖 Key Features

- 🔥 Automated Criteria Engine
- 📄 Dynamic Resume Generator (PDF)
- 📊 Skill Gap Analysis
- 📈 Resume Quality Scoring API
- 📢 Real-time Notification System
- 📅 Interview Scheduling with Conflict Detection
- 🤝 Alumni Referral & Mentorship Integration
- 💬 PlacementBot (Query Assistance)

---

## 🛠 Tech Stack

- Backend: Flask (Python)
- Database: SQLite
- Frontend: HTML, CSS, JavaScript (Jinja Templates)
- PDF Engine: ReportLab
- Deployment: Render (Cloud Hosting)
- Server: Gunicorn

---

## ⚙️ Installation (Local Setup)

1. Clone the repository:
