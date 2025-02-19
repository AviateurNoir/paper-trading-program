import yfinance as yf
import pandas as pd
import os
import streamlit as st


class PaperTradingApp:
    def __init__(self):
        self.portfolio_file = "portfolio.csv"
        self.balance_file = "balance.csv"
        self.trade_history_file = "trade_history.csv"
        self.balance = 10000.00  # Default starting balance
        self.portfolio = {}  # Dictionary to store stock symbol and quantities
        self.load_balance_and_portfolio()
        self.initialize_trade_history()

    def initialize_trade_history(self):
        if not os.path.exists(self.trade_history_file):
            df = pd.DataFrame(columns=["Action", "Symbol", "Price", "Quantity", "Cost/Revenue", "Balance"])
            df.to_csv(self.trade_history_file, index=False)

    def load_balance_and_portfolio(self):
        # Load balance
        if os.path.exists(self.balance_file):
            balance_df = pd.read_csv(self.balance_file)
            if not balance_df.empty:
                self.balance = float(balance_df.iloc[0]['Balance'])
        
        # Load portfolio
        if os.path.exists(self.portfolio_file):
            portfolio_df = pd.read_csv(self.portfolio_file)
            if not portfolio_df.empty:
                self.portfolio = dict(zip(portfolio_df['Symbol'], portfolio_df['Quantity']))
        

    def save_balance_and_portfolio(self):
        # Save balance to separate file
        balance_df = pd.DataFrame({'Balance': [round(self.balance, 2)]})
        balance_df.to_csv(self.balance_file, index=False)
        
        # Save portfolio to separate file
        if self.portfolio:
            portfolio_df = pd.DataFrame({
                'Symbol': list(self.portfolio.keys()),
                'Quantity': list(self.portfolio.values())
            })
            portfolio_df.to_csv(self.portfolio_file, index=False)

    def save_trade(self, action, symbol, price, quantity, cost_revenue):
        new_trade = pd.DataFrame({
            'Action': [action],
            'Symbol': [symbol],
            'Price': [round(price, 2)],
            'Quantity': [quantity],
            'Cost/Revenue': [round(cost_revenue, 2)],
            'Balance': [round(self.balance, 2)]
        })
        
        if os.path.exists(self.trade_history_file):
            trades_df = pd.read_csv(self.trade_history_file)
            trades_df = pd.concat([trades_df, new_trade], ignore_index=True)
        else:
            trades_df = new_trade
        
        trades_df.to_csv(self.trade_history_file, index=False)

    def get_stock_price(self, symbol): ### need to figurre out why this use to work but now it doesn't
        try:                            ### or use beautiful soup to get the price (web scraping)
            data = yf.download(symbol, period="1d", interval="1m")
            price = data["Close"].iloc[-1].item()
            if price is None:
                price = yf.Ticker(symbol).history(period="1d").iloc[-1]["Close"]
            return price
        except:
            try:
                price = yf.Ticker(symbol).history(period="1d").iloc[-1]["Close"]
            except Exception as e:
                print(f"\nError fetching price for {symbol}: {e}")
                return None
            return price

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
        st.title("Paper Trading App")
        
        # Sidebar for navigation
        page = st.sidebar.selectbox(
            "Navigation",
            ["View Portfolio", "Buy Stock", "Sell Stock", "Trade History"]  # Added Trade History
        )
        
        if page == "View Portfolio":
            st.header("Portfolio")
            
            # Calculate portfolio value first
            portfolio_value = 0
            if self.portfolio:
                portfolio_data = []
                for symbol, quantity in self.portfolio.items():
                    price = self.get_stock_price(symbol)
                    value = price * quantity if price else 0
                    portfolio_value += value
                    portfolio_data.append({
                        'Symbol': symbol,
                        'Quantity': quantity,
                        'Price/Share': round(price, 2),
                        'Total Value': round(value, 2)
                    })
            
            # Display account metrics in columns
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Cash Balance", f"${self.balance:.2f}")
            with col2:
                st.metric("Portfolio Value", f"${portfolio_value:.2f}")
            with col3:
                st.metric("Total Account Value", f"${(self.balance + portfolio_value):.2f}")
            
            # Display portfolio details
            if not self.portfolio:
                st.info("No stocks in portfolio.")
            else:
                df = pd.DataFrame(portfolio_data)
                st.dataframe(df, use_container_width=True)

        elif page == "Buy Stock":
            st.header("Buy Stock")
            symbol = st.text_input("Stock Symbol").upper()
            if symbol:
                price = self.get_stock_price(symbol)
                if price:
                    st.write(f"Current price: ${price:.2f}")
                    quantity = st.number_input("Number of shares", min_value=1, step=1)
                    cost = price * quantity
                    if st.button("Buy"):
                        if cost > self.balance:
                            st.error("Insufficient balance for this purchase.")
                        else:
                            self.balance -= cost
                            if symbol in self.portfolio:
                                self.portfolio[symbol] += quantity
                            else:
                                self.portfolio[symbol] = quantity
                            self.save_trade("Buy", symbol, price, quantity, -cost)
                            self.save_balance_and_portfolio()
                            st.success(f"Bought {quantity} shares of {symbol} for ${cost:.2f}")
        
        elif page == "Sell Stock":
            st.header("Sell Stock")
            if not self.portfolio:
                st.info("No stocks in portfolio to sell.")
            else:
                symbol = st.selectbox("Select Stock", list(self.portfolio.keys()))
                price = self.get_stock_price(symbol)
                if price:
                    st.write(f"Current price: ${price:.2f}")
                    quantity = st.number_input("Number of shares", 
                                             min_value=1, 
                                             max_value=self.portfolio[symbol],
                                             step=1)
                    if st.button("Sell"):
                        revenue = price * quantity
                        self.balance += revenue
                        self.portfolio[symbol] -= quantity
                        if self.portfolio[symbol] == 0:
                            del self.portfolio[symbol]
                        self.save_trade("Sell", symbol, price, quantity, revenue)
                        self.save_balance_and_portfolio()
                        st.success(f"Sold {quantity} shares of {symbol} for ${revenue:.2f}")

        elif page == "Trade History":
            st.header("Trade History")
            if os.path.exists(self.trade_history_file):
                trades_df = pd.read_csv(self.trade_history_file)
                if not trades_df.empty:
                    st.dataframe(trades_df, use_container_width=True)
                else:
                    st.info("No trade history available.")

if __name__ == "__main__":
    app = PaperTradingApp()
    app.run()