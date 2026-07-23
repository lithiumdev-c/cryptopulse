from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

def watchlist_keyboard(items) -> InlineKeyboardMarkup:
    buttons = []
    for item in items:
        buttons.append(
            [InlineKeyboardButton(
                text = f'❌ Delete {item.symbol} (${item.threshold_usd:,.0f})',
                callback_data=f"wl_del_{item.id}"
            )]
        )
    buttons.append([InlineKeyboardButton(text='➕ Add coin', callback_data=f"wl_add")])
    buttons.append([InlineKeyboardButton(text='🔄 Refresh', callback_data=f"wl_refresh")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def payment_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text = 'Pay with stars 1000')]
    ]