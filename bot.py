
import os
import telebot
import yt_dlp

# Token server tənzimləmələrindən (Environment Variable) götürüləcək
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
  bot.reply_to(
      message,
      'Salam! Mənə istənilən linki (YouTube, Instagram, TikTok və s.) at, mən'
      ' də sənə medianı yükləyib göndərim.',
  )


@bot.message_handler(func=lambda message: True)
def download_media(message):
  url = message.text.strip()

  if not url.startswith('http'):
    bot.reply_to(
        message, 'Zəhmət olmasa etibarlı bir media linki göndərin.'
    )
    return

  msg = bot.reply_to(message, '⏳ Media yüklənir, gözləyin...')

  ydl_opts = {
      'outtmpl': 'downloads/%(id)s.%(ext)s',
      'format': 'best',
  }

  try:
    os.makedirs('downloads', exist_ok=True)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(url, download=True)
      filename = ydl.prepare_filename(info)

    with open(filename, 'rb') as f:
      if filename.endswith(('.mp4', '.mkv', '.webm', '.mov')):
        bot.send_video(message.chat.id, f)
      elif filename.endswith(('.mp3', '.m4a', '.wav', '.flac')):
        bot.send_audio(message.chat.id, f)
      else:
        bot.send_document(message.chat.id, f)

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
  
