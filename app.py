import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters

# Database setup
conn = sqlite3.connect('casker_bot.db', check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS users (
             user_id INTEGER PRIMARY KEY,
             username TEXT,
             coins INTEGER DEFAULT 0,
             frozen_coins INTEGER DEFAULT 0,
             invite_count INTEGER DEFAULT 0,
             language TEXT DEFAULT 'en',
             last_daily_bonus TEXT,
             level TEXT DEFAULT 'Newbie'
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS tasks (
             task_id INTEGER PRIMARY KEY AUTOINCREMENT,
             category TEXT,
             link TEXT,
             coins INTEGER,
             description TEXT
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS user_tasks (
             user_id INTEGER,
             task_id INTEGER,
             completion_time DATETIME,
             status TEXT DEFAULT 'pending',
             screenshot TEXT,
             PRIMARY KEY (user_id, task_id)
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
             withdrawal_id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INTEGER,
             amount_coins INTEGER,
             amount_php REAL,
             method TEXT,
             account_info TEXT,
             status TEXT DEFAULT 'pending',
             request_time DATETIME
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS frozen_challenges (
             user_id INTEGER PRIMARY KEY,
             frozen_amount INTEGER,
             required_invites INTEGER,
             completed BOOLEAN DEFAULT 0
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS badges (
             user_id INTEGER,
             badge_name TEXT,
             earned_date DATETIME
             )''')

# Insert initial tasks
tasks_data = [
    # Websites
    ('website', 'https://shrinkme.ink/Proceed', 350, 'Shrinkme.io - Proceed'),
    ('website', 'https://shrinkme.ink/Keepitup', 350, 'Shrinkme.io - Keepitup'),
    ('website', 'https://shrinkme.ink/Proceed2the', 350, 'Shrinkme.io - Proceed2the'),
    ('website', 'https://shrinkme.ink/TotheNextone', 350, 'Shrinkme.io - TotheNextone'),
    ('website', 'https://shrinkme.ink/Almostdones', 350, 'Shrinkme.io - Almostdones'),
    ('website', 'https://linky.io/en/@Pauljjk/dotasker-musty-view-this-post', 200, 'Lilky.Io - Dotasker'),
    ('website', 'https://linky.io/en/@Pauljjk/new-ways-to-earn-in-lilky-io', 200, 'Lilky.Io - New Ways'),
    ('website', 'https://linky.io/en/@Pauljjk/time-to-earn-more-money', 200, 'Lilky.Io - Earn Money'),
    ('website', 'https://oii.la/NewEarningBlogPost', 250, 'Clk.Sh - Blog Post'),
    ('website', 'https://oii.la/NewEarningBlogPosts', 250, 'Clk.Sh - Blog Posts'),
    ('website', 'https://oii.la/NewEarningBlogPostCheckit', 250, 'Clk.Sh - Checkit'),
    ('website', 'https://oii.la/Youreallmostdone', 250, 'Clk.Sh - Almost Done'),
    ('website', 'https://oii.la/FreeEarningSites', 250, 'Clk.Sh - Free Sites'),
    
    # Telegram Groups
    ('telegram_group', 'https://t.me/PinoyEarningCaptcha', 100, 'Pinoy Earning Captcha'),
    ('telegram_group', 'https://t.me/RefferalExchangeslink', 100, 'Referral Exchanges'),
    ('telegram_group', 'https://t.me/SPEEDMANTRICKS', 100, 'Speedman Tricks'),
    ('telegram_group', 'https://t.me/+gSl3DMN3Z5o3NGZl', 100, 'Earning Group'),
    
    # Telegram Bots
    ('telegram_bot', 'https://t.me/BubbleBattleBot/play?startapp=bb_mt0eyllj4o', 500, 'Bubble Battle Bot'),
    ('telegram_bot', 'https://t.me/Y_Sense_bot', 500, 'Y Sense Bot'),
    ('telegram_bot', 'https://t.me/LTCClickersBot?start=user33775667', 500, 'LTC Clickers'),
    ('telegram_bot', 'https://t.me/BCHClickers_Bot?start=user33775667', 500, 'BCH Clickers'),
    ('telegram_bot', 'https://t.me/spell_wallet_bot/wallet?startapp=r-spell1vm0l449xutd3xtdfayjv33l4vtt5l4s758fx4l__utm-friendsTabRef', 500, 'Spell Wallet'),
    ('telegram_bot', 'https://t.me/token1win_bot/start?startapp=refId6142093981', 500, '1win Token Bot'),
    ('telegram_bot', 'https://t.me/PokerMasterofficialbot/miniapp?startapp=GtUOfHYD7AA', 500, 'Poker Master'),
    
    # Apps/Downloads
    ('app_download', 'https://play.google.com/store/apps/details?id=game.buzzbreak.cardstory', 1000, 'Card Story - Use code 83719872'),
    ('app_download', 'https://ph.storewards.co/invite/referrerCode/pd5lw', 1000, 'Storewards - Use code pd5lw'),
    ('app_download', 'https://tgldy.xyz/s/8569576', 1000, 'Money-making App'),
    ('app_download', 'https://arenalive.ph/s/F0aejFU', 1000, 'Arenalive Referral'),
    ('app_download', 'bit.ly/Join-Go-Rewards', 1000, 'Go Rewards'),
    ('app_download', 'https://minepi.com/paulljjk', 1000, 'Pi Network - Use paulljjk'),
    ('app_download', 'https://discoverpawns.eu/14519322', 1000, 'Pawns.app'),
    ('app_download', 'https://s.pita.live/s/VEQkC4', 1000, 'Pita Live'),
    ('app_download', 'https://h5.vshowapi.com/inviteNew/share?c=poppo&link_id=6706799&user_id=59738652&temp_type=1&sys_temp_id=2', 1000, 'VShow App - ID:59738652'),
    ('app_download', 'https://play.google.com/store/apps/details?id=com.gogolive', 1000, 'GOGO Live - Code:03HFTM'),
    
    # Social Media
    ('social_media', 'https://www.facebook.com/share/18gJCUEBcR/', 250, 'Facebook Share')
]

for task in tasks_data:
    c.execute("INSERT OR IGNORE INTO tasks (category, link, coins, description) VALUES (?, ?, ?, ?)", task)

conn.commit()

# Bot setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "7949444590:AAGgm0kttgk-ba8Ac3M8jso4LVy1jGeIVfg"
ADMIN_IDS = [123456789]  # Replace with actual admin IDs

# Frozen coins challenges
FROZEN_CHALLENGES = [
    (500, 1), (1000, 3), (2000, 5), (3000, 7), (5000, 10),
    (10000, 30), (20000, 50), (30000, 70), (50000, 100), (100000, 300)
]

# Level thresholds
LEVELS = {
    "Newbie": (0, 5000),
    "Tasker": (5001, 50000),
    "Grinder": (50001, 200000),
    "Elite": (200001, float('inf'))
}

# Badges
BADGES = {
    "Invite King": 50,
    "Daily Grinder": 7,
    "Cashout Champ": 5
}

# Bot functions
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id
    
    # Create user if not exists
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", 
              (user_id, user.username or user.first_name))
    conn.commit()
    
    # Language selection
    keyboard = [
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
        [InlineKeyboardButton("Filipino 🇵🇭", callback_data='lang_fil')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "Welcome to CASKER Bot! Please choose your language:\n\n"
        "Maligayang pagdating sa CASKER Bot! Mangyaring pumili ng iyong wika:",
        reply_markup=reply_markup
    )

def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith('lang_'):
        # Set language
        lang = data.split('_')[1]
        c.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
        conn.commit()
        query.edit_message_text(get_text(user_id, 'lang_selected'))
        main_menu(update, context, user_id)
        
    elif data == 'main_menu':
        main_menu(update, context, user_id)
        
    elif data == 'profile':
        show_profile(update, context, user_id)
        
    elif data == 'tasks':
        show_task_categories(update, context, user_id)
        
    elif data.startswith('task_category_'):
        category = data.split('_', 2)[2]
        show_tasks(update, context, user_id, category)
        
    elif data.startswith('start_task_'):
        task_id = int(data.split('_')[2])
        start_task(update, context, user_id, task_id)
        
    elif data == 'daily_bonus':
        claim_daily_bonus(update, context, user_id)
        
    elif data == 'invite':
        show_invite_info(update, context, user_id)
        
    elif data == 'withdraw':
        start_withdrawal(update, context, user_id)
        
    elif data == 'leaderboard':
        show_leaderboard(update, context)
        
    elif data == 'spin':
        daily_spin(update, context, user_id)
        
    elif data == 'frozen_coins':
        show_frozen_coins(update, context, user_id)

def get_text(user_id, key):
    c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    lang = c.fetchone()[0] or 'en'
    
    translations = {
        'lang_selected': {
            'en': "Language set successfully!",
            'fil': "Tagumpay na naitakda ang wika!"
        },
        'warning': {
            'en': "⚠️ WARNING: Before starting any task, make sure you complete it. We will verify every click. If we notice something suspicious or incomplete tasks, you will be banned for 1 month. Do NOT delete any apps related to tasks.",
            'fil': "⚠️ BABALA: Bago simulan ang anumang gawain, siguraduhing kumpletuhin ito. Ive-verify namin ang bawat pag-click. Kung may mapansin kaming kahina-hinala o hindi kumpletong gawain, maa-ban ka ng 1 buwan. Huwag BURAHIN ang anumang app na may kinalaman sa mga gawain."
        }
    }
    
    return translations[key][lang]

def main_menu(update: Update, context: CallbackContext, user_id: int) -> None:
    c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    lang = c.fetchone()[0] or 'en'
    
    buttons = [
        [InlineKeyboardButton("📱 Profile" if lang == 'en' else "📱 Profile", callback_data='profile'),
         InlineKeyboardButton("✅ Tasks" if lang == 'en' else "✅ Mga Gawain", callback_data='tasks')],
        [InlineKeyboardButton("🎁 Daily Bonus" if lang == 'en' else "🎁 Araw-araw na Bonus", callback_data='daily_bonus'),
         InlineKeyboardButton("👥 Invite Friends" if lang == 'en' else "👥 Imbitahin ang mga Kaibigan", callback_data='invite')],
        [InlineKeyboardButton("💰 Withdraw" if lang == 'en' else "💰 Mag-withdraw", callback_data='withdraw'),
         InlineKeyboardButton("🏆 Leaderboard" if lang == 'en' else "🏆 Leaderboard", callback_data='leaderboard')],
        [InlineKeyboardButton("🎰 Daily Spin" if lang == 'en' else "🎰 Araw-araw na Ikot", callback_data='spin'),
         InlineKeyboardButton("🧊 Frozen Coins" if lang == 'en' else "🧊 Nakongeladong Mga Barya", callback_data='frozen_coins')]
    ]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    text_en = "🌟 Welcome to CASKER Bot! 🌟\nEarn coins by completing tasks and inviting friends!"
    text_fil = "🌟 Maligayang pagdating sa CASKER Bot! 🌟\nKumita ng mga barya sa pamamagitan ng paggawa ng mga gawain at pag-imbita ng mga kaibigan!"
    
    context.bot.send_message(
        chat_id=user_id,
        text=text_en if lang == 'en' else text_fil,
        reply_markup=reply_markup
    )

def show_profile(update: Update, context: CallbackContext, user_id: int) -> None:
    c.execute("SELECT coins, frozen_coins, invite_count, level, language FROM users WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()
    
    if not user_data:
        return
    
    coins, frozen_coins, invite_count, level, lang = user_data
    php_value = coins * 0.001
    
    # Progress to next level
    next_level = None
    if level == "Newbie":
        next_level = "Tasker (5001 coins)"
        progress = min(coins / 5001 * 100, 100)
    elif level == "Tasker":
        next_level = "Grinder (50001 coins)"
        progress = min((coins - 5000) / 45000 * 100, 100)
    elif level == "Grinder":
        next_level = "Elite (200001 coins)"
        progress = min((coins - 50000) / 150000 * 100, 100)
    else:
        next_level = "Max Level"
        progress = 100
    
    # Get badges
    c.execute("SELECT badge_name FROM badges WHERE user_id = ?", (user_id,))
    badges = [row[0] for row in c.fetchall()]
    
    text_en = f"""
📱 YOUR PROFILE

🆔 User ID: {user_id}
💰 Coins: {coins:,} (₱{php_value:,.2f})
🧊 Frozen Coins: {frozen_coins:,}
👥 Invites: {invite_count}
🏆 Level: {level}
🌟 Next Level: {next_level}
📊 Progress: {progress:.1f}%

🎖️ Badges: {', '.join(badges) if badges else 'None'}

🔗 Your referral link:
https://t.me/casker_earn_bot?start={user_id}
    """
    
    text_fil = f"""
📱 IYONG PROFILE

🆔 User ID: {user_id}
💰 Mga Barya: {coins:,} (₱{php_value:,.2f})
🧊 Nakongeladong Mga Barya: {frozen_coins:,}
👥 Mga Imbitasyon: {invite_count}
🏆 Antas: {level}
🌟 Susunod na Antas: {next_level}
📊 Pag-unlad: {progress:.1f}%

🎖️ Mga Badge: {', '.join(badges) if badges else 'Wala'}

🔗 Iyong referral link:
https://t.me/casker_earn_bot?start={user_id}
    """
    
    back_button = [[InlineKeyboardButton("🔙 Back" if lang == 'en' else "🔙 Bumalik", callback_data='main_menu')]]
    
    context.bot.send_message(
        chat_id=user_id,
        text=text_en if lang == 'en' else text_fil,
        reply_markup=InlineKeyboardMarkup(back_button)
    )

def show_task_categories(update: Update, context: CallbackContext, user_id: int) -> None:
    c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    lang = c.fetchone()[0] or 'en'
    
    categories = [
        ("🌐 Websites", "website"),
        ("👥 Telegram Groups", "telegram_group"),
        ("🤖 Telegram Bots", "telegram_bot"),
        ("📥 Apps/Downloads", "app_download"),
        ("📱 Social Media", "social_media")
    ]
    
    buttons = []
    for name, category in categories:
        buttons.append([InlineKeyboardButton(
            name,
            callback_data=f'task_category_{category}'
        )])
    
    buttons.append([InlineKeyboardButton(
        "🔙 Back" if lang == 'en' else "🔙 Bumalik",
        callback_data='main_menu'
    )])
    
    context.bot.send_message(
        chat_id=user_id,
        text=get_text(user_id, 'warning'),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

def show_tasks(update: Update, context: CallbackContext, user_id: int, category: str) -> None:
    c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    lang = c.fetchone()[0] or 'en'
    
    c.execute("SELECT task_id, description, coins FROM tasks WHERE category = ?", (category,))
    tasks = c.fetchall()
    
    if not tasks:
        context.bot.send_message(
            chat_id=user_id,
            text="No tasks available in this category." if lang == 'en' else "Walang available na mga gawain sa kategoryang ito."
        )
        return
    
    buttons = []
    for task_id, description, coins in tasks:
        c.execute("SELECT status FROM user_tasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
        task_status = c.fetchone()
        
        status = ""
        if task_status:
            if task_status[0] == 'completed':
                status = " ✅"
            elif task_status[0] == 'pending':
                status = " ⏳"
        
        buttons.append([InlineKeyboardButton(
            f"{description} ({coins} coins){status}",
            callback_data=f'start_task_{task_id}'
        )])
    
    buttons.append([InlineKeyboardButton(
        "🔙 Back" if lang == 'en' else "🔙 Bumalik",
        callback_data='tasks'
    )])
    
    context.bot.send_message(
        chat_id=user_id,
        text="Select a task:" if lang == 'en' else "Pumili ng gawain:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

def start_task(update: Update, context: CallbackContext, user_id: int, task_id: int) -> None:
    c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    lang = c.fetchone()[0] or 'en'
    
    c.execute("SELECT link, coins, description FROM tasks WHERE task_id = ?", (task_id,))
    task = c.fetchone()
    
    if not task:
        return
    
    link, coins, description = task
    
    # Check if already completed
    c.execute("SELECT status FROM user_tasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
    existing_task = c.fetchone()
    
    if existing_task and existing_task[0] == 'completed':
        context.bot.send_message(
            chat_id=user_id,
            text="You've already completed this task!" if lang == 'en' else "Natapos mo na ang gawaing ito!"
        )
        return
    
    # Start task
    if existing_task:
        c.execute("UPDATE user_tasks SET status = 'pending', completion_time = NULL WHERE user_id = ? AND task_id = ?", 
                 (user_id, task_id))
    else:
        c.execute("INSERT INTO user_tasks (user_id, task_id, status) VALUES (?, ?, 'pending')", 
                 (user_id, task_id))
    conn.commit()
    
    warning_text = get_text(user_id, 'warning')
    
    message = f"""
🛠️ TASK STARTED

📝 Task: {description}
💰 Reward: {coins} coins
🔗 Link: {link}

{warning_text}

⚠️ You have 30 minutes to complete this task. After completion, upload a screenshot as proof.
    """
    
    if lang == 'fil':
        message = f"""
🛠️ SINIMULAN ANG GAWAIN

📝 Gawain: {description}
💰 Gantimpala: {coins} mga barya
🔗 Link: {link}

{warning_text}

⚠️ Mayroon kang 30 minuto upang makumpleto ang gawaing ito. Pagkatapos ng pagkumpleto, mag-upload ng screenshot bilang patunay.
        """
    
    context.bot.send_message(
        chat_id=user_id,
        text=message
    )
    
    # Schedule verification
    context.job_queue.run_once(
        verify_task, 
        30 * 60,  # 30 minutes
        context={'user_id': user_id, 'task_id': task_id}
    )

def verify_task(context: CallbackContext) -> None:
    job = context.job
    user_id = job.context['user_id']
    task_id = job.context['task_id']
    
    c.execute("SELECT status FROM user_tasks WHERE user_id = ? AND task_id = ?", (user_id, task_id))
    task_status = c.fetchone()
    
    if not task_status or task_status[0] != 'completed':
        # Mark as expired
        c.execute("UPDATE user_tasks SET status = 'expired' WHERE user_id = ? AND task_id = ?", 
                 (user_id, task_id))
        conn.commit()
        
        c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
        lang = c.fetchone()[0] or 'en'
        
        context.bot.send_message(
            chat_id=user_id,
            text="Task expired. Please complete within 30 minutes next time." 
                 if lang == 'en' else "Nag-expire ang gawain. Mangyaring kumpletuhin sa loob ng 30 minuto sa susunod."
        )

def handle_screenshot(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    photo = update.message.photo[-1].file_id
    
    # Find pending task
    c.execute("SELECT task_id FROM user_tasks WHERE user_id = ? AND status = 'pending'", (user_id,))
    pending_task = c.fetchone()
    
    if not pending_task:
        return
    
    task_id = pending_task[0]
    
    # Update task with screenshot
    c.execute("UPDATE user_tasks SET screenshot = ?, status = 'completed', completion_time = datetime('now') WHERE user_id = ? AND task_id = ?",
             (photo, user_id, task_id))
    conn.commit()
    
    # Get task reward
    c.execute("SELECT coins FROM tasks WHERE task_id = ?", (task_id,))
    coins = c.fetchone()[0]
    
    # Add coins to user
    c.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (coins, user_id))
    conn.commit()
    
    # Update level
    update_user_level(user_id)
    
    c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    lang = c.fetchone()[0] or 'en'
    
    # Praise messages
    praises_en = [
        "🎉 You just earned {coins} coins! You're killing it! 💪",
        "🔥 Task done! That's how legends do it.",
        "👑 You're getting closer to that cashout!",
        "🎯 More tasks = more bonuses. Keep going!"
    ]
    
    praises_fil = [
        "🎉 Kumuha ka ng {coins} na mga barya! Ang galing mo! 💪",
        "🔥 Tapos na ang gawain! Ganyan ang mga alamat.",
        "👑 Palapit ka na sa cashout!",
        "🎯 Mas maraming gawain = mas maraming bonus. Magpatuloy!"
    ]
    
    praise = context.bot.random.choice(praises_en if lang == 'en' else praises_fil).format(coins=coins)
    
    context.bot.send_message(
        chat_id=user_id,
        text=f"✅ Task completed! {praise}"
    )
    
    # Send to admin for verification
    for admin_id in ADMIN_IDS:
        context.bot.send_photo(
            chat_id=admin_id,
            photo=photo,
            caption=f"User {user_id} completed task {task_id}"
        )

def claim_daily_bonus(update: Update, context: CallbackContext, user_id: int) -> None:
    c.execute("SELECT language, last_daily_bonus FROM users WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()
    
    if not user_data:
        return
    
    lang, last_bonus = user_data
    today = datetime.now().strftime('%Y-%m-%d')
    
    if last_bonus == today:
        context.bot.send_message(
            chat_id=user_id,
            text="You've already claimed your daily bonus today!" 
                 if lang == 'en' else "Nakuha mo na ang iyong pang-araw-araw na bonus ngayon!"
        )
        return
    
    # Award bonus (500 coins)
    c.execute("UPDATE users SET coins = coins + 500, last_daily_bonus = ? WHERE user_id = ?", 
             (today, user_id))
    conn.commit()
    
    # Update streak
    update_streak(user_id)
    
    context.bot.send_message(
        chat_id=user_id,
        text="🎉 You claimed your daily 500 coins bonus!" 
             if lang == 'en' else "🎉 Nakuha mo ang iyong pang-araw-araw na 500 coins na bonus!"
    )

def update_streak(user_id):
    # Implement streak tracking logic
    pass

def show_invite_info(update: Update, context: CallbackContext, user_id: int) -> None:
    c.execute("SELECT language, invite_count FROM users WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()
    
    if not user_data:
        return
    
    lang, invite_count = user_data
    
    # Calculate bonus coins from invites
    bonus = 0
    if invite_count >= 3:
        bonus += 200
    if invite_count >= 5:
        bonus += 100  # Total 300
    if invite_count >= 10:
        bonus += 200  # Total 500
    
    text_en = f"""
👥 INVITE FRIENDS

🔗 Your referral link:
https://t.me/casker_earn_bot?start={user_id}

💰 Earn 50 coins for each friend who joins using your link!

🎁 Bonus Rewards:
→ Invite 3 friends: 200 coins
→ Invite 5 friends: +100 coins (total 300)
→ Invite 10 friends: +200 coins (total 500)

📊 Your progress:
→ Friends invited: {invite_count}
→ Bonus earned: {bonus} coins
    """
    
    text_fil = f"""
👥 MAG-IMBITA NG MGA KAIBIGAN

🔗 Ang iyong referral link:
https://t.me/casker_earn_bot?start={user_id}

💰 Kumita ng 50 coins para sa bawat kaibigang sumali gamit ang iyong link!

🎁 Mga Bonus na Gantimpala:
→ Mag-imbita ng 3 kaibigan: 200 coins
→ Mag-imbita ng 5 kaibigan: +100 coins (kabuuang 300)
→ Mag-imbita ng 10 kaibigan: +200 coins (kabuuang 500)

📊 Ang iyong pag-unlad:
→ Mga kaibigang na-imbita: {invite_count}
→ Nakuha na bonus: {bonus} coins
    """
    
    back_button = [[InlineKeyboardButton("🔙 Back" if lang == 'en' else "🔙 Bumalik", callback_data='main_menu')]]
    
    context.bot.send_message(
        chat_id=user_id,
        text=text_en if lang == 'en' else text_fil,
        reply_markup=InlineKeyboardMarkup(back_button)
    )

def start_withdrawal(update: Update, context: CallbackContext, user_id: int) -> None:
    c.execute("SELECT language, coins FROM users WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()
    
    if not user_data:
        return
    
    lang, coins = user_data
    php_value = coins * 0.001
    
    if coins < 500000:
        context.bot.send_message(
            chat_id=user_id,
            text=f"You need at least 500,000 coins to withdraw. You have {coins:,} coins." 
                 if lang == 'en' else f"Kailangan mo ng hindi bababa sa 500,000 coins para makapag-withdraw. Mayroon kang {coins:,} coins."
        )
        return
    
    text_en = f"""
💰 WITHDRAWAL

Your balance: {coins:,} coins (₱{php_value:,.2f})

Withdrawal options:
1. 500,000 coins = ₱500
2. 700,000 coins = ₱700
3. 1,000,000 coins = ₱1,000

Please reply with:
1. Withdrawal amount (in coins)
2. Method (GCash or Maya)
3. Account name
4. Account number

Example:
"700000 GCash Juan Dela Cruz 09123456789"
    """
    
    text_fil = f"""
💰 PAG-WITHDRAW

Ang iyong balanse: {coins:,} coins (₱{php_value:,.2f})

Mga pagpipilian sa pag-withdraw:
1. 500,000 coins = ₱500
2. 700,000 coins = ₱700
3. 1,000,000 coins = ₱1,000

Mangyaring magreply ng:
1. Halagang iwi-withdraw (sa coins)
2. Paraan (GCash o Maya)
3. Pangalan sa account
4. Numero ng account

Halimbawa:
"700000 GCash Juan Dela Cruz 09123456789"
    """
    
    context.bot.send_message(
        chat_id=user_id,
        text=text_en if lang == 'en' else text_fil
    )
    
    # Set state for withdrawal
    context.user_data['awaiting_withdrawal'] = True

def handle_withdrawal(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    
    if not context.user_data.get('awaiting_withdrawal'):
        return
    
    text = update.message.text
    parts = text.split()
    
    if len(parts) < 4:
        update.message.reply_text("Invalid format. Please try again.")
        return
    
    try:
        amount = int(parts[0])
        method = parts[1]
        name = ' '.join(parts[2:-1])
        number = parts[-1]
    except:
        update.message.reply_text("Invalid format. Please try again.")
        return
    
    valid_amounts = [500000, 700000, 1000000]
    if amount not in valid_amounts:
        update.message.reply_text("Invalid amount. Valid amounts: 500000, 700000, 1000000")
        return
    
    if method.lower() not in ['gcash', 'maya']:
        update.message.reply_text("Invalid method. Use GCash or Maya.")
        return
    
    # Check balance
    c.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    coins = c.fetchone()[0]
    
    if coins < amount:
        update.message.reply_text("Insufficient coins.")
        return
    
    # Deduct coins
    c.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (amount, user_id))
    
    # Create withdrawal record
    php_amount = amount * 0.001
    c.execute("""
        INSERT INTO withdrawals (user_id, amount_coins, amount_php, method, account_info, request_time)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (user_id, amount, php_amount, method, f"{name}|{number}"))
    
    conn.commit()
    
    # Notify user
    update.message.reply_text(
        "Withdrawal request submitted! Processing may take 5-10 days. "
        "Please ensure your account details are correct."
    )
    
    # Notify admin
    for admin_id in ADMIN_IDS:
        context.bot.send_message(
            chat_id=admin_id,
            text=f"New withdrawal request!\nUser: {user_id}\nAmount: {amount} coins (₱{php_amount})\nMethod: {method}\nAccount: {name} | {number}"
        )
    
    # Clear state
    context.user_data['awaiting_withdrawal'] = False

def show_leaderboard(update: Update, context: CallbackContext) -> None:
    c.execute("""
        SELECT user_id, username, coins 
        FROM users 
        ORDER BY coins DESC 
        LIMIT 5
    """)
    top_users = c.fetchall()
    
    if not top_users:
        context.bot.send_message(
            chat_id=update.effective_user.id,
            text="No users yet!"
        )
        return
    
    text = "🏆 TOP 5 EARNERS 🏆\n\n"
    for i, (user_id, username, coins) in enumerate(top_users, 1):
        text += f"{i}. {username or 'User#'+str(user_id)} - {coins:,} coins\n"
    
    text += "\n🏅 Rewards:\n1st: 250,000 coins\n2nd: 150,000 coins\n3rd: 100,000 coins"
    text += "\n\nUpdated every 5 hours"
    
    context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text
    )

def daily_spin(update: Update, context: CallbackContext, user_id: int) -> None:
    # Implement spin logic
    pass

def show_frozen_coins(update: Update, context: CallbackContext, user_id: int) -> None:
    c.execute("SELECT language, frozen_coins FROM users WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()
    
    if not user_data:
        return
    
    lang, frozen_coins = user_data
    
    c.execute("SELECT frozen_amount, required_invites, completed FROM frozen_challenges WHERE user_id = ?", (user_id,))
    challenges = c.fetchall()
    
    text_en = f"""
🧊 FROZEN COINS BANK

You have {frozen_coins:,} frozen coins.

Complete challenges to unlock them:
    """
    
    text_fil = f"""
🧊 NAKONGELADONG MGA BARYA

Mayroon kang {frozen_coins:,} nakongeladong mga barya.

Kumpletuhin ang mga hamon upang ma-unlock ang mga ito:
    """
    
    text = text_en if lang == 'en' else text_fil
    
    for amount, required, completed in challenges:
        status = "✅ Completed" if completed else "❌ Not Completed"
        text += f"\n→ Unlock {amount:,} coins: Invite {required} users - {status}"
    
    buttons = [[InlineKeyboardButton("🔙 Back" if lang == 'en' else "🔙 Bumalik", callback_data='main_menu')]]
    
    context.bot.send_message(
        chat_id=user_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

def update_user_level(user_id):
    c.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    coins = c.fetchone()[0]
    
    new_level = "Newbie"
    for level, (min_coins, max_coins) in LEVELS.items():
        if min_coins <= coins <= max_coins:
            new_level = level
            break
    
    c.execute("UPDATE users SET level = ? WHERE user_id = ?", (new_level, user_id))
    conn.commit()
    
    # Check for badge eligibility
    check_badges(user_id)

def check_badges(user_id):
    c.execute("SELECT invite_count FROM users WHERE user_id = ?", (user_id,))
    invite_count = c.fetchone()[0]
    
    # Check for Invite King badge
    if invite_count >= BADGES["Invite King"]:
        award_badge(user_id, "Invite King")
    
    # Other badge checks would be similar

def award_badge(user_id, badge_name):
    c.execute("SELECT 1 FROM badges WHERE user_id = ? AND badge_name = ?", (user_id, badge_name))
    if not c.fetchone():
        c.execute("INSERT INTO badges (user_id, badge_name, earned_date) VALUES (?, ?, datetime('now'))",
                 (user_id, badge_name))
        conn.commit()
        
        # Notify user
        try:
            context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 You earned the '{badge_name}' badge! 🏆"
            )
        except:
            pass

def update_leaderboard(context: CallbackContext):
    # This would run every 5 hours
    pass

def sunday_bonus(context: CallbackContext):
    # Double invite coins on Sundays
    if datetime.today().weekday() == 6:  # Sunday
        # Implementation would go here
        pass

def broadcast_command(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = ' '.join(context.args)
    c.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in c.fetchall()]
    
    for user_id in user_ids:
        try:
            context.bot.send_message(chat_id=user_id, text=message)
        except:
            pass  # User may have blocked the bot
    
    update.message.reply_text(f"Broadcast sent to {len(user_ids)} users.")

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_click))
    dp.add_handler(MessageHandler(Filters.photo, handle_screenshot))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_withdrawal))
    dp.add_handler(CommandHandler("broadcast", broadcast_command))
    
    # Scheduled tasks
    jq = updater.job_queue
    jq.run_repeating(update_leaderboard, interval=5*3600, first=0)
    jq.run_daily(sunday_bonus, time=datetime.strptime("00:00", "%H:%M").time())
    
    # Start bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
