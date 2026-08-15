import json
import os
import ssl
import threading
import time
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler


# 1. Render Port Binding (তাত্ক্ষণিক পোর্টের সমস্যা দূর করতে)
def run_dummy_server():
  port = int(os.environ.get("PORT", 10000))
  server_address = ("", port)
  httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
  httpd.serve_forever()


# ব্যাকগ্রাউন্ডে ওয়েব সার্ভার চালানো
threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. টেলিগ্রাম বট কনফিগারেশন
BOT_TOKEN = "8706612099:AAGqt8SVyB2T4Rc-mnhcwyd8JNkEO8xsUhM"
CHAT_ID = "8747470936"

price_history = []
last_signal = ""

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def send_telegram(message):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  data = json.dumps({
      "chat_id": CHAT_ID,
      "text": message,
      "parse_mode": "Markdown",
  }).encode("utf-8")
  req = urllib.request.Request(
      url, data=data, headers={"Content-Type": "application/json"}
  )
  try:
    urllib.request.urlopen(req, context=ctx, timeout=5)
  except Exception as e:
    print(f"Telegram Error: {e}")


def get_live_price():
  url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
  try:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}
    )
    res = urllib.request.urlopen(req, context=ctx, timeout=10)
    data = json.loads(res.read().decode())
    return round(float(data["price"]), 2)
  except Exception as e:
    print(f"Connection Error: {e}")
    return None


def calculate_rsi(prices, period=14):
  if len(prices) < period + 1:
    return None

  gains, losses = [], []
  for i in range(1, len(prices)):
    change = prices[i] - prices[i - 1]
    if change > 0:
      gains.append(change)
      losses.append(0)
    else:
      gains.append(0)
      losses.append(abs(change))

  avg_gain = sum(gains[-period:]) / period
  avg_loss = sum(losses[-period:]) / period

  if avg_loss == 0:
    return 100.0 if avg_gain > 0 else 50.0

  rs = avg_gain / avg_loss
  return round(100 - (100 / (1 + rs)), 2)


print("Quotex Bot Running...")

while True:
  try:
    price = get_live_price()
    if price:
      price_history.append(price)

      if len(price_history) > 30:
        price_history.pop(0)

      rsi = calculate_rsi(price_history)

      if rsi is not None:
        current_signal = "WAIT"
        if rsi <= 30:
          current_signal = "🟢 CALL (BUY)"
        elif rsi >= 70:
          current_signal = "🔴 PUT (SELL)"

        if current_signal != "WAIT" and current_signal != last_signal:
          msg = (
              f"📊 *Quotex Analysis (BTC/USD)*\n\n"
              f"💵 Price: `${price}`\n"
              f"📈 RSI: `{rsi}`\n"
              f"🎯 Signal: *{current_signal}*"
          )
          send_telegram(msg)
          last_signal = current_signal

  except Exception as e:
    print(f"Loop Error: {e}")

  time.sleep(5)
orever()

