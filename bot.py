import os
import uuid
import telebot
import yt_dlp

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

try:
  bot.remove_webhook()
except Exception:
  pass


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
  bot.reply_to(
      message,
      'Salam! Mənə istənilən media linkini at, dərhal yükləyim!',
  )


@bot.message_handler(func=lambda message: True)
def handle_link(message):
  url = message.text.strip()

  if not url.startswith('http'):
    bot.reply_to(message, 'Zəhmət olmasa etibarlı link göndərin.')
    return

  msg = bot.reply_to(message, '⏳ Media yüklənir, zəhmət olmasa gözləyin...')

  # Fayl adı uzunluğu xətasını qəti olaraq önləmək üçün unikal qısa ID yaradırıq
  unique_filename = str(uuid.uuid4())

  ydl_opts = {
      'outtmpl': f'downloads/{unique_filename}.%(ext)s',
      'format': 'best',
      'noplaylist': True,
      'geo_bypass': True,
      'nocheckcertificate': True,
      'socket_timeout': 20,
      'extractor_args': {
          'youtube': {'player_client': ['android', 'ios', 'web']}
      },
  }

  try:
    os.makedirs('downloads', exist_ok=True)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(url, download=True)
      filename = ydl.prepare_filename(info)

    # Əgər fayl başqa uzantı ilə yadda qalıbsa, qovluqdan tapırıq
    if not os.path.exists(filename):
      for f in os.listdir('downloads'):
        if f.startswith(unique_filename):
          filename = os.path.join('downloads', f)
          break

    with open(filename, 'rb') as f:
      if filename.endswith(('.mp3', '.m4a', '.wav', '.flac', '.opus')):
        bot.send_audio(message.chat.id, f, caption='🎵 Səs faylı yükləndi')
      else:
        bot.send_video(message.chat.id, f, caption='🎬 Video yükləndi')

    bot.delete_message(message.chat.id, msg.message_id)
    if os.path.exists(filename):
      os.remove(filename)

  except Exception as e:
    bot.edit_message_text(
        f'❌ Xəta baş verdi: {str(e)}', message.chat.id, msg.message_id
    )


if __name__ == '__main__':
  print('Bot serverdə işə düşdü...')
  bot.infinity_polling()
  
