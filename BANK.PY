#!/usr/bin/env python3
"""
Secure Bank Account Management System (Python)
- PIN stored as SHA-256 hash (using hashlib)
- Accounts persisted in accounts.json
- Transactions appended to transactions.txt
- Demonstrates OOP access-conventions: __private, _protected, public
"""

import json
import hashlib
import os
from getpass import getpass

ACCOUNTS_FILE = "accounts.json"
TRANSACTION_LOG = "transactions.txt"

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def load_accounts() -> dict:
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    with open(ACCOUNTS_FILE, "r") as f:
        return json.load(f)

def save_accounts(accounts: dict):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=2)

def log_transaction(owner: str, ttype: str, amount: float):
    with open(TRANSACTION_LOG, "a") as f:
        f.write(f"{owner} | {ttype} | ${amount:.2f}\n")

class Account:
    def __init__(self, account_number: int, owner_name: str, pin: str, balance: float):
        # private (name mangling)
        self.__account_number = int(account_number)
        # protected (convention)
        self._balance = float(balance)
        # public
        self.owner_name = owner_name
        # store hashed pin
        self.__pin_hash = sha256_hex(pin)

    # Accessor for private account number
    def show_account_number(self):
        print("Account Number:", self.__account_number)

    # Verify PIN
    def verify_pin(self, pin: str) -> bool:
        return sha256_hex(pin) == self.__pin_hash

    def deposit(self, amt: float):
        self._balance += amt
        print(f"Deposited: ${amt:.2f}")
        log_transaction(self.owner_name, "Deposit", amt)

    def withdraw(self, amt: float):
        if amt > self._balance:
            print("Insufficient Balance!")
            return
        self._balance -= amt
        print(f"Withdrawn: ${amt:.2f}")
        log_transaction(self.owner_name, "Withdraw", amt)

    def show_balance(self):
        print(f"Balance for {self.owner_name}: ${self._balance:.2f}")

    # expose internal state for persistence
    def to_dict(self) -> dict:
        return {
            "account_number": self.__account_number,
            "owner_name": self.owner_name,
            "pin_hash": self.__pin_hash,
            "balance": self._balance,
            "type": "Account"
        }

    @staticmethod
    def from_dict(d: dict):
        # create a bare Account preserving hashed pin (we'll bypass constructor's hashing)
        acct = Account(d["account_number"], d["owner_name"], "dummy", d["balance"])
        acct.__dict__['_Account__pin_hash'] = d["pin_hash"]
        return acct

class SavingsAccount(Account):
    def __init__(self, account_number: int, owner_name: str, pin: str, balance: float, interest_rate: float):
        super().__init__(account_number, owner_name, pin, balance)
        self.interest_rate = float(interest_rate)

    def add_interest(self):
        interest = self._balance * self.interest_rate / 100.0
        self._balance += interest
        print(f"Interest added: ${interest:.2f}")
        log_transaction(self.owner_name, "Interest", interest)

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "type": "SavingsAccount",
            "interest_rate": self.interest_rate
        })
        return base

    @staticmethod
    def from_dict(d: dict):
        acct = SavingsAccount(d["account_number"], d["owner_name"], "dummy", d["balance"], d.get("interest_rate", 0.0))
        acct.__dict__['_Account__pin_hash'] = d["pin_hash"]
        return acct

# Helper to persist account objects (we store by account_number)
def save_account_obj(acct_obj):
    accounts = load_accounts()
    acct_data = acct_obj.to_dict()
    key = str(acct_data["account_number"])
    accounts[key] = acct_data
    save_accounts(accounts)

def load_account_by_number(acc_no: int):
    accounts = load_accounts()
    key = str(acc_no)
    if key not in accounts:
        return None
    data = accounts[key]
    if data.get("type") == "SavingsAccount":
        return SavingsAccount.from_dict(data)
    else:
        return Account.from_dict(data)

def create_account_interactive():
    acc_no = int(input("Enter Account Number: ").strip())
    name = input("Enter Name: ").strip()
    bal = float(input("Enter Initial Balance: ").strip())
    pin = getpass("Enter PIN (input hidden): ").strip()
    rate = float(input("Enter Interest Rate (for Savings): ").strip())
    acct = SavingsAccount(acc_no, name, pin, bal, rate)
    save_account_obj(acct)
    print("Account created successfully!")
    acct.show_account_number()

def login_and_transaction_interactive():
    acc_no = int(input("Enter Account Number: ").strip())
    acct = load_account_by_number(acc_no)
    if acct is None:
        print("Account not found.")
        return
    name = input("Enter Name: ").strip()
    if name != acct.owner_name:
        print("Name does not match account owner.")
        return
    pin = getpass("Enter PIN (hidden): ").strip()
    if not acct.verify_pin(pin):
        print("Invalid PIN! Access denied.")
        return
    print("Login successful!")
    print("1. Deposit\n2. Withdraw\n3. Add Interest (Savings only)\n4. Show Balance")
    choice = input("Choice: ").strip()
    if choice == "1":
        amt = float(input("Enter amount to deposit: ").strip())
        acct.deposit(amt)
    elif choice == "2":
        amt = float(input("Enter amount to withdraw: ").strip())
        acct.withdraw(amt)
    elif choice == "3":
        if isinstance(acct, SavingsAccount):
            acct.add_interest()
        else:
            print("Add Interest only available for SavingsAccount.")
    elif choice == "4":
        acct.show_balance()
    else:
        print("Invalid choice.")
    # save updated account state
    save_account_obj(acct)

def main():
    print("=== Secure Bank Account Management System (Python) ===")
    print("1. Create Account\n2. Login & Transaction\nChoice: ", end="")
    choice = input().strip()
    if choice == "1":
        create_account_interactive()
    elif choice == "2":
        login_and_transaction_interactive()
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
