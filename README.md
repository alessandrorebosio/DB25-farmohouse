# 🏡 Farmhouse - Agritourism Management System
10906 - Academic Year 2024/25, Bachelor's Degree in Computer Science and Engineering, University of Bologna - Cesena Campus

Instructors: Annalisa Franco    
Programming Language: Python

# 📝 Overview
This project implements a comprehensive database system for managing an agritourism facility. The system handles:
- 🛏️ Guest reservations
- 🚜 Activity bookings
- ⭐ Reviews and feedback system
- 👥 Staff administration tools
- 📊 Real-time availability tracking

## ✅ Requirements
- **Python**: 3.10 or higher
- **MySQL Server**: 8.0 or higher
- **pip**: Python package installer
- **MySQL client**: Command line tool (`mysql`)

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/alessandrorebosio/DB25-farmhouse.git
cd DB25-farmhouse
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate     # macOS/Linux
# venv\Scripts\activate      # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
**Create MySQL Database:**
```bash
mysql -u root -p < src/resources/db.sql
mysql -u root -p < src/resources/demo.sql
```

## 🚀 Running the Application

### Start Development Server
```bash
python src/main/manage.py runserver
```

The application will be available at: **[http://localhost:8000](http://localhost:8000)**

## 📦 Dependencies
The project uses the following main dependencies (see `requirements.txt`):
- **Django 5.2.4**: Web framework
- **mysqlclient 2.2.7**: MySQL database adapter
- **asgiref 3.9.1**: ASGI utilities
- **sqlparse 0.5.3**: SQL parsing library

## 👥 Team Members

### Alessandro Rebosio
- **GitHub**: [@alessandrorebosio](https://github.com/alessandrorebosio)
- **Email**: [alessandro.rebosio@studio.unibo.it](mailto:alessandro.rebosio@studio.unibo.it)

### Filippo Ricciotti
- **GitHub**: [@Riccio-15](https://github.com/Riccio-15)
- **Email**: [filippo.ricciotti@studio.unibo.it](mailto:filippo.ricciotti@studio.unibo.it)
