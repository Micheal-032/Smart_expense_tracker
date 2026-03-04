# 💰 Smart Personal Expense Tracker

A professional-grade, multi-user web application for tracking personal expenses with complete data isolation, smart insights, and beautiful UI.

![Tech Stack](https://img.shields.io/badge/Python-Flask-blue)
![Database](https://img.shields.io/badge/Database-SQLite-green)
![Frontend](https://img.shields.io/badge/Frontend-HTML%2FCSS%2FJS-orange)

## ✨ Features

### 🔐 Authentication System
- **User Registration** with email validation and password strength checking
- **Secure Login** with session-based authentication
- **Password Hashing** using PBKDF2-SHA256
- **Complete Data Isolation** - Each user can only access their own data

### 💸 Expense Management
- **Add Expenses** with date, amount, category, payment mode, and notes
- **Edit/Delete Expenses** with full CRUD operations
- **Quick-Add Feature** - Pre-fills last-used category for faster entry
- **Multiple Payment Modes** - Cash, UPI, Card tracking

### 📊 Dashboard & Analytics
- **Monthly Summary** - Total spending for current month
- **Today's Spending** - Real-time daily tracker
- **Top Category** - Highest spending category
- **Budget Status** - Visual progress bar with percentage
- **Category Breakdown** - Spending distribution across categories
- **Smart Insights** - Intelligent warnings and tips

### 📈 Reports
- **Monthly Reports** - Category-wise and payment mode analysis
- **Daily Reports** - Detailed transaction listing
- **Visual Progress Bars** - Easy-to-read spending breakdowns
- **Flexible Date Selection** - View any month or day

### 🏷️ Category Management
- **Default Categories** - Food, Transport, Rent, Shopping, Medical, Entertainment
- **Custom Categories** - Add your own expense categories
- **Usage Tracking** - See how many expenses use each category
- **Smart Deletion** - Prevents deleting categories with existing expenses

### 🎯 Smart Features
1. **Smart Expense Insights** - Warns when food spending exceeds 40% of total
2. **Budget Warnings** - Alert when reaching 80% of monthly budget
3. **Expense Reminders** - Notification if no expenses logged today
4. **Quick-Add** - Remembers last-used category via localStorage
5. **Auto Monthly Reset** - Stats automatically update each month while preserving history

### 🎨 Premium UI/UX
- **Modern Design** - Glassmorphism, gradients, and smooth animations
- **Dark Theme** - Eye-friendly color scheme
- **Mobile Responsive** - Works perfectly on all devices
- **Micro-Animations** - Smooth transitions and hover effects
- **Premium Typography** - Inter font family from Google Fonts

## 🛠️ Tech Stack

- **Backend**: Python 3.x + Flask 3.0
- **Database**: SQLite with user-isolated tables
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Authentication**: Flask sessions with secure cookies
- **Security**: Werkzeug password hashing (PBKDF2-SHA256)

## 📁 Project Structure

```
tracker/
├── app.py                      # Main Flask application with all API routes
├── database.py                 # Database schema and initialization
├── auth_utils.py              # Authentication utilities and decorators
├── run.py                     # Application launcher
├── requirements.txt           # Python dependencies
├── expense_tracker.db         # SQLite database (auto-generated)
├── static/
│   ├── css/
│   │   └── style.css         # Complete design system
│   └── js/
│       └── (future scripts)
└── templates/
    ├── login.html            # User login page
    ├── signup.html           # User registration
    ├── dashboard.html        # Main dashboard
    ├── expenses.html         # Expense management
    ├── reports.html          # Analytics & reports
    ├── categories.html       # Category management
    └── profile.html          # User profile & settings
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python run.py
```

The application will:
1. Initialize the SQLite database
2. Create all required tables
3. Generate sample data for testing
4. Start the development server on `http://localhost:5000`

### Step 3: Access the Application
Open your browser and navigate to:
```
http://localhost:5000
```

## 🔑 Demo Credentials

For testing, use the pre-created demo account:

- **Email**: `demo@expense.com`
- **Password**: `Password123`

The demo account comes with 50+ sample expenses across various categories.

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Categories Table
```sql
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, category_name)
);
```

### Expenses Table
```sql
CREATE TABLE expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_mode TEXT NOT NULL,
    note TEXT,
    expense_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);
```

### Budget Table
```sql
CREATE TABLE budget (
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    monthly_limit REAL NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, month, year)
);
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### Expenses
- `GET /api/expenses` - Get all user expenses
- `POST /api/expenses` - Add new expense
- `PUT /api/expenses/<id>` - Update expense
- `DELETE /api/expenses/<id>` - Delete expense

### Categories
- `GET /api/categories` - Get all user categories
- `POST /api/categories` - Add new category
- `DELETE /api/categories/<id>` - Delete category

### Dashboard
- `GET /api/dashboard/summary` - Get dashboard statistics
- `GET /api/dashboard/trends` - Get expense trends

### Reports
- `GET /api/reports/monthly?month=YYYY-MM` - Monthly report
- `GET /api/reports/daily?date=YYYY-MM-DD` - Daily report

### Budget
- `GET /api/budget` - Get current budget
- `POST /api/budget` - Set monthly budget

## 🔒 Security Features

1. **Password Hashing** - Using Werkzeug's PBKDF2-SHA256
2. **Session Management** - Secure Flask sessions with HTTPOnly cookies
3. **Data Isolation** - All queries filter by `user_id` from session
4. **SQL Injection Prevention** - Parameterized queries throughout
5. **Email Uniqueness** - Database constraint + validation
6. **Login Required** - Decorator protects all authenticated routes

## 💡 Usage Guide

### 1. Sign Up
1. Click "Sign Up" on login page
2. Enter name, email, and password (min 8 chars with letters and numbers)
3. Click "Create Account"

### 2. Add Expenses
1. Navigate to "Expenses" page
2. Fill in date, amount, category, payment mode, and optional note
3. Click "Add Expense"
4. The form remembers your last-used category for quick entry

### 3. View Dashboard
- See monthly total, today's spending, top category, and budget status
- View category breakdown with progress bars
- Check smart insights for spending tips

### 4. Generate Reports
1. Go to "Reports" page
2. Choose "Monthly" or "Daily" report
3. Select date range
4. View category-wise and payment mode breakdowns

### 5. Manage Categories
- Add custom categories on "Categories" page
- Delete unused categories (only those with 0 expenses)

### 6. Set Budget
1. Navigate to "Profile" page
2. Enter monthly budget limit
3. Click "Update Budget"
4. Dashboard will show warnings at 80% usage

## 🎯 Use Cases

✅ College mini project  
✅ Resume portfolio project  
✅ Personal finance tracking  
✅ Hackathon submission  
✅ Learning full-stack development  
✅ Python Flask tutorial project  

## 🚢 Deployment

### Local Development
Already configured! Just run `python run.py`

### Production Deployment
For production, consider:
1. Using PostgreSQL instead of SQLite
2. Setting `app.debug = False`
3. Using a production WSGI server like Gunicorn
4. Setting a strong `SECRET_KEY` via environment variable
5. Enabling HTTPS
6. Using a reverse proxy like Nginx

## 📝 Future Enhancements

- [ ] Export reports to PDF/CSV
- [ ] Recurring expenses
- [ ] Multi-currency support
- [ ] Income tracking
- [ ] Advanced charts (Chart.js integration)
- [ ] Email notifications
- [ ] Mobile app (React Native)
- [ ] Expense categories with icons

## 🤝 Contributing

This is a beginner-friendly project! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📄 License

This project is open source and available for educational purposes.

## 👨‍💻 Author

Built with ❤️ using Flask, SQLite, and modern web technologies.

---

**Made for developers who want a clean, professional expense tracking solution!**
