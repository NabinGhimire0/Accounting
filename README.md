# Tally-like Accounting Application Documentation

**Version:** 1.0  
**Author:** *Unknown*  
**Date:** *[2025/2/22]*

---

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Running the Application](#running-the-application)
5. [Code Structure and Explanation](#code-structure-and-explanation)  
   5.1 [Database Models](#database-models)  
   &nbsp;&nbsp;&nbsp;&nbsp;a. [User Model](#user-model)  
   &nbsp;&nbsp;&nbsp;&nbsp;b. [Account Model](#account-model)  
   &nbsp;&nbsp;&nbsp;&nbsp;c. [JournalEntry Model](#journalentry-model)  
   &nbsp;&nbsp;&nbsp;&nbsp;d. [TransactionDetail Model](#transactiondetail-model)  
   &nbsp;&nbsp;&nbsp;&nbsp;e. [AuditLog Model](#auditlog-model)  
   &nbsp;&nbsp;&nbsp;&nbsp;f. [Stock Model](#stock-model)  
   5.2 [PDF Generation Function](#pdf-generation-function)  
   5.3 [Login/Registration Window](#loginregistration-window)  
   5.4 [Main Application (TallyApp)](#main-application-tallyapp)  
   &nbsp;&nbsp;&nbsp;&nbsp;a. [Navigation Panel](#navigation-panel)  
   &nbsp;&nbsp;&nbsp;&nbsp;b. [Dashboard Screen](#dashboard-screen)  
   &nbsp;&nbsp;&nbsp;&nbsp;c. [Masters (Accounts) Screen](#masters-accounts-screen)  
   &nbsp;&nbsp;&nbsp;&nbsp;d. [Voucher Entry Screen](#voucher-entry-screen)  
   &nbsp;&nbsp;&nbsp;&nbsp;e. [Stock Management Screen](#stock-management-screen)  
   &nbsp;&nbsp;&nbsp;&nbsp;f. [Ledger Screen](#ledger-screen)  
   &nbsp;&nbsp;&nbsp;&nbsp;g. [Reports Screen](#reports-screen)  
   &nbsp;&nbsp;&nbsp;&nbsp;h. [Audit Logs Screen](#audit-logs-screen)  
6. [Demonstration and Sample Data](#demonstration-and-sample-data)
7. [Future Enhancements](#future-enhancements)
8. [Conclusion](#conclusion)

---

## 1. Overview

This Tally-like Accounting Application is a comprehensive desktop solution built with Python's Tkinter (for the GUI) and SQLAlchemy (for database management using SQLite). It simulates a full-featured accounting system supporting multiple voucher types (Journal, Payment, Receipt, Contra, Debit Note, Credit Note), a wide range of account types (Assets, Liabilities, Equity, Revenue, Expense, Stock), stock management, ledger viewing, and detailed reports. It even handles adjustments such as discounts, depreciation, and bad debt. The Profit & Loss (Income Statement) report calculates net profit or net loss and adds a balancing line (e.g., "Net Profit c/d" or "Net Loss c/d").

---

## 2. System Requirements

- **Python 3.x**
- **Tkinter** (included with standard Python installations)
- **SQLAlchemy**  
  Install via: `pip install SQLAlchemy`
- **ReportLab** (for PDF generation)  
  Install via: `pip install reportlab`
- **Werkzeug** (for password hashing)  
  Install via: `pip install werkzeug`
- Operating system: Windows, macOS, or Linux

---

## 3. Installation

1. **Download the Code:**  
   Save the code file as `tally_printable_app_with_pdf_print_adjusted.py` (or your chosen name).

2. **(Optional) Create a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install SQLAlchemy reportlab werkzeug
   ```

---

## 4. Running the Application

To start the application, open a terminal, navigate to the directory containing your script, and run:
```bash
python tally_printable_app_with_pdf_print_adjusted.py
```
A login window will appear. You can register a new user or log in with an existing account to access the main application.

---

## 5. Code Structure and Explanation

### 5.1 Database Models

The application uses SQLAlchemy to define its data structure. Each model represents a table in the SQLite database.

#### a. User Model
Stores user credentials for login.
```python
class User(Base):
    __tablename__ = 'users'
    id       = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
```
*Explanation:*  
- `id`: Unique identifier.  
- `username`: Must be unique for each user.  
- `password`: Stores the hashed password.

#### b. Account Model
Holds all account information (Cash, Bank, Sales Revenue, etc.).
```python
class Account(Base):
    __tablename__ = 'accounts'
    id      = Column(Integer, primary_key=True)
    name    = Column(String(100), nullable=False)
    type    = Column(String(50), nullable=False)  # e.g., Asset, Liability, Equity, Revenue, Expense, Stock
    balance = Column(Float, default=0.0)
```
*Explanation:*  
- `name`: The name of the account.  
- `type`: Defines the category (used later for reports).  
- `balance`: Updated with each transaction.

#### c. JournalEntry Model
Represents a voucher entry.
```python
class JournalEntry(Base):
    __tablename__ = 'journal_entries'
    id           = Column(Integer, primary_key=True)
    date         = Column(DateTime, default=datetime.utcnow)
    description  = Column(String(200))
    voucher_type = Column(String(50), default="Journal")
    transactions = relationship('TransactionDetail', back_populates='journal_entry')
```
*Explanation:*  
- `date`: Automatically set when the voucher is created.  
- `voucher_type`: Can be Journal, Payment, Receipt, etc.  
- `transactions`: Links to all line items in the voucher.

#### d. TransactionDetail Model
Contains each line of a voucher.
```python
class TransactionDetail(Base):
    __tablename__ = 'transaction_details'
    id               = Column(Integer, primary_key=True)
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'))
    account_id       = Column(Integer, ForeignKey('accounts.id'))
    amount           = Column(Float, nullable=False)
    type             = Column(String(10), nullable=False)  # "debit" or "credit"
    journal_entry    = relationship('JournalEntry', back_populates='transactions')
```
*Explanation:*  
- Links a transaction to its journal entry and the affected account.  
- `amount` and `type` (debit/credit) determine the effect on the account’s balance.

#### e. AuditLog Model
Tracks all significant actions.
```python
class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id        = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action    = Column(String(100))
    details   = Column(String(500))
```
*Explanation:*  
Each log entry records what happened (action) and additional details.

#### f. Stock Model
Manages inventory items.
```python
class Stock(Base):
    __tablename__ = 'stocks'
    id             = Column(Integer, primary_key=True)
    product_name   = Column(String(100), nullable=False)
    quantity       = Column(Integer, default=0)
    purchase_price = Column(Float, default=0.0)
    selling_price  = Column(Float, default=0.0)
    details        = Column(Text)
```
*Explanation:*  
Stores details about each product including quantity and pricing.

---

### 5.2 PDF Generation Function

Generates a PDF from a text report.
```python
def save_report_as_pdf(report_text, file_path):
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter
    lines = report_text.splitlines()
    y = height - 50
    for line in lines:
        c.drawString(50, y, line)
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()
```
*Explanation:*  
- Splits the report text into lines and writes them onto a PDF canvas.
- Handles page breaks when the page fills up.

---

### 5.3 Login/Registration Window

Provides a simple GUI for user login and registration.
```python
class LoginWindow:
    def __init__(self, master):
        self.master = master
        master.title("Login - Tally-like Accounting")
        master.geometry("300x150")
        tk.Label(master, text="Username").pack(pady=2)
        self.entry_username = tk.Entry(master)
        self.entry_username.pack(pady=2)
        tk.Label(master, text="Password").pack(pady=2)
        self.entry_password = tk.Entry(master, show="*")
        self.entry_password.pack(pady=2)
        btn_frame = tk.Frame(master)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Login", width=10, command=self.login).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Register", width=10, command=self.register).pack(side='left', padx=5)
```
*Explanation:*  
- Presents two fields for username and password.
- On successful login, it launches the main application.

---

### 5.4 Main Application (TallyApp)

The core of the application; it creates the main window with a navigation panel.

#### a. Navigation Panel
```python
self.nav_frame = tk.Frame(master, width=200, bg='lightgray')
self.nav_frame.pack(side='left', fill='y')
btn_config = {'width': 20, 'padx': 5, 'pady': 5, 'anchor': 'w'}
tk.Button(self.nav_frame, text="Dashboard", command=self.show_dashboard, **btn_config).pack(fill='x')
# ... other buttons for Masters, Voucher Entry, etc.
```
*Explanation:*  
- Provides buttons on the left side to navigate between different screens (Dashboard, Masters, Voucher Entry, Stock, Ledger, Reports, Audit Logs).

#### b. Dashboard Screen
```python
def show_dashboard(self):
    self.clear_content()
    tk.Label(self.content_frame, text="Dashboard", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
    total_accounts = session.query(Account).count()
    total_vouchers = session.query(JournalEntry).count()
    total_stock = session.query(Stock).count()
    last_entry = session.query(JournalEntry).order_by(JournalEntry.date.desc()).first()
    summary = f"Total Accounts: {total_accounts}\nTotal Vouchers: {total_vouchers}\nTotal Stock Items: {total_stock}\n"
    if last_entry:
        summary += f"Last Voucher: {last_entry.description} ({last_entry.voucher_type}) on {last_entry.date.strftime('%Y-%m-%d %H:%M:%S')}"
    else:
        summary += "No vouchers recorded yet."
    tk.Label(self.content_frame, text=summary, font=('Arial', 12), bg='white').pack(pady=20)
```
*Explanation:*  
- Displays summary information retrieved from the database.

#### c. Masters (Accounts) Screen
Includes adding and deleting accounts.
```python
def show_accounts_master(self):
    self.clear_content()
    tk.Label(self.content_frame, text="Accounts Master", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
    # Treeview for displaying accounts:
    self.accounts_tree = ttk.Treeview(tree_frame, columns=("ID", "Name", "Type", "Balance"), show="headings")
    # ... Code to add headings and load data ...
    # Form for adding new accounts:
    tk.Label(btn_frame, text="Name:", bg='white').grid(row=0, column=0, padx=5, pady=2)
    self.entry_account_name = tk.Entry(btn_frame)
    self.entry_account_name.grid(row=0, column=1, padx=5, pady=2)
    tk.Label(btn_frame, text="Type:", bg='white').grid(row=0, column=2, padx=5, pady=2)
    self.combo_account_type = ttk.Combobox(btn_frame, values=["Asset", "Liability", "Equity", "Revenue", "Expense", "Stock"])
    self.combo_account_type.grid(row=0, column=3, padx=5, pady=2)
    tk.Button(btn_frame, text="Add Account", command=self.add_account).grid(row=0, column=4, padx=5, pady=2)
    tk.Button(btn_frame, text="Delete Account", command=self.delete_account).grid(row=0, column=5, padx=5, pady=2)
```
*Explanation:*  
- Displays existing accounts.
- Provides form inputs to add a new account and a delete button to remove a selected account.

#### d. Voucher Entry Screen
Allows entry of vouchers with multiple transaction lines.
```python
def show_voucher_entry(self):
    self.clear_content()
    tk.Label(self.content_frame, text="Voucher Entry", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
    # Form to choose voucher type and description:
    tk.Label(form_frame, text="Voucher Type:", bg='white').grid(row=0, column=0, padx=5, pady=2)
    self.combo_voucher_type = ttk.Combobox(form_frame, values=["Journal", "Payment", "Receipt", "Contra", "Debit Note", "Credit Note"])
    self.combo_voucher_type.current(0)
    self.combo_voucher_type.grid(row=0, column=1, padx=5, pady=2)
    tk.Label(form_frame, text="Description:", bg='white').grid(row=0, column=2, padx=5, pady=2)
    self.entry_voucher_desc = tk.Entry(form_frame, width=50)
    self.entry_voucher_desc.grid(row=0, column=3, padx=5, pady=2)
```
*Explanation:*  
- Sets up voucher header details and a dynamic section to add multiple transaction rows.

#### e. Stock Management Screen
Manage inventory items.
```python
def show_stock_management(self):
    self.clear_content()
    tk.Label(self.content_frame, text="Stock Management", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
    # Treeview to list stock items and a form to add new items.
```
*Explanation:*  
- Users can add stock items with details like product name, quantity, and pricing.
  
#### f. Ledger Screen
View transactions affecting a chosen account.
```python
def show_ledger(self):
    self.clear_content()
    tk.Label(self.content_frame, text="Ledger", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
    # Dropdown for account selection and a Treeview to display ledger entries.
```
*Explanation:*  
- Loads and displays all transactions from the `TransactionDetail` table for a selected account.

#### g. Reports Screen
Generates reports and provides PDF/print options.
```python
def show_reports(self):
    self.clear_content()
    tk.Label(self.content_frame, text="Reports", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
    # Buttons for Trial Balance, Income Statement, and Balance Sheet.
    # Additional buttons for "Save as PDF" and "Print Report".
```
*Explanation:*  
- The Income Statement uses a two‑pane layout to display revenues and expenses.
- It calculates net profit or net loss and displays a balancing line.
- The code stores the text version of the report (in `self.current_report`) so that it can be saved as a PDF or printed.

#### h. Audit Logs Screen
Lists all logged actions.
```python
def show_audit_logs(self):
    self.clear_content()
    tk.Label(self.content_frame, text="Audit Logs", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
    tree = ttk.Treeview(self.content_frame, columns=("ID", "Timestamp", "Action", "Details"), show="headings")
    # Code to populate the treeview with audit log entries.
```
*Explanation:*  
- Displays a full audit trail of system events.

---

## 6. Demonstration and Sample Data

### A. Master Accounts Setup
Using the Masters (Accounts) screen, create the following accounts (among others):

1. **Cash** – *Asset*  
2. **Bank** – *Asset*  
3. **Accounts Receivable** – *Asset*  
4. **Inventory** – *Stock*  
5. **Prepaid Expenses** – *Asset*  
6. **Fixed Assets** – *Asset*  
7. **Accounts Payable** – *Liability*  
8. **Loan Payable** – *Liability*  
9. **Accrued Expenses** – *Liability*  
10. **Capital** – *Equity*  
11. **Retained Earnings** – *Equity*  
12. **Sales Revenue** – *Revenue*  
13. **Service Revenue** – *Revenue*  
14. **Discount Received** – *Revenue*  
15. **Cost of Goods Sold (COGS)** – *Expense*  
16. **Salaries Expense** – *Expense*  
17. **Rent Expense** – *Expense*  
18. **Utilities Expense** – *Expense*  
19. **Discount Allowed** – *Expense*  
20. **Depreciation Expense** – *Expense*  
21. **Bad Debt Expense** – *Expense*  
22. **Purchase Expense** – *Expense*  
23. **Sales Return** – *Revenue* (or contra revenue)  
24. **Purchase Return** – *Expense* (or contra expense)  
25. **Interest Expense** – *Expense*

### B. Voucher Transactions
Enter 50+ transactions covering every voucher type. (Refer to the sample script in the documentation for each voucher transaction with details.)

### C. Stock Management
Enter at least two items (e.g., Widget A, Gadget B) with quantities and prices.

### D. Ledger Viewing
Select key accounts (e.g., Cash, Bank, Inventory) in the Ledger screen and verify that all related transactions appear.

### E. Reports Testing
Generate the following reports and verify that:  
- **Trial Balance:** All accounts and updated balances are shown.  
- **Income Statement:** Revenues and expenses are listed in a two‑pane layout with a balancing "Net Profit c/d" or "Net Loss c/d" line.  
- **Balance Sheet:** Assets are balanced against Liabilities + Equity.  
- Use the **Save as PDF** and **Print Report** buttons to create and print a PDF copy.

### F. Audit Logs
Review the audit logs to see all actions, such as registrations, voucher entries, account modifications, etc.

---

## 7. Future Enhancements

- **Advanced Reporting:** Dynamic charts, filtering, and multi-period analysis.
- **User Role Management:** Adding roles and permissions for different user types.
- **Data Export:** Options to export to CSV, Excel, etc.
- **Enhanced Error Handling:** More robust validations and exception logging.

---

## 8. Conclusion

This documentation covers every aspect of this Accounting Application. The code is structured into clear modules handling database models, PDF generation, login, and a multi-functional main application. The sample data demonstration provides over 50 transactions and tests every type of voucher and account. Use this guide to fully test, understand, and extend the application as needed.

--