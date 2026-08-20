import asyncio
import os
from aiohttp import web
import edge_tts
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import requests
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import yt_dlp

# ================= আপনার কনফিগারেশন =================
API_ID = 33978180
API_HASH = "b3cb0b0378d532f1a8e7ef1c1fd2e841"
BOT_TOKEN = "8386397372:AAG43W1Eom0ug_kqGBBjypdn2ZwtUUwynNA"
CHAT_ID = -1004378457331  # চ্যানেলের লাইভ আইডি

# সিগন্যাল পাওয়ার এপিআই লিংক
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

# আপনার জেনারেট করা সেশন কোড
SESSION_STRING = "1BVtsOKkBuwX1uqOP1ofqgm7ROMqx34npFQSGIgjHA2q7st-FHQ13qix6nkoYyOJZKiP1vSmNSxmMbLMNxux7beziJtC0j3WchY35xtZ6ohHzi_rEsWxqb408084-hv0OvG1ji-mGki02nnibh3XXMAkgO8r27xkXPR5_FIZHuE2YafTkSj7M7Hl1sIvCzmrnnIYT-D9IPRm4LmPk4z13g068QRxPNsGYXWk7clDZ9_sXfG88VVH4-odA9oTP9144wwBZxlmABl5RZOWx8H4MN6ezX4Zrt_EdRKCS_aCybjGbvESvOIkLtXtpxbeG6Az3uKHYsl1waglqejI2BN4M7nPI8HGvmr4="
# ==================================================

# বট অ্যাকাউন্ট (কমান্ড নেওয়ার জন্য)
bot = TelegramClient("signal_bot_session", API_ID, API_HASH)

# অ্যাসিস্ট্যান্ট ইউজার অ্যাকাউন্ট (লাইভে কথা বলার জন্য)
assistant = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# PyTgCalls এখন আপনার অ্যাসিস্ট্যান্ট অ্যাকাউন্ট দিয়ে লাইভে জয়েন হবে
call_py = PyTgCalls(assistant)

is_running = False
last_period = None
current_pred = None
pending_check = False


# মিষ্টি মেয়েদের ভয়েস তৈরি
async def generate_sweet_girl_voice(text):
    audio_file = "voice_output.raw"
    mp3_file = "temp.mp3"
    comm = edge_tts.Communicate(
        text, voice="bn-BD-NabanitaNeural", rate="+3%", pitch="+3Hz"
    )
    await comm.save(mp3_file)
    os.system(
        f"ffmpeg -y -i {mp3_file} -f s16le -ac 1 -ar 48000 {audio_file} >/dev/null 2>&1"
    )
    return audio_file


# লাইভে কথা বা গান প্লে করা
async def play_in_live(raw_audio_file):
    try:
        await call_py.play(CHAT_ID, MediaStream(raw_audio_file))
    except Exception as e:
        # repr(e) ব্যবহারে করে আসল এররটি সুনির্দিষ্টভাবে লগে প্রিন্ট হবে
        print(f"Play Stream Info: {repr(e)}")


# ১ মিনিটের সিগন্যাল প্রেডিকশন
def calculate_prediction(history_list):
    last5 = [
        "BIG" if int(x["number"]) >= 5 else "SMALL" for x in history_list[:5]
    ]
    if last5[0] == last5[1] == last5[2]:
        return last5[0]
    return "SMALL" if last5[0] == "BIG" else "BIG"


# ১ মিনিটের লাইভ সিগন্যাল লুপ
async def wingo_1min_live_engine():
    global last_period, current_pred, pending_check, is_running
    print(">> ১ মিনিটের WinGo AI লাইভ সিগন্যাল ইঞ্জিন চালু রয়েছে...")

    while is_running:
        try:
            res = requests.get(
                f"{API_URL}?t={int(asyncio.get_event_loop().time() * 1000)}",
                timeout=5,
            )
            data = res.json()
            history = data.get("data", {}).get("list", [])

            if history:
                latest = history[0]
                actual_period = str(latest["issueNumber"])
                actual_num = int(latest["number"])
                actual_size = "BIG" if actual_num >= 5 else "SMALL"

                # উইন / লস লাইভে বলা
                if (
                    pending_check
                    and last_period
                    and last_period != actual_period
                ):
                    if current_pred:
                        if current_pred == actual_size:
                            win_speech = "বুম বুম! কোপ! আমাদের সিগন্যাল ডিরেক্ট উইন হয়েছে! সবাইকে অনেক অনেক অভিনন্দন!"
                            print(f"[WIN] {actual_size}")
                            v_file = await generate_sweet_girl_voice(win_speech)
                            await play_in_live(v_file)
                            await asyncio.sleep(6)
                        else:
                            loss_speech = "কোনো সমস্যা নাই, সবাই মার্টিঙ্গেল লেভেল অনুযায়ী পরের ট্রেডের জন্য প্রস্তুত হন।"
                            print(f"[LOSS] {actual_size}")
                            v_file = await generate_sweet_girl_voice(
                                loss_speech
                            )
                            await play_in_live(v_file)
                            await asyncio.sleep(6)
                    pending_check = False

                # নতুন সিগন্যাল লাইভে ঘোষণা
                if last_period != actual_period:
                    last_period = actual_period
                    current_pred = calculate_prediction(history)
                    pending_check = True

                    last_3_digits = str(int(actual_period) + 1)[-3:]
                    pred_bangla = "বিগ" if current_pred == "BIG" else "স্মল"

                    signal_speech = (
                        f"পিরিয়ড নাম্বার {last_3_digits}। "
                        f"সিগন্যাল হলো {pred_bangla}। সবাই {pred_bangla}-এ ট্রেড ধরুন। "
                        f"সবাই অপেক্ষা করুন, এবার কিন্তু পুরাই কোপ হবে, সবাই উইন হবেন!"
                    )

                    print(
                        f"\n[🚨 লাইভ সিগন্যাল] Period: {last_3_digits} | Signal: {current_pred}"
                    )
                    v_file = await generate_sweet_girl_voice(signal_speech)
                    await play_in_live(v_file)

        except Exception as e:
            print(f"Loop Error: {e}")

        await asyncio.sleep(3)


# Render ক্লাউড অ্যাক্টিভ রাখার সার্ভার
async def keep_alive():
    server = web.Application()
    server.router.add_get("/", lambda r: web.Response(text="Bot is running!"))
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# /start মেসেজ দিলে লাইভে ঢুকে স্বাগতম জানাবে
@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    global is_running
    if is_running:
        await event.respond("⚠️ বট ইতিমধ্যেই লাইভে সক্রিয় আছে!")
        return

    is_running = True
    await event.respond("✅ বট সরাসরি লাইভ স্ট্রিমে যুক্ত হচ্ছে...")

    try:
        # লাইভে ঢুকেই প্রথম ডায়লগ
        welcome_intro = (
            "হ্যালো এভরিওয়ান! আমি হলাম এআই রোবট। "
            "সবাই তাড়াতাড়ি লাইভে চলে আসুন, আমি এই রোবট সবাইকে ১ মিনিটের ১০০% পারফেক্ট সিগন্যাল দিবো।"
        )
        welcome_audio = await generate_sweet_girl_voice(welcome_intro)
        await play_in_live(welcome_audio)
    except Exception as e:
        print(f"Join Error: {e}")

    asyncio.create_task(wingo_1min_live_engine())


# /song কমান্ড দিলে "Ek Din Teri Raahon Mein" গানটি লাইভে বাজবে
@bot.on(events.NewMessage(pattern=r"^/song(?:\s+(.*))?"))
async def song_handler(event):
    query = event.pattern_match.group(1)
    if not query:
        query = "Ek Din Teri Raahon Mein song"

    await event.respond(f"🎵 লাইভ স্ট্রিমে গান বাজানো হচ্ছে: **{query}**...")

    try:
        # ইউটিউব থেকে গানটি প্রসেস করা
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "song.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{query}"])

        # লাইভ স্ট্রিমের অডিও ফরম্যাটে কনভার্ট
        raw_song = "song.raw"
        os.system(
            f"ffmpeg -y -i song.mp3 -f s16le -ac 1 -ar 48000 {raw_song} >/dev/null 2>&1"
        )

        # গান লাইভে প্লে করা
        await play_in_live(raw_song)
        await event.respond(f"▶️ **{query}** গানটি এখন লাইভে চলছে!")
    except Exception as e:
        await event.respond(f"গান প্লে করতে সমস্যা হয়েছে: {e}")


# /stop মেসেজ দিলে লাইভ বন্ধ হবে
@bot.on(events.NewMessage(pattern="/stop"))
async def stop_handler(event):
    global is_running
    is_running = False
    try:
        await call_py.leave_call(CHAT_ID)
        await event.respond("🛑 বট লাইভ ত্যাগ করেছে।")
    except Exception as e:
        print(f"Stop Error: {e}")


async def main():
    await bot.start(bot_token=BOT_TOKEN)  # কমান্ড শোনার জন্য বট চালু হলো
    await assistant.start()  # লাইভে জয়েন হওয়ার জন্য ইউজার আইডি চালু হলো
    await call_py.start()  # কলিং ইঞ্জিন চালু হলো
    await keep_alive()
    print("==================================================")
    print(" বট সম্পূর্ণ রেডি! টেলিগ্রামে /start লিখে দিন।")
    print("==================================================")
    await bot.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
