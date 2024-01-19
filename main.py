import os
import telebot
from telebot import types
from instagrapi import Client
from datetime import datetime
import requests
import json
import time
from server import server

headers = {
    'Cookie': 'dpr=1.25; mid=ZaovZwALAAFd9Nr_0zaDa75IWLmx; ig_did=F8FD23C6-A66B-4D27-8B7B-D6D401500756; datr=Zy-qZU3nWQhUOeNsXIWp3Puz; ig_nrcb=1; csrftoken=ewY6Ejs5KxWkQei4a1YRvNNGc9LKAWNl; ds_user_id=59723618514; sessionid=59723618514%3AjolXz8m8clrBEJ%3A15%3AAYewOkzOCotdhBlK1z4X9enmA-P7byR7zYPIIRvmKg; rur="LDC\05459723618514\0541737188306:01f77caa3b25120d37ae290be9ff9623e5304e90305b2e777c827d9c1d7e3e984a28af28"',
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_6 like Mac OS X) AppleWebKit/604.5.6 (KHTML, like Gecko) Mobile/15D100 Instagram 37.0.0.9.96 (iPhone7,2; iOS 11_2_6; pt_PT; pt-PT; scale=2.34; gamut=normal; 750x1331)',
    }

API_KEY = os.environ.get('API_KEY')
MEDIA_URL = os.environ.get('MEDIA_URL')
USERS_URL = os.environ.get('USERS_URL')
INSTA_URL = os.environ.get('INSTA_URL')
CHATID = os.environ.get('CHATID')

bot = telebot.TeleBot(API_KEY)
cl = Client()

server()

def chat(message):
    userId = message.chat.id
    nameUser = str(message.chat.first_name) + ' ' + str(message.chat.last_name)
    username = message.chat.username
    text = message.text
    date = datetime.now()
    data = f'User id: {userId}\nUsername: @{username}\nName: {nameUser}\nText: {text}\nDate: {date}'
    bot.send_message(chat_id=CHATID, text=data)
    
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_chat_action(message.chat.id, action='typing')
    smsg = "Botista is up!\nSend me an Instagram link (Photo, Reel, IGTV, Album) and I will download it for you <3"
    bot.reply_to(message, smsg)
    chat(message)

@bot.message_handler(commands=['contact'])
def contact(message):
    bot.send_chat_action(message.chat.id, action='typing')
    smsg = "Contact bot creator to report a bug or suggest a feature:\n@TheAtef\nhttps://t.me/TheAtef"
    bot.reply_to(message, smsg, disable_web_page_preview=True)
    chat(message)

@bot.message_handler(commands=['donate'])
def donate(message):
    bot.send_chat_action(message.chat.id, action='typing')
    smsg = "Thanks for considering donating!\nHere is my Buy Me a Coffee link:\nhttps://www.buymeacoffee.com/TheAtef"
    bot.reply_to(message, smsg, disable_web_page_preview=True)
    chat(message)

@bot.message_handler(commands=['pfp'])
def start(message):
    chat(message)
    bot.send_chat_action(message.chat.id, action='upload_photo')
    if message.text == "/pfp":
        smsg = "Send command with the username.\nExample: /pfp @atefshaban"
        bot.reply_to(message, smsg)
    if "@" in message.text:
        try:
            bot.send_chat_action(message.chat.id, 'upload_photo')
            username = message.text.removeprefix('/pfp @')
            url = f'{USERS_URL}{username}/usernameinfo/'
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                parsed_json = json.loads(r.text)['user']
                pk = str(parsed_json['pk'])
                name = parsed_json['full_name']
                followers = parsed_json['follower_count']
                followings = parsed_json['following_count']
                bio = parsed_json['biography']
                caption = f"Name: {name}\nUsername: <a href='{INSTA_URL}{username}/'>@{username}</a>\nFollowers: {followers}\nFollowing: {followings}\nBio:\n{bio}"
                pic = parsed_json['hd_profile_pic_url_info']['url']
                bot.send_photo(message.chat.id, pic, caption, reply_to_message_id=message.message_id, parse_mode = 'HTML')
        except Exception:
            bot.reply_to(message, "Unvalid username.")

@bot.message_handler(func=lambda m: True)
def get_media(message):
    chat(message)
    delete = bot.reply_to(message, 'Processing...')
    if "instagram.com/" in message.text:
        pk = cl.media_pk_from_url(message.text)
        url = f'{MEDIA_URL}{pk}/info/'
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            try:
                parsed_json = json.loads(r.text)["items"].pop()
                media_type = parsed_json['media_type']
            except Exception:
                media_type = None
                bot.reply_to(message, "Sorry, something went wrong.")
        else:
            bot.delete_message(message.chat.id, delete.message_id, timeout=10)
            media_type = None
            bot.reply_to(message, "Invalid, please send a public Instagram link.")
    else:
        bot.delete_message(message.chat.id, delete.message_id, timeout=10)
        media_type = None
        bot.reply_to(message, "Invalid, please send a public Instagram link.")
    
    if media_type == 2:
        bot.delete_message(message.chat.id, delete.message_id, timeout=10)
        bot.send_chat_action(message.chat.id, action='upload_video')
        video_url = sorted(parsed_json["video_versions"], key=lambda o: o["height"] * o["width"])[-1]["url"]
        caption = f"User: <a href='{INSTA_URL}{parsed_json['user']['username']}/'>@{parsed_json['user']['username']}</a>\n\nCaption:\n{parsed_json['caption']['text']}\n\nPlays: {parsed_json['play_count']:,}\nLikes: {parsed_json['like_count']:,}"
        try:
            if len(caption) <= 1024:
                bot.send_video(chat_id=message.chat.id, video=video_url, timeout=200, caption=caption, reply_to_message_id=message.message_id, parse_mode='HTML')
            else: 
                bot.send_video(chat_id=message.chat.id, video=video_url, timeout=200, reply_to_message_id=message.message_id)
                bot.send_message(message.chat.id, caption, 'HTML')
        except Exception as e:
            bot.reply_to(message, "Sorry, something went wrong.")

    if media_type == 1:
        bot.delete_message(message.chat.id, delete.message_id, timeout=10)
        bot.send_chat_action(message.chat.id, action='upload_photo')
        image = sorted(parsed_json["image_versions2"]["candidates"],key=lambda o: o["height"] * o["width"],)[-1]["url"]
        caption = f"User: <a href='{INSTA_URL}{parsed_json['user']['username']}/'>@{parsed_json['user']['username']}</a>\n\nCaption:\n{parsed_json['caption']['text']}\n\nLikes: {parsed_json['like_count']:,}"
        try:
            if len(caption) <= 1024:
                bot.send_photo(chat_id=message.chat.id, photo=image, timeout=200, caption=caption, reply_to_message_id=message.message_id, parse_mode='HTML')
            else:
                bot.send_photo(chat_id=message.chat.id, photo=image, timeout=200, reply_to_message_id=message.message_id)
                bot.send_message(message.chat.id, caption, 'HTML')
        except Exception as e:
            bot.reply_to(message, "Sorry, something went wrong.")

    if media_type == 8:
        bot.delete_message(message.chat.id, delete.message_id, timeout=10)
        caption = f"User: <a href='{INSTA_URL}{parsed_json['user']['username']}/'>@{parsed_json['user']['username']}</a>\n\nCaption:\n{parsed_json['caption']['text']}\n\nLikes: {parsed_json['like_count']:,}"
        bot.send_message(message.chat.id, caption, 'HTML', reply_to_message_id=message.message_id)
        for item in parsed_json['carousel_media']:
            if item['media_type'] == 1:
                try:
                    bot.send_chat_action(message.chat.id, action='upload_photo')
                    image = sorted(item["image_versions2"]["candidates"], key=lambda o: o["height"] * o["width"])[-1]["url"]
                    bot.send_photo(message.chat.id, image)
                except Exception:
                    bot.send_message(message.chat.id, 'Sorry, couldn\'t send photo.')
            if item['media_type'] == 2:
                try:
                    bot.send_chat_action(message.chat.id, action='upload_video')
                    video_url = sorted(item["video_versions"], key=lambda o: o["height"] * o["width"])[-1]["url"]
                    bot.send_video(message.chat.id, video_url)
                except Exception:
                    bot.send_message(message.chat.id, 'Sorry, couldn\'t send video.')

print('Bot is running...')
while True:
    try:
        bot.infinity_polling()
    except Exception as e:
        print(e)
        time.sleep(10)
