import sqlite3
from datetime import datetime
import random

# Function to create a connection to the SQLite database
def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return connimport sqlite3
from datetime import datetime
import random
import re

# Function to create a connection to the SQLite database
def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

# Function to initialize the database (create tables if not exist)
def initialize_database(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_number INTEGER PRIMARY KEY,
            account_holder TEXT NOT NULL,
            balance REAL NOT NULL,
            pin TEXT NOT NULL
        )
    """)
   
    conn.commit()

def create_user_table(conn, account_number):
    cursor = conn.cursor()
    table_name = f"user_{account_number}"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            transaction_id INTEGER PRIMARY KEY,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_date TEXT NOT NULL,
            balance REAL NOT NULL
        )
    """)
    conn.commit()

def delete_account(conn, acct_number, pin):
    cursor = conn.cursor()
    
    # Check if the account exists and PIN is correct
    acct = cursor.execute(f"""
        SELECT * FROM accounts WHERE account_number = '{acct_number}' AND pin = '{pin}'
    """).fetchone()
    
    if acct is None:
        print("Invalid account number or PIN.")
        return
    
    try:
        # Delete the account entry from the accounts table
        cursor.execute("""
            DELETE FROM accounts WHERE account_number = ?
        """, (acct_number,))
        
        # Drop the corresponding user transaction table
        table_name = f"user_{acct_number}"
        cursor.execute(f"""
            DROP TABLE IF EXISTS {table_name}
        """)
        
        conn.commit()
        
        print(f"Account {acct_number} has been successfully deleted.")
    except sqlite3.Error as e:
        print(f"Error deleting account: {e}")

def info(conn, acct_number, pin):
    print("-------------------Your account details---------------------")
    cursor = conn.cursor()
    
    try:
        # Use JOIN to retrieve account details along with recent transaction information
        cursor.execute(f"""
            SELECT accounts.account_number, accounts.account_holder, accounts.balance,
                   user_{acct_number}.transaction_id, user_{acct_number}.transaction_type,
                   user_{acct_number}.amount, user_{acct_number}.transaction_date,
                   user_{acct_number}.balance AS trans_balance
            FROM accounts
            JOIN user_{acct_number} ON accounts.account_number = user_{acct_number}.account_number
            WHERE accounts.account_number = '{acct_number}' AND accounts.pin = '{pin}'
            ORDER BY user_{acct_number}.transaction_date DESC
        """)
        
        result = cursor.fetchone()
        
        if result:
            acct_number, acct_holder, balance, trans_id, trans_type, amount, trans_date, trans_balance = result
            print(f"Account holder name  : {acct_holder}")
            print(f"Account Number       : {acct_number}")
            print(f"Account balance      : ${balance:.2f}")
            print("\nRecent Transaction:")
            print("{:<10} {:<20} {:<10} {:<30} {:<10}".format(
                "Trans. ID", "Transaction Type", "Amount", "Transaction Date", "Balance"))
            print("-" * 80)
            print("{:<10} {:<20} {:<10} {:<30} {:<10}".format(
                trans_id, trans_type, f"${amount:.2f}", trans_date, f"${trans_balance:.2f}"))
        else:
            print("Account not found or no transactions.")
    
    except sqlite3.Error as e:
        print(f"Error fetching account information: {e}")

def withdraw(conn, acct_number, pin):
    while True:
        try:
            withdraw_amount = float(input("Enter amount to be withdrawn: "))
            if withdraw_amount <= 0:
                print("Invalid amount. Please enter a positive value.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid amount.")
    
    cursor = conn.cursor()
    
    # Check if the account exists and PIN is correct
    acct = cursor.execute(f"""
        SELECT * FROM accounts WHERE account_number = '{acct_number}' AND pin = '{pin}'
    """).fetchone()
    
    if acct is None:
        print("Invalid account number or PIN.")
        return
    
    current_balance = acct[2]
    
    if current_balance < withdraw_amount:
        print("Withdrawal failed due to insufficient balance.")
        return
    
    new_balance = current_balance - withdraw_amount
    
    try:
       
        cursor.execute("""
            UPDATE accounts SET balance = ? WHERE account_number = ?
        """, (new_balance, acct_number))
        
        
        table_name = f"user_{acct_number}"
        transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(f"""
            INSERT INTO {table_name} (transaction_type, amount, transaction_date, balance)
            VALUES (?, ?, ?, ?)
        """, ("Withdrawal", withdraw_amount, transaction_date, new_balance))
        
        conn.commit()
        
        print(f"Withdrawal of ${withdraw_amount} successful. New balance: ${new_balance}")
    except sqlite3.Error as e:
        print(f"Error withdrawing amount: {e}")

def deposit(conn, acct_number, pin):
    while True:
        try:
            deposit_amount = float(input("Enter amount to deposit: "))
            if deposit_amount <= 0:
                print("Invalid amount. Please enter a positive value.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid amount.")
    
    cursor = conn.cursor()
    
    
    acct = cursor.execute(f"""
        SELECT * FROM accounts WHERE account_number = '{acct_number}' AND pin = '{pin}'
    """).fetchone()
    
    if acct is None:
        print("Invalid account number or PIN.")
        return
    
    current_balance = acct[2]
    new_balance = current_balance + deposit_amount
    
    try:
       
        cursor.execute("""
            UPDATE accounts SET balance = ? WHERE account_number = ?
        """, (new_balance, acct_number))
        
       
        table_name = f"user_{acct_number}"
        transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(f"""
            INSERT INTO {table_name} (transaction_type, amount, transaction_date, balance)
            VALUES (?, ?, ?, ?)
        """, ("Deposit", deposit_amount, transaction_date, new_balance))
        
        conn.commit()
        
        print(f"Deposit of ${deposit_amount} successful. New balance: ${new_balance}")
    except sqlite3.Error as e:
        print(f"Error depositing amount: {e}")

def transfer(conn, sender_acct_number, sender_pin):
    print("<---------------Enter details of account to transfer funds to--------------->")
    while True:
        receiver_acct_number = input("Enter receiver's account number: ")
        if not receiver_acct_number.isdigit() or len(receiver_acct_number) != 6:
            print("Invalid account number. Please enter a 6-digit number.")
            continue
        break
    
    while True:
        try:
            transfer_amount = float(input("Enter amount to transfer: "))
            if transfer_amount <= 0:
                print("Invalid amount. Please enter a positive value.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid amount.")
    
    cursor = conn.cursor()
    
   
    sender_acct = cursor.execute(f"""
        SELECT * FROM accounts WHERE account_number = '{sender_acct_number}' AND pin = '{sender_pin}'
    """).fetchone()
    
    if sender_acct is None:
        print("Invalid sender account number or PIN.")
        return
    
    sender_balance = sender_acct[2]
    
    if sender_balance < transfer_amount:
        print("Insufficient balance for transfer.")
        return
    
    try:
        
        new_sender_balance = sender_balance - transfer_amount
        cursor.execute("""
            UPDATE accounts SET balance = ? WHERE account_number = ?
        """, (new_sender_balance, sender_acct_number))
        
        # Insert withdrawal transaction record into sender's transaction table
        sender_table_name = f"user_{sender_acct_number}"
        sender_transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(f"""
            INSERT INTO {sender_table_name} (transaction_type, amount, transaction_date, balance)
            VALUES (?, ?, ?, ?)
        """, ("Transfer (to " + receiver_acct_number + ")", transfer_amount, sender_transaction_date, new_sender_balance))
        
        # Check if receiver's account exists
        receiver_acct = cursor.execute(f"""
            SELECT * FROM accounts WHERE account_number = '{receiver_acct_number}'
        """).fetchone()
        
        if receiver_acct is None:
            print("Receiver's account not found.")
            return
        
        # Update receiver's account balance
        receiver_balance = receiver_acct[2]
        new_receiver_balance = receiver_balance + transfer_amount
        cursor.execute("""
            UPDATE accounts SET balance = ? WHERE account_number = ?
        """, (new_receiver_balance, receiver_acct_number))
        
        # Insert deposit transaction record into receiver's transaction table
        receiver_table_name = f"user_{receiver_acct_number}"
        receiver_transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(f"""
            INSERT INTO {receiver_table_name} (transaction_type, amount, transaction_date, balance)
            VALUES (?, ?, ?, ?)
        """, ("Transfer (from " + sender_acct_number + ")", transfer_amount, receiver_transaction_date, new_receiver_balance))
        
        conn.commit()
        
        print(f"Transfer of ${
    

# Function to initialize the database (create tables if not exist)
def initialize_database(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_number INTEGER PRIMARY KEY,
            account_holder TEXT NOT NULL,
            balance REAL NOT NULL,
            pin TEXT NOT NULL
        )
    """)
   
    conn.commit()
def create_user_table(conn, account_number):
    cursor = conn.cursor()
    table_name = f"user_{account_number}"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            transaction_id INTEGER PRIMARY KEY,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_date TEXT NOT NULL,
            balance REAL NOT NULL
        )
    """)
    conn.commit()

def delete_account(conn, acct_number, pin):
    cursor = conn.cursor()
    
    # Check if the account exists and PIN is correct
    acct = cursor.execute(f"""
        SELECT * FROM accounts WHERE account_number = '{acct_number}' AND pin = {pin}
    """).fetchone()
    
    if acct is None:
        print("Invalid account number or PIN.")
        return
    
    try:
        # Delete the account entry from the accounts table
        cursor.execute("""
            DELETE FROM accounts WHERE account_number = ?
        """, (acct_number,))
        
        # Drop the corresponding user transaction table
        table_name = f"user_{acct_number}"
        cursor.execute(f"""
            DROP TABLE IF EXISTS {table_name}
        """)
        
        conn.commit()
        
        print(f"Account {acct_number} has been successfully deleted.")
    except sqlite3.Error as e:
        print(f"Error deleting account: {e}")


def info(conn, acct_number, pin):
    print("-------------------Your account details---------------------")
    cursor = conn.cursor()
    
    try:
        # Use JOIN to retrieve account details along with recent transaction information
        cursor.execute(f"""
            SELECT accounts.account_number, accounts.account_holder, accounts.balance,
                   user_{acct_number}.transaction_id, user_{acct_number}.transaction_type,
                   user_{acct_number}.amount, user_{acct_number}.transaction_date,
                   user_{acct_number}.balance AS trans_balance
            FROM accounts
            JOIN user_{acct_number} ON accounts.account_number = user_{acct_number}.account_number
            WHERE accounts.account_number = '{acct_number}' AND accounts.pin = {pin}
            ORDER BY user_{acct_number}.transaction_date DESC
        """)
        
        result = cursor.fetchone()
        
        if result:
            acct_number, acct_holder, balance, trans_id, trans_type, amount, trans_date, trans_balance = result
            print(f"Account holder name  : {acct_holder}")
            print(f"Account Number       : {acct_number}")
            print(f"Account balance      : ${balance:.2f}")
            print("\nRecent Transaction:")
            print("{:<10} {:<20} {:<10} {:<30} {:<10}".format(
                "Trans. ID", "Transaction Type", "Amount", "Transaction Date", "Balance"))
            print("-" * 80)
            print("{:<10} {:<20} {:<10} {:<30} {:<10}".format(
                trans_id, trans_type, f"${amount:.2f}", trans_date, f"${trans_balance:.2f}"))
        else:
            print("Account not found or no transactions.")
    
    except sqlite3.Error as e:
        print(f"Error fetching account information: {e}")


def withdraw(conn, acct_number, pin):
    withdraw_amount = float(input("Enter amount to be withdrawn: "))
    cursor = conn.cursor()
    
    # Check if the account exists and PIN is correct
    acct = cursor.execute(f"""
        SELECT * FROM accounts WHERE account_number = '{acct_number}' AND pin = {pin}
    """).fetchone()
    
    if acct is None:
        print("Invalid account number or PIN.")
        return
    
    current_balance = acct[2]
    
    if current_balance < withdraw_amount:
        print("Withdrawal failed due to insufficient balance.")
        return
    
    new_balance = current_balance - withdraw_amount
    
    try:
       
        cursor.execute("""
            UPDATE accounts SET balance = ? WHERE account_number = ?
        """, (new_balance, acct_number))
        
        
        table_name = f"user_{acct_number}"
        transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(f"""
            INSERT INTO {table_name} (transaction_type, amount, transaction_date, balance)
            VALUES (?, ?, ?, ?)
        """, ("Withdrawal", withdraw_amount, transaction_date, new_balance))
        
        conn.commit()
        
        print(f"Withdrawal of ${withdraw_amount} successful. New balance: ${new_balance}")
    except sqlite3.Error as e:
        print(f"Error withdrawing amount: {e}")


def deposit(conn, acct_number, pin):
    deposit_amount = float(input("Enter amount to deposit: "))
    cursor = conn.cursor()
    
    
    acct = cursor.execute(f"""
        SELECT * FROM accounts WHERE account_number = '{acct_number}' AND pin = {pin}
    """).fetchone()
    
    if acct is None:
        print("Invalid account number or PIN.")
        return
    
    current_balance = acct[2]
    new_balance = current_balance + deposit_amount
    
    try:
       
        cursor.execute("""
            UPDATE accounts SET balance = ? WHERE account_number = ?
        """, (new_balance, acct_number))
        
       
        table_name = f"user_{acct_number}"
        transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(f"""
            INSERT INTO {table_name} (transaction_type, amount, transaction_date, balance)
            VALUES (?, ?, ?, ?)
        """, ("Deposit", deposit_amount, transaction_date, new_balance))
        
        conn.commit()
        
        print(f"Deposit of ${deposit_amount} successful. New balance: ${new_balance}")
    except sqlite3.Error as e:
        print(f"Error depositing amount: {e}")

def transfer(conn, sender_acct_number, sender_pin):
    print("<---------------Enter details of account to transfer funds to--------------->")
    receiver_acct_number = input("Enter receiver's account number: ")
    transfer_amount = float(input("Enter amount to transfer: "))
    cursor = conn.cursor()
    
   
    sender_acct = cursor.execute(f"""
        SELECT * FROM accounts WHERE account_number = '{sender_acct_number}' AND pin = {sender_pin}
    """).fetchone()
    
    if sender_acct is None:
        print("Invalid sender account number or PIN.")
        return
    
    sender_balance = sender_acct[2]
    
    if sender_balance < transfer_amount:
        print("Insufficient balance for transfer.")
        return
    
    try:
        
        new_sender_balance = sender_balance - transfer_amount
        cursor.execute("""
            UPDATE accounts SET balance = ? WHERE account_number = ?
        """, (new_sender_balance, sender_acct_number))
        
        # Insert withdrawal transaction record into sender's transaction table
        sender_table_name = f"user_{sender_acct_number}"
        sender_transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(f"""
            INSERT INTO {sender_table_name} (transaction_type, amount, transaction_date, balance)
            VALUES (?, ?, ?, ?)
        """, ("Transfer (to " + receiver_acct_number + ")", transfer_amount, sender_transaction_date, new_sender_balance))
        
        # Check if receiver's account exists
        receiver_acct = cursor.execute(f"""
            SELECT * FROM accounts WHERE account_number = '{receiver_acct_number}'
        """).fetchone()
        
        if receiver_acct is None:
            print("Receiver's account not found.")
            return
        
        # Update receiver's account balance
        receiver_balance = receiver_acct[2]
        new_receiver_balance = receiver_balance + transfer_amount
        cursor.execute("""
            UPDATE accounts SET balance = ? WHERE account_number = ?
        """, (new_receiver_balance, receiver_acct_number))
        
        # Insert deposit transaction record into receiver's transaction table
        receiver_table_name = f"user_{receiver_acct_number}"
        receiver_transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(f"""
            INSERT INTO {receiver_table_name} (transaction_type, amount, transaction_date, balance)
            VALUES (?, ?, ?, ?)
        """, ("Transfer (from " + sender_acct_number + ")", transfer_amount, receiver_transaction_date, new_receiver_balance))
        
        conn.commit()
        
        print(f"Transfer of ${transfer_amount} to account {receiver_acct_number} successful.")
        print(f"New balance in sender's account: ${new_sender_balance}")
    except sqlite3.Error as e:
        print(f"Error transferring amount: {e}")
        
def transaction_history(conn, acct_number):
    print(f"Transaction History for Account Number: {acct_number}")
    cursor = conn.cursor()
    table_name = f"user_{acct_number}"
    
    try:
        
        cursor.execute(f"""
            SELECT transaction_id, transaction_type, amount, transaction_date, balance
            FROM {table_name}
        """)
        
        transactions = cursor.fetchall()
        
        if transactions:
            print("{:<10} {:<20} {:<10} {:<30} {:<10}".format(
                "Trans. ID", "Transaction Type", "Amount", "Transaction Date", "Balance"))
            print("-" * 80)
            
            for transaction in transactions:
                trans_id, trans_type, amount, trans_date, balance = transaction
                print("{:<10} {:<20} {:<10} {:<30} {:<10}".format(
                    trans_id, trans_type, f"${amount:.2f}", trans_date, f"${balance:.2f}"))
        else:
            print("No transactions found.")
    
    except sqlite3.Error as e:
        print(f"Error fetching transaction history: {e}")

    
def login(conn):
    print("welcome customer !!!!")
    acct_number=input("Enter account number : ")
    pin=int(input("Enter password "))
    cursor = conn.cursor()
    acct=cursor.execute(f"""SELECT * FROM accounts WHERE  account_number='{acct_number}' AND  pin={pin}""").fetchone()
    if acct is not None:
        print(f"u has been login !!!! {acct[1]}  and account number {acct[0]}")
        operation=0
        while(operation != 5):
            print("1.Check balance ")
            print("2.withdraw money")
            print("3.Deposit money")
            print("4.transfer fund to another account")
            print("5.Check transaction history")
            print("6.Delete Account")
            print("7.Sign out")

            operation=int(input("What do want to do :  "))
            match(operation):
                case 1:
                  info(conn,acct_number,pin)
                case 2:
                  withdraw(conn,acct_number,pin)
                case 3:
                  deposit(conn,acct_number,pin)
                case 4:
                  transfer(conn,acct_number,pin)
                case 5:
                   transaction_history(conn,acct_number)
                case 6:
                   delete_account(conn,acct_number,pin)
                case 7:
                    print("Your account sign out successful")
                    return  
                case _:
                  print("Invalid Input!!!")      
    
        return
    else:
       print("Account not found")
       return


def sign(conn):
    print("Welcome to  KVS Bank!!!")
    print("To open an account, please provide the following details:")
    
    while True:
        try:
            acct_name = input("Enter Account holder Name: ")
            if any(char.isdigit() for char in acct_name):
                raise ValueError("Account holder name cannot contain numbers.")
            break
        except ValueError as e:
            print(f"Error: {e}")
    
    password = int(input("Enter password: "))
    initial_amt = int(input("Enter initial amount in account: "))
    acct_number = random.randint(100000, 999999)
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO accounts (account_number, account_holder, balance, pin)
            VALUES (?, ?, ?, ?)
        """, (acct_number, acct_name, initial_amt, password))
        conn.commit()
        
        create_user_table(conn, acct_number)  
        
        print("Account created successfully!")
        print(f"Account holder name: {acct_name}")
        print(f"Account Number: {acct_number}")
    except sqlite3.Error as e:
        print(f"Error creating account: {e}")




def main():
    database = "banking_system.db"
    conn = create_connection(database)
    initialize_database(conn)
    operation=0
    while(operation != 3):
        print("1.Create an account !!!!")
        print("2.Login")
        print("3.Exit")


        operation=int(input("Enter Your choice : "))




        match(operation):
            case 1:
                sign(conn)
            case 2:
                login(conn)
            case 3:
                print("Thanks to visit")
                return
            case _:
                print('invalid Input')
    return
        
    

if __name__== '_main_':
    main()