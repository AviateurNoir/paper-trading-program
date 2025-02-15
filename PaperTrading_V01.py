import yfinance as yf
import csv
import os

class PaperTradingApp:
    def __init__(self):
        self.balance_file = "balance_and_portfolio.csv"
        self.trade_history_file = "trade_history.csv"
        self.balance = 10000.00  # Default starting balance
        self.portfolio = {}  # Dictionary to store stock symbol and quantities
        self.load_balance_and_portfolio()
        self.initialize_trade_history()

    def initialize_trade_history(self):
        if not os.path.exists(self.trade_history_file):
            with open(self.trade_history_file, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Action", "Symbol", "Price", "Quantity", "Cost/Revenue", "Balance"])

    def load_balance_and_portfolio(self):
        if os.path.exists(self.balance_file):
            with open(self.balance_file, mode="r") as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                data = list(reader)
                if data:
                    self.balance = float(data[0][0])
                    for row in data[2:]: ## 2 to skip headers
                        self.portfolio[row[0]] = int(row[1])

    def save_balance_and_portfolio(self):
        with open(self.balance_file, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Balance"])
            writer.writerow([self.balance])
            writer.writerow(["Symbol", "Quantity"])
            for symbol, quantity in self.portfolio.items():
                writer.writerow([symbol, quantity])

    def save_trade(self, action, symbol, price, quantity, cost_revenue):
        with open(self.trade_history_file, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([action, symbol, price, quantity, cost_revenue, self.balance])

    def display_menu(self):
        print("\n--- Paper Trading App ---")
        print("1. View Balance and Portfolio")
        print("2. Buy Stock")
        print("3. Sell Stock")
        print("4. Exit")

    def view_portfolio(self):
        print(f"\nCurrent Balance: ${self.balance:.2f}")
        print("Portfolio:")
        if not self.portfolio:
            print("  No stocks in portfolio.")
        else:
            for symbol, quantity in self.portfolio.items():
                print(f"  {symbol}: {quantity} shares for {self.get_stock_price(symbol)}")

    def get_stock_price(self, symbol):
        try:
            data = yf.download(symbol, period="1d", interval="1m")
            price = data["Close"].iloc[-1].item()
            if price is None:
                price = yf.Ticker(symbol).history(period="1d").iloc[-1]["Close"]
            return price
        except Exception as e:
            print(f"\nError fetching price for {symbol}: {e}")
            return None

    def buy_stock(self):
        symbol = input("Enter stock symbol to buy: ").upper()
        price = self.get_stock_price(symbol)
        print(f"Current price of {symbol}: ${price:.2f}")
        try:
            quantity = int(input(f"Enter number of shares to buy: "))
            cost = price * quantity
            if quantity <= 0:
                print("\nInvalid stock quantity.")
            elif cost > self.balance:
                print("\nInsufficient balance for this purchase.")
            else:
                self.balance -= cost
                if symbol in self.portfolio:
                    self.portfolio[symbol] += quantity
                else:
                    self.portfolio[symbol] = quantity
                print(f"\nBought {quantity} shares of {symbol} for ${cost:.2f}.")
                self.save_trade("Buy", symbol, price, quantity, -cost)
                self.save_balance_and_portfolio()
        except ValueError:
            print("\nInvalid input. Please enter valid numbers.")

    def sell_stock(self):
        symbol = input("Enter stock symbol to sell: ").upper()
        if symbol not in self.portfolio:
            print("\nYou don't own this stock.")
            return
        price = self.get_stock_price(symbol)
        if price is None:
            return
        print(f"Current price of {symbol}: ${price:.2f}")
        try:
            quantity = int(input(f"Enter number of shares to sell: "))
            if quantity > self.portfolio[symbol]:
                print("\nYou don't have enough shares to sell.")
            else:
                revenue = price * quantity
                self.balance += revenue
                self.portfolio[symbol] -= quantity
                if self.portfolio[symbol] == 0:
                    del self.portfolio[symbol]
                print(f"\nSold {quantity} shares of {symbol} for ${revenue:.2f}.")
                self.save_trade("Sell", symbol, price, quantity, revenue)
                self.save_balance_and_portfolio()
        except ValueError:
            print("\nInvalid input. Please enter valid numbers.")

    def run(self):
        while True:
            self.display_menu()
            choice = input("Enter your choice: ")
            if choice == "1":
                self.view_portfolio()
            elif choice == "2":
                self.buy_stock()
            elif choice == "3":
                self.sell_stock()
            elif choice == "4":
                print("\nExiting the app. Happy trading!")
                self.save_balance_and_portfolio()
                break
            else:
                print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    app = PaperTradingApp()
    app.run()