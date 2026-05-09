# 🌤️ Taifun Weather Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.14%2B-blue?style=for-the-badge&logo=python)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-00b8ff?style=for-the-badge&logo=telegram)
![OpenWeatherMap](https://img.shields.io/badge/OpenWeatherMap-API-eb6e4b?style=for-the-badge)

**Your personal meteorologist in Telegram**

[📦 Installation](#-installation) | [🚀 Run](#-run) | [📖 Features](#-features) | [📸 Screenshots](#-screenshots)

</div>

---

## 📖 About

**Taifun Weather Bot** — Telegram bot for current weather, 5-day forecast, daily subscriptions, weather facts, and tips.

---

## 🛠️ Tech Stack

- Python 3.9+
- Aiogram 3.x
- OpenWeatherMap API
- aiohttp
- asyncio

---

## 📦 Installation

```bash
# Clone repo
git clone https://github.com/yourusername/taifun-weather-bot.git
cd taifun-weather-bot

# Create venv
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install deps
pip install aiogram aiohttp
```

## Configuration
Edit bot.py:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN"          # From @BotFather
OPENWEATHER_API_KEY = "YOUR_API_KEY"  # From OpenWeatherMap
```

## 🚀 Run
```bash
python main.py
```
## 📖 Features

| Button | Action |
|--------|--------|
| 🌤️ Current Weather | Real-time weather |
| 📅 5-Day Forecast | Daily forecast |
| ⭐ Favorite Cities | Saved cities list |
| 🔔 Subscriptions | Daily auto updates |
| 📍 Add City | Add to favorites |
| 🎲 Random Fact | Weather trivia |
| 💡 Daily Tip | Weather advice |
| 🌍 Weather Widget | All-in-one dashboard |
| ℹ️ Help | Command list |

### Subscriptions Setup

1. Click **🔔 Subscriptions**
2. Click **➕ Add Subscription**
3. Choose city from favorites
4. Pick time (8:00, 9:00, 10:00, 12:00, 15:00, 18:00, 20:00, 21:00)
5. Done! Daily updates enabled

---

## 📸 Screenshots

| Screenshot | Link |
|------------|------|
| Main Menu | `https://screenshots/main_menu.png` |
| Current Weather | `https://screenshots/current_weather.png` |
| 5-Day Forecast | `https://screenshots/forecast.png` |
| Favorite Cities | `https://screenshots/favorites.png` |
| Subscriptions | `https://screenshots/subscriptions.png` |
| Random Fact | `https://screenshots/random_fact.png` |
| Daily Tip | `https://screenshots/daily_tip.png` |
| Weather Widget | `https://screenshots/widget.png` |
| Daily Notification | `https://screenshots/notification.png` |

---

## ⚠️ Limits (Free OpenWeatherMap)

- 60 requests/minute
- 1,000,000 requests/month
- 5-day forecast (3-hour steps)
