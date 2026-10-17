import os
import uuid
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import yt_dlp

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

user_data = {}

try:
  bot.remove_webhook()
except Exception:
  pass


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
  bot.reply_to(
      message,
      'Salam! Mənə istənilən media linkini at, formatı seç və dərhal yükləyim!',
  )


@bot.message_handler(func=lambda message: True)
def handle_link(message):
  url = message.text.strip()

  if not url.startswith('http'):
    bot.reply_to(message, 'Zəhmət olmasa etibarlı link göndərin.')
    return

  user_data[message.chat.id] = url

  # Format seçimi üçün düymələr
  markup = InlineKeyboardMarkup()
  btn_video = InlineKeyboardButton(
      '🎬 Video İndir', callback_data='dl_video'
  )
  btn_audio = InlineKeyboardButton(
      '🎵 MP3 İndir', callback_data='dl_audio'
  )
  markup.add(btn_video, btn_audio)

  bot.reply_to(
      message, 'Lütfən yükləmək istədiyiniz formatı seçin:', reply_markup=markup
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def callback_download(call):
  chat_id = call.message.chat.id
  url = user_data.get(chat_id)

  if not url:
    bot.answer_callback_query(
        call.id, 'Link tapılmadı, zəhmət olmasa linki yenidən atın.'
    )
    return

  mode = call.data
  bot.edit_message_text(
      '⏳ Yüklənir, xahiş olunur gözləyin...', chat_id, call.message.message_id
  )

  unique_id = str(uuid.uuid4())
  ydl_opts = {
      'outtmpl': f'downloads/{unique_id}.%(ext)s',
      'geo_bypass': True,
      'nocheckcertificate': True,
      'socket_timeout': 20,
      'extractor_args': {
          'youtube': {'player_client': ['android', 'ios', 'web']}
      },
  }

  if mode == 'dl_audio':
    ydl_opts.update({'format': 'bestaudio/best'})
  else:
    ydl_opts.update({'format': 'best/bestvideo+bestaudio'})

  try:
    os.makedirs('downloads', exist_ok=True)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(url, download=True)
      filename = ydl.prepare_filename(info)

    if not os.path.exists(filename):
      for f in os.listdir('downloads'):
        if f.startswith(unique_id):
          filename = os.path.join('downloads', f)
          break

    with open(filename, 'rb') as f:
      if mode == 'dl_audio':
        bot.send_audio(chat_id, f, caption='🎵 MP3 olaraq yükləndi')
      else:
        bot.send_video(chat_id, f, caption='🎬 Video olaraq yükləndi')

    bot.delete_message(chat_id, call.message.message_id)
    if os.path.exists(filename):
      os.remove(filename)

  except Exception as e:
    bot.edit_message_text(
        f'❌ Xəta baş verdi: {str(e)}', chat_id, call.message.message_id
    )


if __name__ == '__main__':
  print('Bot serverdə işə düşdü...')
  bot.infinity_polling()
