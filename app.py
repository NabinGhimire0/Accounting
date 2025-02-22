import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

# -------------------------------
# Database Setup using SQLAlchemy
# -------------------------------
Base = declarative_base()
engine = create_engine('sqlite:///accounting.db', echo=False)
Session = sessionmaker(bind=engine)
session = Session()

# --- User model ---
class User(Base):
    __tablename__ = 'users'
    id       = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password = Column(String(200), nullable=False)

# --- Account model ---
class Account(Base):
    __tablename__ = 'accounts'
    id      = Column(Integer, primary_key=True)
    name    = Column(String(100), nullable=False)
    type    = Column(String(50), nullable=False)  # Asset, Liability, Equity, Revenue, Expense, Stock
    balance = Column(Float, default=0.0)

# --- Journal Entry / Voucher model ---
class JournalEntry(Base):
    __tablename__ = 'journal_entries'
    id           = Column(Integer, primary_key=True)
    date         = Column(DateTime, default=datetime.utcnow)
    description  = Column(String(200))
    voucher_type = Column(String(50), default="Journal")  # Journal, Payment, Receipt, Contra, Debit Note, Credit Note
    transactions = relationship('TransactionDetail', back_populates='journal_entry')

# --- Transaction Details ---
class TransactionDetail(Base):
    __tablename__ = 'transaction_details'
    id               = Column(Integer, primary_key=True)
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'))
    account_id       = Column(Integer, ForeignKey('accounts.id'))
    amount           = Column(Float, nullable=False)
    type             = Column(String(10), nullable=False)  # debit or credit
    journal_entry    = relationship('JournalEntry', back_populates='transactions')

# --- Audit Log ---
class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id        = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action    = Column(String(100))
    details   = Column(String(500))

# --- Stock Management ---
class Stock(Base):
    __tablename__ = 'stocks'
    id             = Column(Integer, primary_key=True)
    product_name   = Column(String(100), nullable=False)
    quantity       = Column(Integer, default=0)
    purchase_price = Column(Float, default=0.0)
    selling_price  = Column(Float, default=0.0)
    details        = Column(Text)

Base.metadata.create_all(engine)

def log_action(action, details):
    audit = AuditLog(action=action, details=details)
    session.add(audit)
    session.commit()

# -------------------------------
# Login / Registration Window
# -------------------------------
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
        
    def login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return
        
        user = session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            log_action("Login", f"User '{username}' logged in.")
            self.master.destroy()
            root = tk.Tk()
            TallyApp(root, user)
            root.mainloop()
        else:
            messagebox.showerror("Error", "Invalid credentials.")
    
    def register(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return
        
        if session.query(User).filter_by(username=username).first():
            messagebox.showerror("Error", "Username already exists.")
            return
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        session.add(new_user)
        session.commit()
        log_action("Registration", f"User '{username}' registered.")
        messagebox.showinfo("Success", "User registered successfully. You can now log in.")

# -------------------------------
# Main Tally-like Application Window
# -------------------------------
class TallyApp:
    def __init__(self, master, user):
        self.master = master
        self.user = user
        master.title("Tally-like Accounting Software")
        master.geometry("1100x650")
        
        # Left Navigation Panel
        self.nav_frame = tk.Frame(master, width=200, bg='lightgray')
        self.nav_frame.pack(side='left', fill='y')
        
        btn_config = {'width': 20, 'padx': 5, 'pady': 5, 'anchor': 'w'}
        tk.Button(self.nav_frame, text="Dashboard", command=self.show_dashboard, **btn_config).pack(fill='x')
        tk.Button(self.nav_frame, text="Masters (Accounts)", command=self.show_accounts_master, **btn_config).pack(fill='x')
        tk.Button(self.nav_frame, text="Voucher Entry", command=self.show_voucher_entry, **btn_config).pack(fill='x')
        tk.Button(self.nav_frame, text="Stock Management", command=self.show_stock_management, **btn_config).pack(fill='x')
        tk.Button(self.nav_frame, text="Ledger", command=self.show_ledger, **btn_config).pack(fill='x')
        tk.Button(self.nav_frame, text="Reports", command=self.show_reports, **btn_config).pack(fill='x')
        tk.Button(self.nav_frame, text="Audit Logs", command=self.show_audit_logs, **btn_config).pack(fill='x')
        
        # Main Content Area
        self.content_frame = tk.Frame(master, bg='white')
        self.content_frame.pack(side='left', fill='both', expand=True)
        
        self.show_dashboard()
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    # ---------------------------
    # Dashboard Screen
    # ---------------------------
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
    
    # ---------------------------
    # Masters (Accounts) Screen with Delete Feature
    # ---------------------------
    def show_accounts_master(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Accounts Master", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
        
        # Accounts Treeview in tabular form
        tree_frame = tk.Frame(self.content_frame)
        tree_frame.pack(fill='both', expand=True)
        self.accounts_tree = ttk.Treeview(tree_frame, columns=("ID", "Name", "Type", "Balance"), show="headings")
        for col in ("ID", "Name", "Type", "Balance"):
            self.accounts_tree.heading(col, text=col)
            self.accounts_tree.column(col, width=120)
        self.accounts_tree.pack(fill='both', expand=True)
        self.refresh_accounts_tree()
        
        # Buttons and Form Frame for Add/Delete
        btn_frame = tk.Frame(self.content_frame, bg='white')
        btn_frame.pack(fill='x', pady=5)
        
        tk.Label(btn_frame, text="Name:", bg='white').grid(row=0, column=0, padx=5, pady=2)
        self.entry_account_name = tk.Entry(btn_frame)
        self.entry_account_name.grid(row=0, column=1, padx=5, pady=2)
        tk.Label(btn_frame, text="Type:", bg='white').grid(row=0, column=2, padx=5, pady=2)
        self.combo_account_type = ttk.Combobox(btn_frame, values=["Asset", "Liability", "Equity", "Revenue", "Expense", "Stock"])
        self.combo_account_type.grid(row=0, column=3, padx=5, pady=2)
        tk.Button(btn_frame, text="Add Account", command=self.add_account).grid(row=0, column=4, padx=5, pady=2)
        tk.Button(btn_frame, text="Delete Account", command=self.delete_account).grid(row=0, column=5, padx=5, pady=2)
    
    def refresh_accounts_tree(self):
        for i in self.accounts_tree.get_children():
            self.accounts_tree.delete(i)
        accounts = session.query(Account).all()
        for acc in accounts:
            self.accounts_tree.insert("", "end", values=(acc.id, acc.name, acc.type, acc.balance))
    
    def add_account(self):
        name = self.entry_account_name.get().strip()
        acc_type = self.combo_account_type.get().strip()
        if not name or not acc_type:
            messagebox.showerror("Error", "Please provide both name and type.")
            return
        new_acc = Account(name=name, type=acc_type)
        session.add(new_acc)
        session.commit()
        log_action("Account Created", f"Account '{name}' of type '{acc_type}' created.")
        messagebox.showinfo("Success", "Account added successfully.")
        self.refresh_accounts_tree()
    
    def delete_account(self):
        selected_item = self.accounts_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select an account to delete.")
            return
        if not messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected account?"):
            return
        item = self.accounts_tree.item(selected_item)
        acc_id = item["values"][0]
        acc = session.query(Account).get(acc_id)
        if acc:
            session.delete(acc)
            session.commit()
            log_action("Account Deleted", f"Account '{acc.name}' (ID {acc.id}) deleted.")
            messagebox.showinfo("Success", "Account deleted successfully.")
            self.refresh_accounts_tree()
        else:
            messagebox.showerror("Error", "Account not found.")
    
    # ---------------------------
    # Voucher Entry Screen
    # ---------------------------
    def show_voucher_entry(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Voucher Entry", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
        
        form_frame = tk.Frame(self.content_frame, bg='white')
        form_frame.pack(fill='x', pady=5)
        tk.Label(form_frame, text="Voucher Type:", bg='white').grid(row=0, column=0, padx=5, pady=2)
        self.combo_voucher_type = ttk.Combobox(form_frame, values=["Journal", "Payment", "Receipt", "Contra", "Debit Note", "Credit Note"])
        self.combo_voucher_type.current(0)
        self.combo_voucher_type.grid(row=0, column=1, padx=5, pady=2)
        tk.Label(form_frame, text="Description:", bg='white').grid(row=0, column=2, padx=5, pady=2)
        self.entry_voucher_desc = tk.Entry(form_frame, width=50)
        self.entry_voucher_desc.grid(row=0, column=3, padx=5, pady=2)
        
        self.transactions_frame = tk.Frame(self.content_frame, bg='white')
        self.transactions_frame.pack(fill='both', pady=10)
        header = ["Account", "Amount", "Type"]
        for i, h in enumerate(header):
            tk.Label(self.transactions_frame, text=h, borderwidth=1, relief="solid", width=20, bg='lightblue').grid(row=0, column=i, padx=1, pady=1)
        
        self.transaction_rows = []
        tk.Button(self.content_frame, text="Add Transaction", command=self.add_transaction_row).pack(pady=5)
        tk.Button(self.content_frame, text="Submit Voucher", command=self.submit_voucher).pack(pady=5)
    
    def add_transaction_row(self):
        row_index = len(self.transaction_rows) + 1
        accounts = session.query(Account).all()
        account_list = [f"{acc.id} - {acc.name}" for acc in accounts]
        account_var = tk.StringVar()
        account_combo = ttk.Combobox(self.transactions_frame, textvariable=account_var, values=account_list, width=18)
        account_combo.grid(row=row_index, column=0, padx=5, pady=2)
        amount_entry = tk.Entry(self.transactions_frame, width=22)
        amount_entry.grid(row=row_index, column=1, padx=5, pady=2)
        type_combo = ttk.Combobox(self.transactions_frame, values=["debit", "credit"], width=18)
        type_combo.grid(row=row_index, column=2, padx=5, pady=2)
        self.transaction_rows.append((account_combo, amount_entry, type_combo))
    
    def submit_voucher(self):
        voucher_type = self.combo_voucher_type.get().strip()
        description = self.entry_voucher_desc.get().strip()
        if not description:
            messagebox.showerror("Error", "Please provide a voucher description.")
            return
        
        transactions = []
        total_debit = 0.0
        total_credit = 0.0
        for (acc_combo, amt_entry, type_combo) in self.transaction_rows:
            acc_str = acc_combo.get().strip()
            if not acc_str:
                continue
            try:
                account_id = int(acc_str.split(" - ")[0])
            except Exception:
                messagebox.showerror("Error", "Invalid account selection.")
                return
            try:
                amount = float(amt_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid amount.")
                return
            tran_type = type_combo.get().strip().lower()
            if tran_type not in ["debit", "credit"]:
                messagebox.showerror("Error", "Transaction type must be 'debit' or 'credit'.")
                return
            transactions.append({"account_id": account_id, "amount": amount, "type": tran_type})
            if tran_type == "debit":
                total_debit += amount
            else:
                total_credit += amount
        
        if len(transactions) < 2:
            messagebox.showerror("Error", "At least two transactions are required.")
            return
        if abs(total_debit - total_credit) > 0.001:
            messagebox.showerror("Error", "Total debits must equal total credits.")
            return
        
        voucher = JournalEntry(description=description, voucher_type=voucher_type)
        session.add(voucher)
        session.commit()  # To get voucher.id
        
        for tran in transactions:
            t = TransactionDetail(
                journal_entry_id=voucher.id,
                account_id=tran["account_id"],
                amount=tran["amount"],
                type=tran["type"]
            )
            session.add(t)
            acc_obj = session.query(Account).get(tran["account_id"])
            if tran["type"] == "debit":
                acc_obj.balance += tran["amount"]
            else:
                acc_obj.balance -= tran["amount"]
        session.commit()
        log_action("Voucher Entry", f"Voucher ID {voucher.id} ({voucher.voucher_type}) created: {description}")
        messagebox.showinfo("Success", "Voucher submitted successfully.")
        self.show_voucher_entry()
    
    # ---------------------------
    # Stock Management Screen
    # ---------------------------
    def show_stock_management(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Stock Management", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
        
        tree_frame = tk.Frame(self.content_frame)
        tree_frame.pack(fill='both', expand=True)
        self.stock_tree = ttk.Treeview(tree_frame, columns=("ID", "Product Name", "Quantity", "Purchase Price", "Selling Price"), show="headings")
        for col in ("ID", "Product Name", "Quantity", "Purchase Price", "Selling Price"):
            self.stock_tree.heading(col, text=col)
            self.stock_tree.column(col, width=120)
        self.stock_tree.pack(fill='both', expand=True)
        self.refresh_stock_tree()
        
        form_frame = tk.Frame(self.content_frame, bg='white')
        form_frame.pack(fill='x', pady=10)
        tk.Label(form_frame, text="Product Name:", bg='white').grid(row=0, column=0, padx=5, pady=2)
        self.entry_product_name = tk.Entry(form_frame)
        self.entry_product_name.grid(row=0, column=1, padx=5, pady=2)
        tk.Label(form_frame, text="Quantity:", bg='white').grid(row=0, column=2, padx=5, pady=2)
        self.entry_quantity = tk.Entry(form_frame)
        self.entry_quantity.grid(row=0, column=3, padx=5, pady=2)
        tk.Label(form_frame, text="Purchase Price:", bg='white').grid(row=1, column=0, padx=5, pady=2)
        self.entry_purchase_price = tk.Entry(form_frame)
        self.entry_purchase_price.grid(row=1, column=1, padx=5, pady=2)
        tk.Label(form_frame, text="Selling Price:", bg='white').grid(row=1, column=2, padx=5, pady=2)
        self.entry_selling_price = tk.Entry(form_frame)
        self.entry_selling_price.grid(row=1, column=3, padx=5, pady=2)
        tk.Label(form_frame, text="Details:", bg='white').grid(row=2, column=0, padx=5, pady=2)
        self.entry_stock_details = tk.Entry(form_frame, width=50)
        self.entry_stock_details.grid(row=2, column=1, columnspan=3, padx=5, pady=2)
        tk.Button(form_frame, text="Add Stock Item", command=self.add_stock_item).grid(row=3, column=0, columnspan=4, pady=5)
    
    def refresh_stock_tree(self):
        for i in self.stock_tree.get_children():
            self.stock_tree.delete(i)
        stocks = session.query(Stock).all()
        for item in stocks:
            self.stock_tree.insert("", "end", values=(item.id, item.product_name, item.quantity, item.purchase_price, item.selling_price))
    
    def add_stock_item(self):
        product_name = self.entry_product_name.get().strip()
        try:
            quantity = int(self.entry_quantity.get().strip())
            purchase_price = float(self.entry_purchase_price.get().strip())
            selling_price = float(self.entry_selling_price.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for quantity and prices.")
            return
        details = self.entry_stock_details.get().strip()
        if not product_name:
            messagebox.showerror("Error", "Product name is required.")
            return
        new_stock = Stock(product_name=product_name, quantity=quantity, purchase_price=purchase_price, selling_price=selling_price, details=details)
        session.add(new_stock)
        session.commit()
        log_action("Stock Entry", f"New stock item '{product_name}' added with quantity {quantity}.")
        messagebox.showinfo("Success", "Stock item added successfully.")
        self.refresh_stock_tree()
    
    # ---------------------------
    # Ledger Screen
    # ---------------------------
    def show_ledger(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Ledger", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
        top_frame = tk.Frame(self.content_frame, bg='white')
        top_frame.pack(fill='x', pady=5)
        tk.Label(top_frame, text="Select Account:", bg='white').pack(side='left', padx=5)
        self.ledger_account_var = tk.StringVar()
        self.ledger_account_combo = ttk.Combobox(top_frame, textvariable=self.ledger_account_var)
        self.refresh_ledger_account_combo()
        self.ledger_account_combo.pack(side='left', padx=5)
        tk.Button(top_frame, text="Load Ledger", command=self.load_ledger).pack(side='left', padx=5)
        
        self.ledger_tree = ttk.Treeview(self.content_frame, columns=("ID", "VoucherID", "AccountID", "Amount", "Type"), show="headings")
        for col in ("ID", "VoucherID", "AccountID", "Amount", "Type"):
            self.ledger_tree.heading(col, text=col)
            self.ledger_tree.column(col, width=100)
        self.ledger_tree.pack(fill='both', expand=True, pady=5)
    
    def refresh_ledger_account_combo(self):
        accounts = session.query(Account).all()
        acc_list = [f"{acc.id} - {acc.name}" for acc in accounts]
        self.ledger_account_combo['values'] = acc_list
    
    def load_ledger(self):
        acc_str = self.ledger_account_combo.get().strip()
        if not acc_str:
            messagebox.showerror("Error", "Please select an account.")
            return
        account_id = int(acc_str.split(" - ")[0])
        transactions = session.query(TransactionDetail).filter_by(account_id=account_id).all()
        for i in self.ledger_tree.get_children():
            self.ledger_tree.delete(i)
        for tran in transactions:
            self.ledger_tree.insert("", "end", values=(tran.id, tran.journal_entry_id, tran.account_id, tran.amount, tran.type))
    
    # ---------------------------
    # Reports Screen (Modern Two-Pane & Printable)
    # ---------------------------
    def show_reports(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Reports", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
        btn_frame = tk.Frame(self.content_frame, bg='white')
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Trial Balance", command=self.report_trial_balance, width=15).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Income Statement", command=self.report_income_statement, width=15).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Balance Sheet", command=self.report_balance_sheet, width=15).grid(row=0, column=2, padx=5)
        
        # A frame to hold the modern two-pane table (if needed)
        self.report_frame = tk.Frame(self.content_frame, bg='white')
        self.report_frame.pack(fill='both', padx=5, pady=5, expand=True)
        
        # Print Report button at the bottom
        tk.Button(self.content_frame, text="Print Report", command=self.print_report).pack(pady=5)
        # Variable to store current report content (as text)
        self.current_report = ""
    
    def report_trial_balance(self):
        # Clear report frame
        for widget in self.report_frame.winfo_children():
            widget.destroy()
        accounts = session.query(Account).all()
        tree = ttk.Treeview(self.report_frame, columns=("ID", "Name", "Type", "Balance"), show="headings")
        for col in ("ID", "Name", "Type", "Balance"):
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(fill='both', expand=True)
        for acc in accounts:
            tree.insert("", "end", values=(acc.id, acc.name, acc.type, f"{acc.balance:.2f}"))
        # Store report text for printing
        report_text = "TRIAL BALANCE\n\n"
        report_text += "{:<5} {:<20} {:<15} {:>10}\n".format("ID", "Name", "Type", "Balance")
        report_text += "-"*55 + "\n"
        for acc in accounts:
            report_text += "{:<5} {:<20} {:<15} {:>10.2f}\n".format(acc.id, acc.name, acc.type, acc.balance)
        self.current_report = report_text
    
    def report_income_statement(self):
        # Clear report frame
        for widget in self.report_frame.winfo_children():
            widget.destroy()
        revenues = session.query(Account).filter_by(type="Revenue").all()
        expenses = session.query(Account).filter_by(type="Expense").all()
        total_rev = sum(acc.balance for acc in revenues)
        total_exp = sum(acc.balance for acc in expenses)
        net_income = total_rev - total_exp
        
        # Use a PanedWindow to show Revenues on left and Expenses on right
        pw = tk.PanedWindow(self.report_frame, orient=tk.HORIZONTAL, bg='white')
        pw.pack(fill='both', expand=True)
        
        left_frame = tk.Frame(pw, bg='white')
        right_frame = tk.Frame(pw, bg='white')
        pw.add(left_frame)
        pw.add(right_frame)
        
        tk.Label(left_frame, text="Revenues", font=('Arial', 12, 'bold'), bg='white').pack(pady=5)
        rev_tree = ttk.Treeview(left_frame, columns=("ID", "Name", "Balance"), show="headings")
        for col in ("ID", "Name", "Balance"):
            rev_tree.heading(col, text=col)
            rev_tree.column(col, width=120)
        rev_tree.pack(fill='both', expand=True)
        for acc in revenues:
            rev_tree.insert("", "end", values=(acc.id, acc.name, f"{acc.balance:.2f}"))
        
        tk.Label(right_frame, text="Expenses", font=('Arial', 12, 'bold'), bg='white').pack(pady=5)
        exp_tree = ttk.Treeview(right_frame, columns=("ID", "Name", "Balance"), show="headings")
        for col in ("ID", "Name", "Balance"):
            exp_tree.heading(col, text=col)
            exp_tree.column(col, width=120)
        exp_tree.pack(fill='both', expand=True)
        for acc in expenses:
            exp_tree.insert("", "end", values=(acc.id, acc.name, f"{acc.balance:.2f}"))
        
        # Below the panes, show summary
        summary_label = tk.Label(self.report_frame, text=f"Total Revenue: {total_rev:.2f}    Total Expense: {total_exp:.2f}    Net Income: {net_income:.2f}", font=('Arial', 12), bg='white')
        summary_label.pack(pady=5)
        
        # Store report text for printing
        report_text = "INCOME STATEMENT\n\nRevenues:\n"
        report_text += "{:<5} {:<20} {:>10}\n".format("ID", "Name", "Balance")
        report_text += "-"*40 + "\n"
        for acc in revenues:
            report_text += "{:<5} {:<20} {:>10.2f}\n".format(acc.id, acc.name, acc.balance)
        report_text += "\nExpenses:\n"
        report_text += "{:<5} {:<20} {:>10}\n".format("ID", "Name", "Balance")
        report_text += "-"*40 + "\n"
        for acc in expenses:
            report_text += "{:<5} {:<20} {:>10.2f}\n".format(acc.id, acc.name, acc.balance)
        report_text += f"\nTotal Revenue: {total_rev:.2f}\nTotal Expense: {total_exp:.2f}\nNet Income: {net_income:.2f}\n"
        self.current_report = report_text
    
    def report_balance_sheet(self):
        # Clear report frame
        for widget in self.report_frame.winfo_children():
            widget.destroy()
        assets = session.query(Account).filter_by(type="Asset").all()
        liabilities = session.query(Account).filter_by(type="Liability").all()
        equity = session.query(Account).filter_by(type="Equity").all()
        total_assets = sum(acc.balance for acc in assets)
        total_liab = sum(acc.balance for acc in liabilities)
        total_equity = sum(acc.balance for acc in equity)
        
        # Use a PanedWindow: Left pane for Assets; Right pane for Liabilities & Equity
        pw = tk.PanedWindow(self.report_frame, orient=tk.HORIZONTAL, bg='white')
        pw.pack(fill='both', expand=True)
        
        left_frame = tk.Frame(pw, bg='white')
        right_frame = tk.Frame(pw, bg='white')
        pw.add(left_frame)
        pw.add(right_frame)
        
        tk.Label(left_frame, text="Assets", font=('Arial', 12, 'bold'), bg='white').pack(pady=5)
        asset_tree = ttk.Treeview(left_frame, columns=("ID", "Name", "Balance"), show="headings")
        for col in ("ID", "Name", "Balance"):
            asset_tree.heading(col, text=col)
            asset_tree.column(col, width=120)
        asset_tree.pack(fill='both', expand=True)
        for acc in assets:
            asset_tree.insert("", "end", values=(acc.id, acc.name, f"{acc.balance:.2f}"))
        
        tk.Label(right_frame, text="Liabilities & Equity", font=('Arial', 12, 'bold'), bg='white').pack(pady=5)
        le_tree = ttk.Treeview(right_frame, columns=("ID", "Name", "Balance"), show="headings")
        for col in ("ID", "Name", "Balance"):
            le_tree.heading(col, text=col)
            le_tree.column(col, width=120)
        le_tree.pack(fill='both', expand=True)
        for acc in liabilities:
            le_tree.insert("", "end", values=(acc.id, acc.name, f"{acc.balance:.2f}"))
        for acc in equity:
            le_tree.insert("", "end", values=(acc.id, acc.name, f"{acc.balance:.2f}"))
        
        summary_label = tk.Label(self.report_frame, text=f"Total Assets: {total_assets:.2f}    Total Liabilities: {total_liab:.2f}    Total Equity: {total_equity:.2f}\nAccounting Equation Valid: {abs(total_assets - (total_liab + total_equity)) < 0.001}", font=('Arial', 12), bg='white')
        summary_label.pack(pady=5)
        
        # Store report text for printing
        report_text = "BALANCE SHEET\n\nAssets:\n"
        report_text += "{:<5} {:<20} {:>10}\n".format("ID", "Name", "Balance")
        report_text += "-"*40 + "\n"
        for acc in assets:
            report_text += "{:<5} {:<20} {:>10.2f}\n".format(acc.id, acc.name, acc.balance)
        report_text += "\nLiabilities & Equity:\n"
        report_text += "{:<5} {:<20} {:>10}\n".format("ID", "Name", "Balance")
        report_text += "-"*40 + "\n"
        for acc in liabilities:
            report_text += "{:<5} {:<20} {:>10.2f}\n".format(acc.id, acc.name, acc.balance)
        for acc in equity:
            report_text += "{:<5} {:<20} {:>10.2f}\n".format(acc.id, acc.name, acc.balance)
        report_text += f"\nTotal Assets: {total_assets:.2f}\nTotal Liabilities: {total_liab:.2f}\nTotal Equity: {total_equity:.2f}\n"
        report_text += f"Accounting Equation Valid: {abs(total_assets - (total_liab + total_equity)) < 0.001}\n"
        self.current_report = report_text
    
    def print_report(self):
        if not self.current_report:
            messagebox.showerror("Error", "No report available to print.")
            return
        # For demonstration, write the current report to a text file.
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")],
                                                 title="Save Report As")
        if file_path:
            with open(file_path, "w") as f:
                f.write(self.current_report)
            messagebox.showinfo("Print Report", f"Report saved to {os.path.basename(file_path)}. Use your system's print feature to print the file.")
    
    # ---------------------------
    # Audit Logs Screen
    # ---------------------------
    def show_audit_logs(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Audit Logs", font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
        tree = ttk.Treeview(self.content_frame, columns=("ID", "Timestamp", "Action", "Details"), show="headings")
        for col in ("ID", "Timestamp", "Action", "Details"):
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(fill='both', expand=True, padx=5, pady=5)
        logs = session.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
        for log in logs:
            tree.insert("", "end", values=(log.id, log.timestamp.strftime("%Y-%m-%d %H:%M:%S"), log.action, log.details))

# -------------------------------
# Run the Application
# -------------------------------
if __name__ == '__main__':
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()
