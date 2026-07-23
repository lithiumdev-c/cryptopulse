import asyncio
import json
import typing
from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery, LabeledPrice, Message,PreCheckoutQuery
from aiogram.filters import CommandObject, CommandStart, Command

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import app.keyboards as kb

import aiohttp
from dotenv import load_dotenv
import os
import logging

import app.database.requests as rq

class WatchlistStates(StatesGroup):
    add_symbol = State()

TIER_LIMITS = {
    'free': {
        'watchlist_limit': 3,
        'min_threshold': 1_000_000,
    },
    'premium': {        
        'watchlist_limit': 50,
        'min_threshold': 5000,
    }
}                                                                                                                                                                                                                                                                                                           

BYBIT_WS_URL = "wss://stream.bybit.com/v5/public/linear"
BYBIT_API_URL = "https://api.bybit.com/v5/market/tickers"

logger = logging.getLogger(__name__)

router = Router()

# Get price

async def symbol_price(symbol: str) -> float | None:
    clean_symbol = symbol.upper().replace("USDT", "")
    pair = f"{clean_symbol}USDT"

    for category in ['linear', 'spot']:
        params = {"category": category, "symbol": pair}
        timeout = aiohttp.ClientTimeout(total=5)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(BYBIT_API_URL, params=params, timeout=timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result_list = data.get('result', {}).get("list", [])

                        if result_list:
                            last_price = float(result_list[0].get('lastPrice', 0))
                            return last_price
        except Exception as e:
            logger.error(f'Error fetching price for {symbol} via Bybit REST API: {e}')

    return None

# Symbol check
async def symbol_check(symbol: str) -> bool:
    clean_symbol = symbol.upper().replace("USDT", "")
    pair = f"{clean_symbol}USDT"

    for category in ['linear', 'spot']:
        params = {'category': category, 'symbol': pair}
        custom_timeout = aiohttp.ClientTimeout(total=5)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(BYBIT_API_URL, params=params,timeout=custom_timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result_lst = data.get("result", {}).get("list", [])
                        if result_lst:
                            return True
        except Exception as e:
            logger.error(f'Failed to validate symbol: {symbol} via BybitAPI')
            return True
    
    return False

# Crypto-whale parsing

async def crypto_parse(bot: Bot):
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                db_symbols = await rq.get_all_monitored_symbols()
                
                if not db_symbols:
                    topics = ["publicTrade.BTCUSDT"]
                else:
                    topics = [f"publicTrade.{s}USDT" if not s.endswith("USDT") else f"publicTrade.{s}" for s in db_symbols]

                logger.info(f"Подключение к Bybit WebSocket. Отслеживаемые тикеры: {topics}")
                async with session.ws_connect(BYBIT_WS_URL) as ws:
                    subscribe_msg = {
                        "op": "subscribe",
                        "args": topics  
                    }
                    
                    await ws.send_str(json.dumps(subscribe_msg))
                    logging.info("Подписка на поток прошла успешно!")

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data_json = json.loads(msg.data)

                            if "topic" in data_json and "data" in data_json:
                                trades = data_json["data"]

                                for trade in trades:
                                    symbol_ticker = trade.get("s")
                                    price = float(trade.get("p", 0))
                                    size = float(trade.get("v", 0))
                                
                                    volume_usd = price * size
                                    if volume_usd >= 1_000_000:
                                        alert_txt = (
                                            "🚨 *🚨 WHALE ALERT ON BYBIT!* 🚨\n\n"
                                            f"🔹 *Asset:* {symbol_ticker}\n"
                                            f"💰 *Total Volume:* ${volume_usd:,.2f}\n"
                                            f"📊 *Price:* ${price:,.2f}\n"
                                            f"📉 *Size:* {size} coins"
                                        )

                                        active_users = await rq.get_active_subscribers(symbol_ticker, volume_usd)

                                        for user in active_users:
                                            try:
                                                await bot.send_message(
                                                    chat_id=user.user_id,
                                                    text=alert_txt,
                                                    parse_mode="Markdown",
                                                )
                                            except Exception as e:
                                                logger.error(f"Не удалось отправить пуш пользователю {user.user_id}: {e}")
                        elif msg.type in (aiohttp.WSMsgType.CLOSE,aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.ERROR):
                            logger.warning("Websocket закрылся или произошла ошибка! Переподключение...")
            except Exception as e:
                logger.error(f"Ошибка в WebSocket подключении: {e} Повтор через 5 секунд")
                await asyncio.sleep(5)
        
    

@router.message(CommandStart())
async def cmd_start(msg: Message):
    if msg.from_user is None:
        return 
    user_id = msg.from_user.id
    caption_txt = (
        "🤖 *Welcome to CryptoPulse!* — Your professional, real-time market anomaly and whale tracker.\n\n"
        "I process high-frequency market data streams via dedicated **WebSockets** to instantly detect massive volume spikes and institutional trades as they happen.\n\n"
        "👉 To learn how to configure your tracking filters and alerts, please use the /help command."
    )
    await msg.answer_photo(
        photo="https://images.unsplash.com/photo-1645731504331-72636399448e?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTU1fHxjcnlwdG9jdXJyZW5jeXxlbnwwfHwwfHx8MA%3D%3D",
        caption=caption_txt,
        parse_mode="Markdown",
    )
    await rq.set_user_id(user_id)

@router.message(Command("help"))
async def cmd_help(msg: Message):
    help_text = (
        "💡 *CryptoPulse Help & Reference Manual*\n\n"
        "Configure your real-time tracking engine using the commands below:\n\n"
        "*📊 Account & Subscription*\n"
        "/profile — Check your current Tier status, active limits, and account metrics.\n"
        "/upgrade — View Premium features, pricing plans, and activate institutional access.\n\n"
        "*🎯 Market Tracking & Filters*\n"
        "/watchlist — Manage your monitored trading pairs and customize volume alerting thresholds.\n"
        "/status — Toggle your live tracking engine stream (Pause/Resume alerts).\n\n"
        "*🪙 Cryptocurrency information*\n"
        "/price btc - Get crypto coin price\n\n"
        "*⏱️ SaaS Tier Limitations:*\n"
        "• *Free Tier:* Monitor up to 3 trading pairs simultaneously with a fixed minimum threshold of $1,000,000 per whale trade.\n"
        "• *Premium Tier:* Monitor up to 50 pairs, fully custom volume thresholds (down to $5,000), and priority low-latency WebSocket routing."    
    )
    await msg.answer(
        help_text, parse_mode="Markdown"
    )

@router.message(Command("profile"))
async def cmd_profile(msg: Message):
    if msg.from_user is None:
        return
    
    user_id = msg.from_user.id
    user_data = await rq.get_profile(user_id)
    
    if not user_data:
        await msg.answer("Profile not found! Please send /start to initialize your account.")
        return
    status_emoji = "🟢 Active" if user_data.is_active else "🔴 Paused"
    tier_name = user_data.tier.upper()

    profile_text = (
        "📊 *CryptoPulse User Profile*\n\n"
        f"👤 *User ID:* `{user_id}`\n"
        f"⚡ *Subscription Tier:* `{tier_name}`\n"
        f"⚙️ *Engine Status:* {status_emoji}\n\n"
    )
    if user_data.tier == 'premium' and user_data.premium_expires_at:
        expires_at = user_data.premium_expires_at.strftime("%Y-%m-%d")
        profile_text += f'⏳ *Premium expires:* `{expires_at}`\n'
    
    profile_text += "💡 *Want to change limits or add more tickers?* Use /watchlist or upgrade your status with /upgrade."
    await msg.answer(profile_text, parse_mode="Markdown")

@router.message(Command("watchlist"))
async def cmd_watchlist(msg: Message):
    if msg.from_user is None:
        return
    user_id = msg.from_user.id
    items = await rq.get_user_watchlist(user_id)

    if not items:
        text = (
            '*📋 Your Watchlist is empty.*\n\n'
            'CryptoPulse will not send you whale alerts until you configure tracking targets'
        )
    else:
        text = (

            '*📋 Your Watchlist Configuration:*\n\n'
            'Whale tracking alerts will be dispatched when a transaction exceeds these limits:'
        )
    
    await msg.answer(text=text, reply_markup=kb.watchlist_keyboard(items), parse_mode="Markdown")

@router.callback_query(F.data == "wl_add")
async def add_data(callback: CallbackQuery, state: FSMContext):
    if callback.message is None:
        return

    await callback.answer()
    await state.set_state(WatchlistStates.add_symbol)
    await callback.message.answer(
        "📝 Enter the crypto asset ticker and value threshold separated by a space.\n"
        "Example: `BTC 1000000` or `ETH 250000`"
    )

@router.message(WatchlistStates.add_symbol)
async def save_watchlist_item(msg: Message, state: FSMContext):
    if msg.text is None or msg.from_user is None or msg.bot is None:
        return
    
    user_id = msg.from_user.id

    try:
        parts = msg.text.split()
        if len(parts) != 2:
            raise ValueError
        
        symbol = parts[0].upper()
        threshold = float(parts[1])

        await msg.bot.send_chat_action(chat_id=msg.chat.id, action='typing')
        is_valid = await symbol_check(symbol)

        if not is_valid:
            await msg.answer(
                f"❌ Asset **{symbol}** was not found on Bybit markets.\n"
                "Please check for typos and enter a valid ticker (e.g., `BTC`, `SOL`, `ETH`).",
                parse_mode="Markdown"
            )
            return



        user_profile = await rq.get_profile(user_id)
        if not user_profile:
            return
            
        tier = user_profile.tier
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        current_count = await rq.get_watchlist_count(user_id)
        if current_count >= limits["watchlist_limit"]:
            await msg.answer(
                f"🚫 *Limit Reached!*\n\n"
                f"Your `{tier.upper()}` tier allows tracking up to {limits['watchlist_limit']} assets.\n"
                f"Please remove an asset or upgrade via /upgrade.",
                parse_mode="Markdown"
            )
            await state.clear()
            return

        if threshold < limits["min_threshold"]:
            await msg.answer(
                f"⚠️ *Threshold Too Low!*\n\n"
                f"Your `{tier.upper()}` tier requires a minimum threshold of `${limits['min_threshold']:,.0f}`.\n"
                f"Please try again or upgrade via /upgrade.",
                parse_mode="Markdown"
            )
            return

        await rq.add_to_watchlist(user_id, symbol, threshold)
        await msg.answer(f"✅ Asset *{symbol}* with threshold `${threshold:,.0f}` has been added!", parse_mode='Markdown')

        await state.clear()

        items = await rq.get_user_watchlist(user_id)
        await msg.answer("📋 Updated Watchlist:", reply_markup=kb.watchlist_keyboard(items))

    except ValueError:
        await msg.answer(
            "⚠️ Invalid structure! Provide input exactly as: **TICKER THRESHOLD**.\n"
            "Example: `BTC 1500000`\n\n"
            "To abort this operation, send /cancel."
        )

@router.callback_query(F.data.startswith("wl_del"))
async def delete_data(callback: CallbackQuery):
    if callback.data is None:
        return
    if not isinstance(callback.message, Message):
        await callback.answer("Error: Message context is unavailable.")
        return
    watchlist_id = int(callback.data.split("_")[2])

    await rq.remove_from_watchlist(watchlist_id)
    await callback.answer("Asset removed", show_alert=True)

    items = await rq.get_user_watchlist(callback.from_user.id)

    if not items:
        await callback.message.edit_text(
            "📋 Your Watchlist is empty.", 
            reply_markup=kb.watchlist_keyboard(items)
        )
    else:
        await callback.message.edit_reply_markup(reply_markup=kb.watchlist_keyboard(items))

@router.callback_query(F.data == "wl_refresh")
async def process_refresh(callback: CallbackQuery):
    if not isinstance(callback.message, Message):
        await callback.answer("Error: Message context is unavailable.")
        return

    await callback.answer("Refreshed")
    items = await rq.get_user_watchlist(callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=kb.watchlist_keyboard(items))

@router.message(Command('status'))
async def cmd_status(msg:Message):
    if msg.from_user is None:
        return
    
    new_status = await rq.toggle_user_status(msg.from_user.id)
    status_emoji = "🟢 Active" if new_status else "🔴 Paused"

    await msg.answer(
        f"⚙️ *Engine Status Updated!*\n\nYour alert stream is now: {status_emoji}",
        parse_mode="Markdown"
    )

@router.message(Command("price"))
async def cmd_price(msg: Message, command: CommandObject):
    if not command.args:
        await msg.answer(
            "⚠️ Please specify a ticker symbol!\n"
            "Example: `/price BTC` or `/price ETH`",
            parse_mode="Markdown"
        )
        return
    
    symbol = command.args.strip().upper().replace('USDT', '')
    price = await symbol_price(symbol)

    if price:
        await msg.answer(
            f"📊 Current price for *{symbol}/USDT* on Bybit: `${price:,.2f}`", 
            parse_mode="Markdown"
        )
    else:
        await msg.answer(
            f"❌ Unable to find price data for asset: *{symbol}*", 
            parse_mode="Markdown"
        )

@router.message(Command('upgrade'))
async def cmd_update(msg: Message):
    description = (
    '*⚡️ CRYPTOPULSE PREMIUM TIER*\n\n'

    'Unlock high-frequency institutional tracking and front-run market movements!\n\n'

    '🔹 Track up to 50 assets simultaneously (vs 3 on Free)\n'
    '🔹 Lower whale threshold down to $5,000 (vs $1,000,000 on Free)\n'
    '🔹 Zero-latency WebSocket alert priority\n'
    '🔹 Spot & Futures market coverage\n\n'

    '💰 Price: 500 Stars / month (~$10.00)'
    )
    prices = [LabeledPrice(label='CryptoPulse premium tier (1 month)', amount=500)]

    await msg.answer_invoice(
        title="CryptoPulse Premium Subscription",
        description=description,
        payload="premium_subscription_payload",  
        provider_token="",                       
        currency="XTR",                          
        prices=prices,
        start_parameter="upgrade-premium",
        parse_mode = 'Markdown'
    )

@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)

@router.message(F.sucessful_payment)
async def process_payment(msg: Message):
    if msg.from_user is None:
        return
    
    user_id = msg.from_user.id

    await rq.change_tier(user_id)

    await msg.answer(
        "🎉 *Congratulations! Premium Activated!*\n\n"
        "Your account has been upgraded to **PREMIUM TIER**.\n"
        "You can now track up to 50 assets with thresholds down to $5,000.\n\n"
        "Use /watchlist to configure your new tracking targets!",
        parse_mode="Markdown"
    )