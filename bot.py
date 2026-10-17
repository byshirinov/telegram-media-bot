import os
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import yt_dlp

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

user_data = {}


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
  bot.reply_to(
      message,
      'Salam! Mənə istənilən media linkini (YouTube, Instagram, TikTok və s.)'
      ' at, ardından yükləmə formatını seç!',
  )


@bot.message_handler(func=lambda message: True)
def handle_link(message):
  url = message.text.strip()

  if not url.startswith('http'):
    bot.reply_to(
        message, 'Zəhmət olmasa etibarlı bir media linki göndərin.'
    )
    return

  user_data[message.chat.id] = url

  markup = InlineKeyboardMarkup()
  btn_video = InlineKeyboardButton(
      '🎬 Video İndir', callback_data='dl_video'
  )
  btn_audio = InlineKeyboardButton(
      '🎵 MP3 (Səs) İndir', callback_data='dl_audio'
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

  ydl_opts = {
      'outtmpl': 'downloads/%(id)s.%(ext)s',
      'geo_bypass': True,
      'nocheckcertificate': True,
      'quiet': True,
      'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web']}},
  }

  if mode == 'dl_audio':
    ydl_opts.update({
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    })
  else:
    ydl_opts.update({
        'format': 'best/bestvideo+bestaudio',
    })

  try:
    os.makedirs('downloads', exist_ok=True)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(url, download=True)
      filename = ydl.prepare_filename(info)
      if mode == 'dl_audio':
        filename = os.path.splitext(filename)[0] + '.mp3'

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
  
