# app.py

import streamlit as st
from datetime import datetime
import pyotp
import time
from NorenRestApiPy.NorenApi import NorenApi

# --- HARDCODED CREDENTIALS (change to secrets if deploying) ---
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

    def login(self):
        """Login to Shoonya API"""
        try:
            totp = pyotp.TOTP(Config.TWO_FA_SECRET).now()
            ret = self.api.login(userid=Config.USER_ID, password=Config.PASSWORD, twoFA=totp,
                                 vendor_code=Config.VENDOR_CODE, api_secret=Config.API_SECRET, imei=Config.IMEI)
            if ret and ret.get('stat') == 'Ok':
                self.logged_in = True
                time.sleep(1)
                return True, "✅ Login Successful!"
            else:
                return False, f"❌ Login Failed: {ret}"
        except Exception as e:
            return False, f"❌ Login Error: {str(e)}"

    def _get_instrument_details(self, symbol):
        exchange = "NSE"
        search_text = symbol.upper()
        try:
            result = self.api.searchscrip(exchange=exchange, searchtext=search_text)
            if result and result.get('stat') == 'Ok' and result.get('values'):
                for instrument in result['values']:
                    if instrument.get('tsym') == f"{search_text}-EQ":
                        return instrument
            return None
        except Exception as e:
            return None

    def place_buy_order(self, symbol, quantity, order_type, limit_price=0):
        if not self.logged_in:
            return "❌ Please login first!"

        instrument = self._get_instrument_details(symbol)
        if not instrument:
            return f"❌ Symbol '{symbol}' not found in NSE."

        trading_symbol = instrument['tsym']
        price_type = "MKT" if order_type == 'MKT' else "LMT"
        price = str(limit_price) if order_type == 'LMT' else "0"

        try:
            result = self.api.place_order(
                buy_or_sell='B',
                product_type='C',
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
            if result and result.get('stat') == 'Ok':
                return f"✅ Buy Order Placed! Order Number: {result.get('norenordno', 'N/A')}"
            elif result:
                return f"❌ Order Failed: {result.get('emsg', 'Unknown error')}"
            else:
                return "❌ Order placement failed. No response from API."
        except Exception as e:
            return f"❌ Exception while placing order: {e}"

# --- Streamlit UI ---

st.set_page_config(page_title="Shoonya Trading UI", page_icon="📈")
st.title("📈 Shoonya Trading App (Ultra Simple UI)")

if 'trader' not in st.session_state:
    st.session_state.trader = ShoonyaTrader()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Login button
if not st.session_state.logged_in:
    if st.button("🔐 Login to Shoonya"):
        success, msg = st.session_state.trader.login()
        st.session_state.logged_in = success
        st.info(msg)

if st.session_state.logged_in:
    st.success("✅ Logged in!")

    symbol = st.text_input("Enter Stock Symbol (e.g., RELIANCE)").upper()
    quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
    order_type = st.radio("Order Type", options=['MKT', 'LMT'])

    limit_price = 0
    if order_type == 'LMT':
        limit_price = st.number_input("Limit Price (₹)", min_value=0.0, value=0.0)

    if st.button("🚀 Place Buy Order"):
        msg = st.session_state.trader.place_buy_order(symbol, quantity, order_type, limit_price)
        if msg.startswith("✅"):
            st.success(msg)
        else:
            st.error(msg)
