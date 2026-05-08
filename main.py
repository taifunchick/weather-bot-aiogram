import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional, Dict

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import aiohttp

# ========== CONFIGURATION ==========
BOT_TOKEN = "your_key"
OPENWEATHER_API_KEY = "your_key"

# ========== SETUP ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ========== FSM STATES ==========
class WeatherStates(StatesGroup):
    waiting_for_city = State()
    waiting_for_add_city = State()
    waiting_for_subscription_city = State()
    waiting_for_subscription_time = State()

# ========== USER DATA STORAGE ==========
user_favorites: Dict[int, list] = {}
user_subscriptions: Dict[int, list] = {} 

def get_favorites(user_id: int) -> list:
    if user_id not in user_favorites:
        user_favorites[user_id] = ["Moscow", "Saint Petersburg"]
    return user_favorites[user_id]

def add_favorite(user_id: int, city: str):
    favs = get_favorites(user_id)
    if city not in favs:
        favs.append(city)

def remove_favorite(user_id: int, city: str):
    favs = get_favorites(user_id)
    if city in favs:
        favs.remove(city)

def get_subscriptions(user_id: int) -> list:
    if user_id not in user_subscriptions:
        user_subscriptions[user_id] = []
    return user_subscriptions[user_id]

def add_subscription(user_id: int, city: str, hour: int, minute: int):
    subs = get_subscriptions(user_id)
    subs.append((city, hour, minute))

def remove_subscription(user_id: int, index: int):
    subs = get_subscriptions(user_id)
    if index < len(subs):
        subs.pop(index)

# ========== WEATHER FUNCTIONS ==========
async def get_current_weather(city: str) -> Optional[dict]:
    """Gets current weather"""
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "en"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logger.error(f"Weather error: {e}")
        return None

async def get_forecast(city: str, days: int = 5) -> Optional[dict]:
    """Gets daily forecast"""
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "en",
        "cnt": days * 8
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return None

def format_current_weather(data: dict) -> str:
    """Formats current weather"""
    city = data['name']
    country = data.get('sys', {}).get('country', '')
    temp = data['main']['temp']
    feels_like = data['main']['feels_like']
    humidity = data['main']['humidity']
    pressure = data['main']['pressure']
    wind_speed = data['wind']['speed']
    weather_desc = data['weather'][0]['description']
    weather_id = data['weather'][0]['id']
    
    # Weather emojis
    if weather_id >= 200 and weather_id < 300:
        emoji = "⛈️"
    elif weather_id >= 300 and weather_id < 500:
        emoji = "🌧️"
    elif weather_id >= 500 and weather_id < 600:
        emoji = "🌧️"
    elif weather_id >= 600 and weather_id < 700:
        emoji = "❄️"
    elif weather_id >= 700 and weather_id < 800:
        emoji = "🌫️"
    elif weather_id == 800:
        emoji = "☀️"
    elif weather_id == 801:
        emoji = "🌤️"
    elif weather_id == 802:
        emoji = "⛅"
    else:
        emoji = "☁️"
    
    return f"""
{emoji} *{city}, {country}*

🌡️ *Temperature:* {temp:.1f}°C (feels like {feels_like:.1f}°C)
📝 *Conditions:* {weather_desc.capitalize()}
💧 *Humidity:* {humidity}%
💨 *Pressure:* {pressure} hPa
🌬️ *Wind:* {wind_speed:.1f} m/s

📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""

def format_forecast(data: dict) -> str:
    """Formats 5-day forecast"""
    city = data['city']['name']
    country = data['city']['country']
    
    daily_forecasts = {}
    for forecast in data['list']:
        date = forecast['dt_txt'].split()[0]
        if date not in daily_forecasts:
            daily_forecasts[date] = []
        daily_forecasts[date].append(forecast)
    
    result = f"📅 *5-Day Weather Forecast*\n🏙️ *{city}, {country}*\n\n"
    
    for i, (date, forecasts) in enumerate(list(daily_forecasts.items())[:5]):
        day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%A')
        day_short = day_name[:3].upper()
        
        temps = [f['main']['temp'] for f in forecasts]
        temp_max = max(temps)
        temp_min = min(temps)
        
        weather_ids = [f['weather'][0]['id'] for f in forecasts]
        main_weather_id = max(set(weather_ids), key=weather_ids.count)
        
        # Emoji for forecast
        if main_weather_id == 800:
            weather_emoji = "☀️"
        elif main_weather_id == 801:
            weather_emoji = "🌤️"
        elif main_weather_id == 802:
            weather_emoji = "⛅"
        elif main_weather_id >= 803:
            weather_emoji = "☁️"
        elif main_weather_id >= 600:
            weather_emoji = "❄️"
        elif main_weather_id >= 500:
            weather_emoji = "🌧️"
        else:
            weather_emoji = "🌡️"
        
        date_str = f"{date.split('-')[2]}.{date.split('-')[1]}"
        result += f"*{date_str} ({day_short})* {weather_emoji} {temp_max:.0f}° / {temp_min:.0f}°\n"
    
    return result

# ========== 50+ INTERESTING WEATHER FACTS ==========
WEATHER_FACTS = [
    "🏔️ The coldest place on Earth is Antarctica. The temperature was recorded at -89.2°C!",
    "🔥 The hottest temperature on Earth +56.7°C was recorded in Death Valley, USA.",
    "⚡ Lightning can heat the air to 30,000°C — 5 times hotter than the Sun's surface!",
    "🌪️ In 1999, the strongest tornado wind was recorded in Oklahoma — 512 km/h.",
    "❄️ The largest snowflake was recorded in 1887 in Montana — 38 cm in diameter!",
    "🌈 Rainbows can only be seen when the sun is behind you.",
    "🌧️ The heaviest rain in 1 minute fell in 1956 in Maryland — 31.2 mm.",
    "🌊 Typhoons, hurricanes, and cyclones are the same phenomenon, just in different regions.",
    "📏 Each minute of a thunderstorm produces about 6,000 lightning strikes!",
    "🎨 Clouds have weight: an average cumulus cloud weighs about 500 tons!",
    "🏜️ The driest place on Earth is the Atacama Desert in Chile. No rain fell there for 400 years!",
    "🌧️ Snow sometimes falls in the Sahara Desert — last time was in 2018.",
    "⚡ A single lightning bolt contains enough energy to power 100 light bulbs for a whole day.",
    "🌫️ Fog is just a cloud that has descended to the ground.",
    "❄️ Snow can fall at temperatures up to +5°C if the air is humid enough.",
    "🌡️ The most dramatic temperature change was recorded in the USA: from +7°C to -37°C in 24 hours!",
    "🏔️ The temperature at the summit of Everest never rises above 0°C.",
    "🌪️ Inside a tornado, the pressure is so low that houses explode from within.",
    "☀️ In one second, the Sun releases more energy than humanity has in its entire history.",
    "🌙 The Moon has no atmosphere, so there's no weather, but temperatures range from -173°C to +127°C.",
    "🎵 Hurricanes have been named since 1953. The list of names repeats every 6 years.",
    "🏠 The rainiest place on Earth is Mawsynram village in India: 11,872 mm of rain per year!",
    "🌊 The eye of a hurricane is a zone of complete calm in the center of the storm.",
    "❄️ Snow reflects up to 90% of sunlight — that's why you can get sunburned in the mountains.",
    "🌈 A double rainbow occurs when light reflects twice inside a water droplet.",
    "🌡️ Atmospheric pressure changes with weather: high pressure means good weather, low pressure means rain.",
    "🌧️ Acid rain can be caused by volcanic eruptions or air pollution.",
    "☁️ Cirrus clouds consist of ice crystals and indicate changing weather.",
    "🌊 El Niño is a phenomenon where the Pacific Ocean warms, causing abnormal weather.",
    "❄️ It snows on Mars too, but it consists of carbon dioxide — dry ice.",
    "⚡ Ball lightning is a rare phenomenon that still has no scientific explanation.",
    "🌧️ In 2017, it rained red water in India — it was dust from the Sahara Desert.",
    "🏔️ Kamchatka has a valley of geysers where fountains of boiling water erupt from underground.",
    "❄️ About 31 million tons of cosmic dust fall to Earth every year.",
    "🌡️ The hottest month on Earth on average is July, the coldest is January.",
    "🌊 Super Typhoon Haiyan in 2013 was the most powerful on record.",
    "⚡ About 50 lightning strikes occur in Earth's atmosphere every second.",
    "🌫️ The Great Smog of London in 1952 killed about 12,000 people.",
    "❄️ Antarctica is the largest desert in the world, though 99% covered in ice.",
    "☀️ The polar day lasts 6 months at the North Pole and 6 months at the South Pole.",
    "🌧️ About 16 billion tons of water fall to Earth as precipitation every hour.",
    "🌪️ The smallest tornado was only 2 meters wide but destroyed several houses.",
    "❄️ Snowflakes always have 6 branches due to the crystalline structure of ice.",
    "🌊 A tsunami can move at airplane speed — up to 800 km/h in the open ocean.",
    "☁️ Thunderclouds can reach heights of 15–20 kilometers.",
    "🔥 Dust storms in Australia raise red dust from the desert.",
    "🌡️ In Siberia, winter temperatures can drop to -70°C and summer to +40°C.",
    "⚡ One lightning strike can provide electricity for 10 homes for a month.",
    "🌧️ Animal rain is a real phenomenon when a tornado lifts animals with water.",
    "🌊 TAIFUN is the best developer.",
]

# ========== WIDGETS AND ADDITIONAL FUNCTIONS ==========
def get_weather_tip() -> str:
    """Weather tip"""
    tips = [
        "☂️ If pressure drops sharply — expect rain or storm!",
        "🧥 When humidity is above 70%, cold feels stronger, dress warmer.",
        "🕶️ UV index above 3 — sunglasses needed.",
        "🌡️ The most comfortable temperature for humans is 21-23°C.",
        "💧 When air humidity is low, drink more water — dehydration is sneaky.",
        "🏠 Set your AC to 22-24°C — the difference from outside shouldn't exceed 8°C.",
        "🧣 Your neck and head lose the most heat — cover them in cold weather.",
        "☀️ Tanning is dangerous from 11:00 AM to 4:00 PM — the sun is most active.",
    ]
    return random.choice(tips)

def get_weather_comparison(city: str = None) -> str:
    """Weather comparison with interesting places"""
    comparisons = [
        "📊 Winter temperature in Moscow is about the same as on Mars!",
        "🏔️ Summer in Antarctica is warmer than winter in Norilsk.",
        "🔥 The Sahara Desert at night is colder than Moscow in winter.",
        "🌧️ London receives less rain per year than Novosibirsk.",
        "❄️ The lowest temperature in Russia (-71°C) was recorded in Oymyakon.",
    ]
    return random.choice(comparisons)

def get_moon_phase() -> str:
    """Moon phase"""
    phases = [
        "🌑 New Moon — the night will be dark.",
        "🌒 Waxing Crescent — the moon is growing.",
        "🌓 First Quarter — half the moon is visible.",
        "🌔 Waxing Gibbous — full moon is coming soon.",
        "🌕 Full Moon — the moon is bright all night.",
        "🌖 Waning Gibbous — nights are getting darker.",
        "🌗 Last Quarter — half moon visible.",
        "🌘 Waning Crescent — new moon soon.",
    ]
    return random.choice(phases)

def get_uv_index_recommendation(uv_index: int = None) -> str:
    """UV index recommendation"""
    if uv_index is None:
        uv_index = random.randint(0, 11)
    
    if uv_index <= 2:
        return f"☀️ UV index {uv_index}: Low. Safe for outdoor activities."
    elif uv_index <= 5:
        return f"🟡 UV index {uv_index}: Moderate. Use SPF 30 sunscreen."
    elif uv_index <= 7:
        return f"🟠 UV index {uv_index}: High. Sunscreen, hat, and sunglasses needed."
    elif uv_index <= 10:
        return f"🔴 UV index {uv_index}: Very high. Avoid going out from 11 AM to 4 PM."
    else:
        return f"☠️ UV index {uv_index}: Extreme! Stay in the shade."

# ========== KEYBOARDS ==========
def get_main_keyboard() -> InlineKeyboardMarkup:
    """Main menu"""
    buttons = [
        [InlineKeyboardButton(text="🌤️ Current Weather", callback_data="weather_now")],
        [InlineKeyboardButton(text="📅 5-Day Forecast", callback_data="weather_5days")],
        [InlineKeyboardButton(text="⭐ Favorite Cities", callback_data="favorites")],
        [InlineKeyboardButton(text="🔔 Subscriptions", callback_data="subscriptions")],
        [InlineKeyboardButton(text="📍 Add City", callback_data="add_city_from_menu")],
        [InlineKeyboardButton(text="🎲 Random Fact", callback_data="random_fact")],
        [InlineKeyboardButton(text="💡 Daily Tip", callback_data="daily_tip")],
        [InlineKeyboardButton(text="🌍 Weather Widget", callback_data="widget")],
        [InlineKeyboardButton(text="ℹ️ Help", callback_data="help")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_city_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Keyboard with favorite cities"""
    favs = get_favorites(user_id)
    buttons = []
    for city in favs[:8]:
        buttons.append([InlineKeyboardButton(text=city, callback_data=f"select_city_{city}")])
    buttons.append([InlineKeyboardButton(text="➕ Add New City", callback_data="add_city")])
    buttons.append([InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ========== COMMANDS ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🌤️ *Taifun Weather Bot*\n\n"
        "I show weather in any city!\n\n"
        "*How to use:*\n"
        "• Just send a city name\n"
        "• Or use the menu buttons\n"
        "• Add cities to favorites\n\n"
        "🌍 *New features:*\n"
        "• Weather tips\n"
        "• Interesting facts\n"
        "• Comparisons with other places",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📚 *Commands & Features*\n\n"
        "/start - Start the bot\n"
        "/help - This help\n\n"
        "*Inline buttons:*\n"
        "🌤️ Current Weather\n"
        "📅 5-Day Forecast\n"
        "⭐ Favorite Cities\n"
        "🔔 Subscriptions\n"
        "📍 Add City\n"
        "🎲 Random Weather Fact\n"
        "💡 Daily Tip\n"
        "🌍 Weather Widget\n\n"
        "*The bot is free and ad-free!*",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message()
async def handle_message(message: types.Message, state: FSMContext):
    """Handle messages (cities)"""
    current_state = await state.get_state()
    
    if current_state == WeatherStates.waiting_for_add_city.state:
        city = message.text.strip()
        add_favorite(message.from_user.id, city)
        await message.answer(f"✅ City *{city}* added to favorites!", parse_mode="Markdown")
        await state.clear()
        await cmd_start(message)
    
    elif current_state == WeatherStates.waiting_for_city.state:
        city = message.text.strip()
        await show_weather(message, city)
        await state.clear()
    
    elif current_state == WeatherStates.waiting_for_subscription_city.state:
        await state.update_data(sub_city=message.text.strip())
        await message.answer("🕐 Enter hour (0-23):")
        await state.set_state(WeatherStates.waiting_for_subscription_time)
    
    elif current_state == WeatherStates.waiting_for_subscription_time.state:
        try:
            hour = int(message.text.strip())
            if 0 <= hour <= 23:
                data = await state.get_data()
                city = data.get('sub_city')
                add_subscription(message.from_user.id, city, hour, 0)
                await message.answer(f"✅ Subscription for *{city}* at {hour}:00 created!", parse_mode="Markdown")
                await state.clear()
                await cmd_start(message)
            else:
                await message.answer("❌ Hour must be between 0 and 23")
        except ValueError:
            await message.answer("❌ Enter a number between 0 and 23")
    
    else:
        await show_weather(message, message.text.strip())

async def show_weather(message: types.Message, city: str):
    """Show weather for city"""
    await message.answer(f"🔍 Searching for weather in *{city}*...", parse_mode="Markdown")
    
    data = await get_current_weather(city)
    
    if not data:
        await message.answer(f"❌ City *{city}* not found. Check the name.", parse_mode="Markdown")
        return
    
    weather_text = format_current_weather(data)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Add to Favorites", callback_data=f"add_fav_{city}")],
        [InlineKeyboardButton(text="📅 5-Day Forecast", callback_data=f"forecast_{city}")],
        [InlineKeyboardButton(text="🔙 Main Menu", callback_data="back_to_main")]
    ])
    
    await message.answer(weather_text, parse_mode="Markdown", reply_markup=keyboard)

# ========== CALLBACK HANDLERS ==========
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text("🌤️ *Main Menu*", parse_mode="Markdown")
    await callback.message.edit_reply_markup(reply_markup=get_main_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    await cmd_help(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "weather_now")
async def weather_now_callback(callback: CallbackQuery):
    favs = get_favorites(callback.from_user.id)
    if favs:
        await callback.message.edit_text("🌆 *Select a city:*", parse_mode="Markdown")
        await callback.message.edit_reply_markup(reply_markup=get_city_keyboard(callback.from_user.id))
    else:
        await callback.message.edit_text(
            "📝 *No favorite cities*\n\nSend a city name in chat or click 'Add City'",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    await callback.answer()

@dp.callback_query(F.data == "weather_5days")
async def weather_5days_callback(callback: CallbackQuery):
    favs = get_favorites(callback.from_user.id)
    if favs:
        buttons = []
        for city in favs[:8]:
            buttons.append([InlineKeyboardButton(text=city, callback_data=f"forecast_{city}")])
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text("📅 *Select a city for forecast:*", parse_mode="Markdown")
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await callback.message.edit_text("📝 *No favorite cities*", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "favorites")
async def favorites_callback(callback: CallbackQuery):
    favs = get_favorites(callback.from_user.id)
    if favs:
        cities_list = "\n".join([f"⭐ {city}" for city in favs])
        await callback.message.edit_text(
            f"*Favorite Cities:*\n\n{cities_list}\n\nSelect a city:",
            parse_mode="Markdown",
            reply_markup=get_city_keyboard(callback.from_user.id)
        )
    else:
        await callback.message.edit_text("📝 *No favorite cities*", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "subscriptions")
async def subscriptions_callback(callback: CallbackQuery):
    subs = get_subscriptions(callback.from_user.id)
    if subs:
        text = "*🔔 Your Subscriptions:*\n\n"
        for i, (city, hour, minute) in enumerate(subs):
            text += f"{i+1}. {city} at {hour:02d}:{minute:02d}\n"
        await callback.message.edit_text(text, parse_mode="Markdown")
    else:
        await callback.message.edit_text(
            "🔔 *No active subscriptions*\n\nSend /subscribe <city> to create one",
            parse_mode="Markdown"
        )
    await callback.answer()
    await callback.message.answer("🔙 Returning...", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "add_city_from_menu")
async def add_city_from_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✏️ *Enter the city name to add to favorites:*\n\n"
        "Example: `London`, `Tokyo`, `Paris`",
        parse_mode="Markdown"
    )
    await state.set_state(WeatherStates.waiting_for_add_city)
    await callback.answer()

@dp.callback_query(F.data == "add_city")
async def add_city_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✏️ *Enter the city name:*",
        parse_mode="Markdown"
    )
    await state.set_state(WeatherStates.waiting_for_add_city)
    await callback.answer()

@dp.callback_query(F.data == "random_fact")
async def random_fact_callback(callback: CallbackQuery):
    fact = random.choice(WEATHER_FACTS)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Another Fact", callback_data="random_fact")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(f"🎲 *Interesting Weather Fact:*\n\n{fact}", parse_mode="Markdown")
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "daily_tip")
async def daily_tip_callback(callback: CallbackQuery):
    tip = get_weather_tip()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Another Tip", callback_data="daily_tip")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(f"💡 *Daily Tip:*\n\n{tip}", parse_mode="Markdown")
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "widget")
async def widget_callback(callback: CallbackQuery):
    tip = get_weather_tip()
    comparison = get_weather_comparison()
    moon = get_moon_phase()
    uv = get_uv_index_recommendation()
    
    widget_text = f"""
🌍 *Weather Widget*

💡 {tip}
📊 {comparison}
🌙 {moon}
{uv}

*Random Fact:*
{random.choice(WEATHER_FACTS[:10])}
"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Refresh Widget", callback_data="widget")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(widget_text, parse_mode="Markdown")
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith("select_city_"))
async def select_city_callback(callback: CallbackQuery):
    city = callback.data.replace("select_city_", "")
    data = await get_current_weather(city)
    
    if data:
        weather_text = format_current_weather(data)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📅 Forecast", callback_data=f"forecast_{city}")],
            [InlineKeyboardButton(text="❌ Remove", callback_data=f"remove_fav_{city}")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="favorites")]
        ])
        await callback.message.edit_text(weather_text, parse_mode="Markdown")
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await callback.answer("Error getting weather", show_alert=True)
    await callback.answer()

@dp.callback_query(F.data.startswith("forecast_"))
async def forecast_callback(callback: CallbackQuery):
    city = callback.data.replace("forecast_", "")
    await callback.answer("📅 Loading forecast...")
    
    data = await get_forecast(city)
    
    if data:
        forecast_text = format_forecast(data)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌤️ Current Weather", callback_data=f"select_city_{city}")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="weather_5days")]
        ])
        await callback.message.edit_text(forecast_text, parse_mode="Markdown")
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await callback.message.edit_text(f"❌ Could not get forecast for {city}")
    await callback.answer()

@dp.callback_query(F.data.startswith("add_fav_"))
async def add_fav_callback(callback: CallbackQuery):
    city = callback.data.replace("add_fav_", "")
    add_favorite(callback.from_user.id, city)
    await callback.answer(f"✅ {city} added to favorites!", show_alert=True)

@dp.callback_query(F.data.startswith("remove_fav_"))
async def remove_fav_callback(callback: CallbackQuery):
    city = callback.data.replace("remove_fav_", "")
    remove_favorite(callback.from_user.id, city)
    await callback.answer(f"❌ {city} removed from favorites", show_alert=True)
    await favorites_callback(callback)

# ========== RUN ==========
async def main():
    print("🌤️ Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())