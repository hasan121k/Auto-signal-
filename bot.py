import asyncio
import os
from aiohttp import web
import edge_tts
from pyrogram import Client, filters
import requests

# নতুন ও পুরনো উভয় ভার্সনের জন্য অটোমেটিক ইমপোর্ট হ্যান্ডলার
try:
    from pytgcalls import PyTgCalls
except ImportError:
    from pytgcalls import Client as PyTgCalls

try:
    from pytgcalls.types import MediaStream
except ImportError:
    try:
        from pytgcalls.types import AudioPiped as MediaStream
    except ImportError:
        pass

# ================= আপনার কনফিগারেশন =================
API_ID = 33978180
API_HASH = "b3cb0b0378d532f1a8e7ef1c1fd2e841"
BOT_TOKEN = "8386397372:AAG43W1Eom0ug_kqGBBjypdn2ZwtUUwynNA"
CHAT_ID = -1004378457331

# ১ মিনিটের অফিসিয়াল WinGo API
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"
# ==================================================

app = Client("signal_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call_py = PyTgCalls(app)

is_running = False
last_period = None
current_pred = None
pending_check = False


# মিষ্টি বাংলাদেশি মেয়েদের কণ্ঠ
async def generate_girl_voice(text):
    audio_file = "voice_output.mp3"
    communicate = edge_tts.Communicate(
        text, voice="bn-BD-NabanitaNeural", rate="+5%", pitch="+2Hz"
    )
    await communicate.save(audio_file)
    return audio_file


# লাইভে ভয়েস প্লে
async def play_in_live(audio_file):
    try:
        await call_py.play(CHAT_ID, MediaStream(audio_file))
    except Exception as e:
        print(f"ভয়েস প্লে এরর: {e}")


# ১ মিনিটের সিগন্যাল প্রেডিকশন
def calculate_prediction(history_list):
    last5_sizes = [
        "BIG" if int(x["number"]) >= 5 else "SMALL" for x in history_list[:5]
    ]
    if last5_sizes[0] == last5_sizes[1] == last5_sizes[2]:
        return last5_sizes[0]
    return "SMALL" if last5_sizes[0] == "BIG" else "BIG"


# ১ মিনিটের অটোমেটিক সিগন্যাল ইঞ্জিন
async def wingo_1min_engine():
    global last_period, current_pred, pending_check, is_running
    print(">> ১ মিনিটের WinGo AI লাইভ সিগন্যাল চালু হয়েছে...")

    while is_running:
        try:
            res = requests.get(f"{API_URL}?t={int(asyncio.get_event_loop().time() * 1000)}", timeout=5)
            data = res.json()
            history = data.get("data", {}).get("list", [])

            if history:
                latest = history[0]
                actual_period = str(latest["issueNumber"])
                actual_num = int(latest["number"])
                actual_size = "BIG" if actual_num >= 5 else "SMALL"

                # উইন / লস চেক
                if pending_check and last_period and last_period != actual_period:
                    if current_pred:
                        if current_pred == actual_size:
                            win_msg = "বুম বুম! কোপ! আমাদের সিগন্যাল ডিরেক্ট উইন হয়েছে! সবাইকে অনেক অভিনন্দন!"
                            print(f"[RESULT] WIN: {actual_size}")
                            v_file = await generate_girl_voice(win_msg)
                            await play_in_live(v_file)
                            await asyncio.sleep(6)
                        else:
                            loss_msg = "কোনো সমস্যা নাই, সবাই মার্টিঙ্গেল লেভেল অনুযায়ী পরের ট্রেডের জন্য রেডি হন।"
                            print(f"[RESULT] LOSS: {actual_size}")
                            v_file = await generate_girl_voice(loss_msg)
                            await play_in_live(v_file)
                            await asyncio.sleep(6)
                    pending_check = False

                # নতুন সিগন্যাল তৈরি
                if last_period != actual_period:
                    last_period = actual_period
                    current_pred = calculate_prediction(history)
                    pending_check = True

                    next_period_full = str(int(actual_period) + 1)
                    last_3_digits = next_period_full[-3:]
                    pred_bangla = "বিগ" if current_pred == "BIG" else "স্মল"

                    signal_speech = (
                        f"পিরিয়ড নাম্বার {last_3_digits}। "
                        f"সিগন্যাল হলো {pred_bangla}। সবাই {pred_bangla}-এ ট্রেড ধরুন। "
                        f"সবাই অপেক্ষা করুন, এবার কোপ হবে, সবাই উইন হবেন!"
                    )

                    print(f"\n[🚨 নতুন সিগন্যাল] Period: {last_3_digits} | Signal: {current_pred}")

                    voice_path = await generate_girl_voice(signal_speech)
                    await play_in_live(voice_path)

        except Exception as err:
            print(f"API/Signal Error: {err}")

        await asyncio.sleep(3)


# Render স্লিপ প্রিভেন্ট সার্ভার
async def keep_alive():
    server = web.Application()
    server.router.add_get("/", lambda r: web.Response(text="Bot is running!"))
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# /start কমান্ড
@app.on_message(filters.command("start"))
async def start_handler(client, message):
    global is_running
    if is_running:
        await message.reply_text("⚠️ বট ইতিমধ্যেই লাইভে সক্রিয় আছে!")
        return

    is_running = True
    await message.reply_text("✅ ১ মিনিটের WinGo AI বট লাইভে জয়েন হচ্ছে...")

    try:
        welcome_audio = await generate_girl_voice(
            "হ্যালো এভরিওয়ান! আমাদের ভিআইপি সিগন্যাল লাইভ স্ট্রিমে স্বাগতম।"
        )
        await play_in_live(welcome_audio)
    except Exception as e:
        print(f"Welcome Audio Error: {e}")

    asyncio.create_task(wingo_1min_engine())


# /stop কমান্ড
@app.on_message(filters.command("stop"))
async def stop_handler(client, message):
    global is_running
    is_running = False
    try:
        await call_py.leave_call(CHAT_ID)
        await message.reply_text("🛑 লাইভ স্ট্রিম বট বন্ধ করা হয়েছে।")
    except Exception as e:
        print(f"Stop Error: {e}")


async def main():
    await app.start()
    await call_py.start()
    await keep_alive()
    print("==================================================")
    print(" ১ মিনিটের WinGo AI প্রেডিক্টর বট লাইভ শুরু করার জন্য রেডি!")
    print(" টেলিগ্রামে /start লিখে দিন।")
    print("==================================================")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
