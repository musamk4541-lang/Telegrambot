import sqlite3
import os
import re
import asyncio
import threading
from flask import Flask
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, MessageNotModifiedError

# ================= FLASK WEB SERVER FOR RENDER (FREE TIER) =================
app = Flask('')

@app.route('/')
def home():
    return "Bot yana aiki lafiya kalau a Render Free Tier!"

def run_web():
    # Render yana tura lambar Port ta wannan Environment Variable ɗin
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# Gudanar da Web Server a bango kafin komai
threading.Thread(target=run_web, daemon=True).start()
# ===========================================================================

# Secret Credentials
API_ID = 31270033  
API_HASH = '4ed684ebbd6a4d258a49c9923183b468'  
BOT_TOKEN = '8651109350:AAEOCevtrlKor5RjcJTnl9Sr8bjXfd7e_KI'  

# Initialize Main Bot Engine
bot = TelegramClient('babban_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

DATABASE_NAME = 'bot_bayanai_v4.db'
tsarin_login = {}
tsarin_zabi = {}  
tsarin_tashoshi = {}  
active_user_clients = {}  

def gyara_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS masu_amfani (
            user_id INTEGER PRIMARY KEY, 
            phone_number TEXT, 
            session_string TEXT,
            source_channel TEXT,
            source_name TEXT,
            target_channel TEXT,
            target_name TEXT,
            forwarding_status INTEGER DEFAULT 0,
            header_status INTEGER DEFAULT 0,
            media_forwarding INTEGER DEFAULT 1,
            url_preview INTEGER DEFAULT 0,
            cire_links INTEGER DEFAULT 0,
            cire_usernames INTEGER DEFAULT 0,
            repeat_post INTEGER DEFAULT 0,
            auto_delete_msg INTEGER DEFAULT 0,
            link_auto_replies INTEGER DEFAULT 0,
            amazon_converter INTEGER DEFAULT 0,
            disable_links INTEGER DEFAULT 0,
            mono_text INTEGER DEFAULT 0,
            protected_forwards INTEGER DEFAULT 0,
            auto_reaction INTEGER DEFAULT 0,
            blacklist_keywords TEXT DEFAULT '',
            whitelist_keywords TEXT DEFAULT '',
            trim_words TEXT DEFAULT '',
            replace_links TEXT DEFAULT '',
            replace_usernames TEXT DEFAULT '',
            replace_words TEXT DEFAULT '',
            add_header TEXT DEFAULT '',
            add_footer TEXT DEFAULT '',
            target_delay INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

gyara_database()

def dauko_session(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT session_string FROM masu_amfani WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res and res[0] else None

def ajiye_session_db(user_id, phone, session_str):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO masu_amfani (user_id, phone_number, session_string)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET phone_number=?, session_string=?
    ''', (user_id, phone, session_str, phone, session_str))
    conn.commit()
    conn.close()

def sabunta_channel_db(user_id, guri, chat_id, chat_name):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    if guri == 'source':
        cursor.execute("UPDATE masu_amfani SET source_channel=?, source_name=? WHERE user_id=?", (str(chat_id), chat_name, user_id))
    elif guri == 'target':
        cursor.execute("UPDATE masu_amfani SET target_channel=?, target_name=? WHERE user_id=?", (str(chat_id), chat_name, user_id))
    conn.commit()
    conn.close()

def duba_cikakken_config(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM masu_amfani WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def sauya_kofofin_gaba_daya(user_id, col_name, yanayi=None):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    if yanayi is not None:
        cursor.execute(f"UPDATE masu_amfani SET {col_name}=? WHERE user_id=?", (yanayi, user_id))
    else:
        cursor.execute(f"SELECT {col_name} FROM masu_amfani WHERE user_id=?", (user_id,))
        res = cursor.fetchone()
        if res:
            sabon_yanayi = 0 if res[0] == 1 else 1
            cursor.execute(f"UPDATE masu_amfani SET {col_name}=? WHERE user_id=?", (sabon_yanayi, user_id))
    conn.commit()
    conn.close()

def goge_channel_db(user_id, guri):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    if guri == 'source':
        cursor.execute("UPDATE masu_amfani SET source_channel='', source_name='Ba a saita ba' WHERE user_id=?", (user_id,))
    elif guri == 'target':
        cursor.execute("UPDATE masu_amfani SET target_channel='', target_name='Ba a saita ba' WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def reset_all_config_db(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE masu_amfani SET 
        source_channel='', source_name='Ba a saita ba',
        target_channel='', target_name='Ba a saita ba',
        forwarding_status=0, header_status=0, media_forwarding=1,
        url_preview=0, cire_links=0, cire_usernames=0, mono_text=0
        WHERE user_id=?
    ''', (user_id,))
    conn.commit()
    conn.close()

def goge_user_daga_db(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM masu_amfani WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

# Allon Farko (/start) - Restart & Login
@bot.on(events.NewMessage(pattern='/start'))
async def start_cmd(event):
    user_id = event.sender_id
    res = duba_cikakken_config(user_id)
    
    if not res:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO masu_amfani (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
    
    await lconfig_cmd(event)

# Nuna Cikakken Config (/lconfig)
@bot.on(events.NewMessage(pattern='/lconfig'))
async def lconfig_cmd(event):
    user_id = event.sender_id
    res = duba_cikakken_config(user_id)
    
    src_name = res['source_name'] if res and res['source_name'] else 'Ba a saita ba'
    trg_name = res['target_name'] if res and res['target_name'] else 'Ba a saita ba'
    
    def status_icon(val):
        return "🟢 ON" if val == 1 else "🔴 OFF"

    f_status = status_icon(res['forwarding_status']) if res else "🔴 OFF"
    h_status = status_icon(res['header_status']) if res else "🔴 OFF"
    m_status = status_icon(res['media_forwarding']) if res else "🟢 ON"
    u_status = status_icon(res['url_preview']) if res else "🔴 OFF"
    l_status = status_icon(res['cire_links']) if res else "🔴 OFF"
    un_status = status_icon(res['cire_usernames']) if res else "🔴 OFF"
    mn_status = status_icon(res['mono_text']) if res else "🔴 OFF"

    dashboard = f"""🛠️ **Your Current Configuration Settings**
━━━━━━━━━━━━━━━━━━━
📥 **Source Channels for Copy Post**
   └─ • `{src_name}`

🎯 **Target Channels for Forwarding**
   └─ • `{trg_name}`

⚙️ **General Settings**
  ┌─ Forwarding Status: {f_status}
  ├─ Header Status: {h_status}
  ├─ Media Forwarding: {m_status}
  ├─ URL Preview: {u_status}
  ├─ Remove Links: {l_status}
  ├─ Remove Usernames: {un_status}
  └─ Mono Text: {mn_status}

💬 **Help Center:** @musamk11
━━━━━━━━━━━━━━━━━━━
🚀 *Zabi abubuwan da kake son sauyawa a kasa:*"""

    keyboard = [
        [Button.inline("🚀 Fara Login", b"fara_login"), Button.inline("❌ Logout Lamba", b"logout_acc")],
        [Button.inline("📥 Saita Source", b"saita_source"), Button.inline("🎯 Saita Target", b"saita_target")],
        [Button.inline("🔄 Forwarding Status", b"tog_forwarding_status"), Button.inline("🔼 Header Status", b"tog_header_status")],
        [Button.inline("🖼️ Media Forwarding", b"tog_media_forwarding"), Button.inline("🌐 URL Preview", b"tog_url_preview")],
        [Button.inline("🔗 Remove Links", b"tog_cire_links"), Button.inline("👤 Remove Usernames", b"tog_cire_usernames")],
        [Button.inline("📞 Tuntubi Support", b"tuntuba_admin"), Button.inline("🔄 Refresh Menu", b"refresh_dashboard")]
    ]
    
    if isinstance(event, events.CallbackQuery.Event):
        try:
            await event.edit(dashboard, buttons=keyboard)
        except MessageNotModifiedError:
            pass
    else:
        await event.respond(dashboard, buttons=keyboard)

# Saita Source Channel (/source)
@bot.on(events.NewMessage(pattern='/source'))
async def source_cmd(event):
    user_id = event.sender_id
    u_client = active_user_clients.get(user_id)
    if not u_client:
        sess_str = dauko_session(user_id)
        if sess_str:
            u_client = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
            await u_client.connect()
            active_user_clients[user_id] = u_client
        else:
            await event.respond("❌ Ba ka yi Login ba tukunna! Tura /start domin shigar da asusunka.")
            return

    await event.respond("⏳ Ina binciko dukkan tashoshin ku dake cikin wannan asusun, don Allah jira kaɗan...")
    try:
        tashoshi_list = []
        async for dialog in u_client.iter_dialogs():
            if dialog.is_channel or dialog.is_group:
                tashoshi_list.append({'id': dialog.id, 'title': dialog.title})
        
        if not tashoshi_list:
            await event.respond("❌ Ba a sami wata tasha ko group a cikin asusunka ba.")
            return

        tsarin_tashoshi[user_id] = tashoshi_list
        tsarin_zabi[user_id] = 'source'

        sako = "📥 **Zabi lambar tashar da kake so a kasa don Source:**\n━━━━━━━━━━━━━━━━━━━\n"
        for i, ch in enumerate(tashoshi_list[:50], 1):
            sako += f"{i}. {ch['title']}\n"
        sako += "\n━━━━━━━━━━━━━━━━━━━\n✍️ **Rubuta lambar a kasa:**"
        await event.respond(sako)
    except Exception as e:
        await event.respond(f"❌ Kuskure wajen zakulo tashoshi: {str(e)}")

# Saita Target Channel (/target)
@bot.on(events.NewMessage(pattern='/target'))
async def target_cmd(event):
    user_id = event.sender_id
    u_client = active_user_clients.get(user_id)
    if not u_client:
        sess_str = dauko_session(user_id)
        if sess_str:
            u_client = TelegramClient(StringSession(sess_str), API_ID, API_HASH)
            await u_client.connect()
            active_user_clients[user_id] = u_client
        else:
            await event.respond("❌ Ba ka yi Login ba tukunna! Tura /start domin shigar da asusunka.")
            return

    await event.respond("⏳ Ina binciko dukkan tashoshin ku dake cikin wannan asusun, don Allah jira kaɗan...")
    try:
        tashoshi_list = []
        async for dialog in u_client.iter_dialogs():
            if dialog.is_channel or dialog.is_group:
                tashoshi_list.append({'id': dialog.id, 'title': dialog.title})
        
        if not tashoshi_list:
            await event.respond("❌ Ba a sami wata tasha ko group a cikin asusunka ba.")
            return

        tsarin_tashoshi[user_id] = tashoshi_list
        tsarin_zabi[user_id] = 'target'

        sako = "🎯 **Zabi lambar tashar da kake so a kasa don Target:**\n━━━━━━━━━━━━━━━━━━━\n"
        for i, ch in enumerate(tashoshi_list[:50], 1):
            sako += f"{i}. {ch['title']}\n"
        sako += "\n━━━━━━━━━━━━━━━━━━━\n✍️ **Rubuta lambar a kasa:**"
        await event.respond(sako)
    except Exception as e:
        await event.respond(f"❌ Kuskure wajen zakulo tashoshi: {str(e)}")

# Kunna Forwarding (/start_forwarding)
@bot.on(events.NewMessage(pattern='/start_forwarding'))
async def start_forwarding_cmd(event):
    user_id = event.sender_id
    sauya_kofofin_gaba_daya(user_id, 'forwarding_status', 1)
    await event.respond("🟢 An kunna **Auto Forwarding** cikin nasara!")

# Kashe Forwarding (/stop_forvwarding)
@bot.on(events.NewMessage(pattern='/stop_forvwarding'))
async def stop_forwarding_cmd(event):
    user_id = event.sender_id
    sauya_kofofin_gaba_daya(user_id, 'forwarding_status', 0)
    await event.respond("🔴 An kashe **Auto Forwarding** cikin nasara!")

# Goge Source Channel (/remove_source)
@bot.on(events.NewMessage(pattern='/remove_source'))
async def remove_source_cmd(event):
    user_id = event.sender_id
    goge_channel_db(user_id, 'source')
    await event.respond("🗑️ An goge Source Channel dinka.")

# Goge Target Channel (/remove_target)
@bot.on(events.NewMessage(pattern='/remove_target'))
async def remove_target_cmd(event):
    user_id = event.sender_id
    goge_channel_db(user_id, 'target')
    await event.respond("🗑️ An goge Target Channel dinka.")

# Settings na Message Forwarding (/forward_settings)
@bot.on(events.NewMessage(pattern='/forward_settings'))
async def forward_settings_cmd(event):
    user_id = event.sender_id
    res = duba_cikakken_config(user_id)
    if not res:
        await event.respond("❌ Don Allah yi /start tukunna.")
        return
        
    dashboard_settings = f"""⚙️ **Message Forwarding Configuration Settings**
━━━━━━━━━━━━━━━━━━━
🖼️ Media Forwarding: {"🟢 ON" if res['media_forwarding'] == 1 else "🔴 OFF"}
🌐 URL Preview: {"🟢 ON" if res['url_preview'] == 1 else "🔴 OFF"}
🔗 Remove Links: {"🟢 ON" if res['cire_links'] == 1 else "🔴 OFF"}
👤 Remove Usernames: {"🟢 ON" if res['cire_usernames'] == 1 else "🔴 OFF"}
📝 Mono Text: {"🟢 ON" if res['mono_text'] == 1 else "🔴 OFF"}
🔼 Header Status: {"🟢 ON" if res['header_status'] == 1 else "🔴 OFF"}
"""
    await event.respond(dashboard_settings)

# Reset Dukkan Configuration (/reset_config)
@bot.on(events.NewMessage(pattern='/reset_config'))
async def reset_config_cmd(event):
    user_id = event.sender_id
    reset_all_config_db(user_id)
    await event.respond("🔄 An mayar da dukkan settings dinka zuwa na farko (Default).")

# Nemar Taimako ko Tuntuba (/help)
@bot.on(events.NewMessage(pattern='/help'))
async def help_cmd(event):
    await event.respond("💬 Tuntubi babban admin na Support a nan: @musamk11")

# Logout Lambar Wayar Mutum (/logout)
@bot.on(events.NewMessage(pattern='/logout'))
async def logout_cmd(event):
    user_id = event.sender_id
    if user_id in active_user_clients:
        try:
            await active_user_clients[user_id].disconnect()
        except:
            pass
        del active_user_clients[user_id]
    goge_user_daga_db(user_id)
    await event.respond("✅ An yi logout kuma an goge dukkan zamanka (sessions) daga bot.")

# ----------------- CALLBACK BUTTON HANDLERS -----------------

@bot.on(events.CallbackQuery(data=b"refresh_dashboard"))
async def refresh_db_click(event):
    await lconfig_cmd(event)

@bot.on(events.CallbackQuery(data=re.compile(b"tog_(.*)")))
async def toggle_settings_click(event):
    user_id = event.sender_id
    col_name = event.data.decode().split('_', 1)[1]
    
    res = duba_cikakken_config(user_id)
    if not res:
        await event.respond("❌ Don Allah yi Login da farko kafin sarrafa settings.", alert=True)
        return
        
    sauya_kofofin_gaba_daya(user_id, col_name)
    await lconfig_cmd(event)

@bot.on(events.CallbackQuery(data=b"fara_login"))
async def fara_login_click(event):
    user_id = event.sender_id
    tsarin_login[user_id] = {'step': 'phone'}
    await event.respond("📞 Don Allah turo lambar wayarka tare da lambar kasa (e.g., +2348012345678):")

@bot.on(events.CallbackQuery(data=b"logout_acc"))
async def logout_acc_click(event):
    await logout_cmd(event)

@bot.on(events.CallbackQuery(data=b"saita_source"))
async def saita_source_click(event):
    await source_cmd(event)

@bot.on(events.CallbackQuery(data=b"saita_target"))
async def saita_target_click(event):
    await target_cmd(event)

@bot.on(events.CallbackQuery(data=b"tuntuba_admin"))
async def tuntuba_admin_click(event):
    await help_cmd(event)


# -------- PROCESSING TEXT MESSAGES (CHANNELS SELECTION & LOGIN) --------

@bot.on(events.NewMessage)
async def karbi_bayanai(event):
    if event.text.startswith('/'):
        return
        
    user_id = event.sender_id
    text = event.text.strip()

    if user_id in tsarin_zabi and user_id in tsarin_tashoshi:
        guri = tsarin_zabi[user_id]
        list_din_tashoshi = tsarin_tashoshi[user_id]
        
        if text.isdigit():
            lamba = int(text)
            if 1 <= lamba <= len(list_din_tashoshi):
                zababbiya = list_din_tashoshi[lamba - 1]
                chat_id = zababbiya['id']
                chat_name = zababbiya['title']
                
                sabunta_channel_db(user_id, guri, chat_id, chat_name)
                await event.respond(f"✅ An yi nasarar saita `{chat_name}` a matsayin **{guri.upper()}**!")
                
                del tsarin_zabi[user_id]
                del tsarin_tashoshi[user_id]
                await lconfig_cmd(event)
                return
            else:
                await event.respond(f"❌ Lambar da ka saka ba ta cikin jerin da na tura maka. Don Allah zabi tsakanin 1 zuwa {len(list_din_tashoshi)}:")
                return
        else:
            await event.respond("❌ Don Allah rubuta lambar tashar kawai (misali: 5):")
            return

    if user_id in tsarin_login:
        bayanai = tsarin_login[user_id]
        
        if bayanai['step'] == 'phone':
            bayanai['phone'] = text
            u_client = TelegramClient(StringSession(), API_ID, API_HASH)
            await u_client.connect()
            try:
                sent_code = await u_client.send_code_request(text)
                bayanai['phone_code_hash'] = sent_code.phone_code_hash
                bayanai['client'] = u_client
                bayanai['step'] = 'otp'
                tsarin_login[user_id] = bayanai
                
                bayanai_otp = (
                    "📩 **An tura saƙon OTP cikin nasara!**\n\n"
                    "⚠️ **DOKAR SHIGAR DA OTP:**\n"
                    "Telegram ba ya barin tura lambobin OTP guda 5 kai tsaye a cikin bot. "
                    "Don haka, dole ne ka haɗa lambar OTP ɗinka da kalmar **BAFBOT** a farko ba tare da bada sarari (space) ba.\n\n"
                    "📝 **Misali:** Idan lambar OTP ɗinka ita ne `12345`, to ka rubuta shi kamar haka:\n"
                    "👉 **`BAFBOT12345`**\n\n"
                    "✍️ *Don Allah rubuta naka yanzu ka tura:* "
                )
                await event.respond(bayanai_otp)
            except Exception as e:
                await event.respond(f"❌ Kuskure wajen tura OTP: {str(e)}")
                await u_client.disconnect()
                del tsarin_login[user_id]
                
        elif bayanai['step'] == 'otp':
            u_client = bayanai['client']
            clean_otp = text.upper().replace('BAFBOT', '').strip()
            
            try:
                await u_client.sign_in(bayanai['phone'], clean_otp, phone_code_hash=bayanai['phone_code_hash'])
                sess_str = u_client.session.save()
                ajiye_session_db(user_id, bayanai['phone'], sess_str)
                active_user_clients[user_id] = u_client
                
                await fara_scraper_injiniya(user_id, sess_str)
                
                await event.respond("🟢 Madallah! Ka yi nasarar Login cikin asusunka.")
                del tsarin_login[user_id]
                await lconfig_cmd(event)
            except SessionPasswordNeededError:
                bayanai['step'] = 'password'
                tsarin_login[user_id] = bayanai
                await event.respond("🔐 Asusunka yana da Verification Mataki na Biyu (2FA). Turo password dinka:")
            except Exception as e:
                await event.respond(f"❌ Kuskure wajen sanya OTP: {str(e)}\n⚠️ Tabbatar ka saka shi a tsarin `BAFBOT12345`")
                await u_client.disconnect()
                del tsarin_login[user_id]
                
        elif bayanai['step'] == 'password':
            u_client = bayanai['client']
            try:
                await u_client.sign_in(password=text)
                sess_str = u_client.session.save()
                ajiye_session_db(user_id, bayanai['phone'], sess_str)
                active_user_clients[user_id] = u_client
                
                await fara_scraper_injiniya(user_id, sess_str)
                
                await event.respond("🟢 Madallah! Ka yi nasarar shiga tare da 2FA password dinka.")
                del tsarin_login[user_id]
                await lconfig_cmd(event)
            except Exception as e:
                await event.respond(f"❌ Kuskure wajen sanya 2FA Password: {str(e)}")
                await u_client.disconnect()
                del tsarin_login[user_id]


# ----------------- LIVE AUTOMATED FORWARDER ENGINE -----------------

async def fara_scraper_injiniya(user_id, session_string):
    if user_id in active_user_clients:
        client = active_user_clients[user_id]
    else:
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        await client.connect()
        active_user_clients[user_id] = client

    try:
        client.list_event_handlers().clear()
    except Exception:
        pass

    async def automated_forward_handler(event):
        config = duba_cikakken_config(user_id)
        if not config or not config['forwarding_status']:
            return
            
        src_id = config['source_channel']
        trg_id = config['target_channel']
        
        if not src_id or not trg_id:
            return
            
        current_chat_id = str(event.chat_id)
        if current_chat_id != src_id and f"-100{current_chat_id}" != src_id and src_id != current_chat_id.replace("-100", ""):
            return

        if event.message.media and not config['media_forwarding']:
            return

        sakon_rubutu = event.message.text or ""
        
        if config['cire_links']:
            sakon_rubutu = re.sub(r'https?://\S+|www\.\S+', '', sakon_rubutu)
        if config['cire_usernames']:
            sakon_rubutu = re.sub(r'@\S+', '', sakon_rubutu)

        if config['mono_text'] and sakon_rubutu:
            sakon_rubutu = f"`{sakon_rubutu}`"

        if config['header_status'] and config['add_header']:
            sakon_rubutu = f"{config['add_header']}\n{sakon_rubutu}"
        if config['add_footer']:
            sakon_rubutu = f"{sakon_rubutu}\n{config['add_footer']}"

        if config['target_delay'] > 0:
            await asyncio.sleep(config['target_delay'])
            
        try:
            target_entity = int(trg_id) if trg_id.replace('-', '').isdigit() else trg_id
            await client.send_message(
                target_entity,
                sakon_rubutu,
                file=event.message.media if config['media_forwarding'] else None,
                link_preview=bool(config['url_preview'])
            )
        except Exception:
            pass

    client.add_event_handler(automated_forward_handler, events.NewMessage)


# Kunna dukkan asusun da ke cikin DB idan bot ya tashi
async def boot_all_active_sessions():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, session_string FROM masu_amfani WHERE session_string IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        uid = row[0]       
        s_str = row[1]     
        try:
            asyncio.create_task(fara_scraper_injiniya(uid, s_str))
        except Exception:
            pass


if __name__ == '__main__':
    bot.loop.run_until_complete(boot_all_active_sessions())
    print("🚀 An gama duka gyare-gyare! Bot din ya tashi lafiya kalau.")
    bot.run_until_disconnected()
