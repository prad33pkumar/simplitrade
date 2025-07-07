# Shoonya API - Stock Buyer (Validated)
# Note: This is for educational purposes. Test thoroughly before live trading.
# WARNING: This version contains hardcoded credentials and is NOT secure for sharing.

# Install required packages
!pip install NorenRestApiPy pyotp

from datetime import datetime
import pyotp
import time

# Import the NorenApi class
from NorenRestApiPy.NorenApi import NorenApi

# --- WARNING: HARDCODED CREDENTIALS ---
class Config:
    USER_ID = "FA58652"
    PASSWORD = "India@123456"
    TWO_FA_SECRET = "Q472J4S3QVWSG74RL5KG3BTW4TAGD33M"
    VENDOR_CODE = "FA58652_U"
    API_SECRET = "cefd822ceab79bd453cb86a6e43df0ef"
    IMEI = "abc1234"
# ------------------------------------

class ShoonyaTrader:
    def __init__(self):
        self.api = NorenApi(host='https://api.shoonya.com/NorenWClientTP/',
                            websocket='wss://api.shoonya.com/NorenWSTP/')
        self.logged_in = False

    def login(self, userid, password, twoFA, vendor_code, api_secret, imei):
        """Login to Shoonya API"""
        try:
            totp = pyotp.TOTP(twoFA).now()
            ret = self.api.login(userid=userid, password=password, twoFA=totp,
                                 vendor_code=vendor_code, api_secret=api_secret, imei=imei)
            if ret and ret.get('stat') == 'Ok':
                print("✅ Login Successful!")
                self.logged_in = True
                print("...allowing 1 second for session to stabilize...")
                time.sleep(1)
                return True
            else:
                print(f"❌ Login Failed: {ret}")
                return False
        except Exception as e:
            print(f"❌ Login Error: {str(e)}")
            return False

    def _get_instrument_details(self, symbol):
        """
        Searches for a stock symbol to validate it and get its token.
        """
        print(f"🔍 Validating stock symbol '{symbol}'...")
        exchange = "NSE"
        search_text = symbol.upper()
        try:
            result = self.api.searchscrip(exchange=exchange, searchtext=search_text)
            if result and result.get('stat') == 'Ok' and result.get('values'):
                for instrument in result['values']:
                    # Find the exact match for the equity instrument (e.g., 'RELIANCE-EQ')
                    if instrument.get('tsym') == f"{search_text}-EQ":
                        print(f"✅ Symbol validated: {instrument['tsym']}")
                        return instrument

            print(f"❌ Could not find a valid NSE equity symbol for '{symbol}'. Please check the symbol.")
            return None
        except Exception as e:
            print(f"❌ An exception occurred during symbol search: {e}")
            return None


    def place_buy_order(self, symbol, quantity, order_type, limit_price=0):
        """
        Validates the symbol and places a buy order for a stock.
        """
        if not self.logged_in:
            print("❌ Please login first!")
            return

        # --- FIX: Validate the instrument before proceeding ---
        instrument = self._get_instrument_details(symbol)
        if not instrument:
            return # Stop if the symbol is invalid

        trading_symbol = instrument['tsym']

        print("\n" + "="*50)
        print(f"🚀 Preparing to buy {quantity} shares of {trading_symbol}")

        # Set order type and price
        price_type = ""
        price = "0"
        if order_type == 'LMT':
            price_type = "LMT"
            price = str(limit_price)
            print(f"   Order Type: Limit @ ₹{price}")
        elif order_type == 'MKT':
            price_type = "MKT"
            print("   Order Type: Market")
        else:
            print("❌ Invalid order type specified.")
            return

        try:
            # --- Place the buy order ---
            result = self.api.place_order(
                buy_or_sell='B',          # 'B' for Buy
                product_type='C',         # 'C' for CNC (Delivery)
                exchange=instrument['exch'],
                tradingsymbol=trading_symbol,
                quantity=str(quantity),
                discloseqty='0',
                price_type=price_type,
                price=price,
                trigger_price='0',
                retention='DAY',
                remarks='Stock_Buy_Bot'
            )

            # --- FIX: Added a check to ensure 'result' is not None ---
            if result and result.get('stat') == 'Ok':
                order_num = result.get('norenordno', 'N/A')
                print(f"✅ Buy Order Placed Successfully for {trading_symbol}!")
                print(f"   Order Number: {order_num}")
            elif result:
                error_msg = result.get('emsg', 'Unknown error')
                print(f"❌ Order Failed for {trading_symbol}: {error_msg}")
            else:
                print(f"❌ Order placement failed. API did not return a response.")

        except Exception as e:
            print(f"❌ An exception occurred while placing the order: {e}")

        print("="*50)

def main():
    print("🏛️ Shoonya API - Stock Buyer (Validated)")
    print("=" * 50)
    trader = ShoonyaTrader()

    if not trader.login(Config.USER_ID, Config.PASSWORD, Config.TWO_FA_SECRET,
                        Config.VENDOR_CODE, Config.API_SECRET, Config.IMEI):
        print("❌ Halting script due to login failure.")
        return

    try:
        # Get Stock Symbol (e.g., RELIANCE or BHARTIARTL)
        symbol_input = input("Enter the stock symbol (e.g., RELIANCE): ").strip().upper()
        if not symbol_input:
            print("❌ Stock symbol cannot be empty.")
            return

        quantity_input = input(f"Enter quantity for {symbol_input}: ")
        quantity = int(quantity_input)
        if quantity <= 0:
            print("❌ Quantity must be greater than zero.")
            return

        order_type_input = input("Enter order type (1 for Market, 2 for Limit): ")
        order_type = ""
        limit_price = 0

        if order_type_input == '1':
            order_type = 'MKT'
        elif order_type_input == '2':
            order_type = 'LMT'
            price_input = input("Enter the limit price: ")
            limit_price = float(price_input)
            if limit_price <= 0:
                print("❌ Limit price must be greater than zero.")
                return
        else:
            print("❌ Invalid choice for order type. Please enter 1 or 2.")
            return

        trader.place_buy_order(symbol_input, quantity, order_type, limit_price)

    except ValueError:
        print("❌ Invalid input. Please enter a valid number for quantity or price.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

    print("\n👋 Script finished.")


if __name__ == "__main__":
    print("⚠️ IMPORTANT DISCLAIMER ⚠️")
    print("This script is for educational purposes and executes trades based on your input.")
    print("You are responsible for all trades.")
    print("="*50 + "\n")
    main()
