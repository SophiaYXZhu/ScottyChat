
import os
import bs4
import itchat
import collections
import time
import random

import itchat.content as ct

from io import StringIO
import contextlib
import traceback

import cv2
import pandas as pd
import openai
import requests
import shutil

class Config:
    GROUPS = ['Your GC']
    
    # path of image folder
    IMG_PATH = 'Your image cache path'

history = collections.OrderedDict()

# event subscribers

dedup_hack = set()

def get_exec(code):
    s = StringIO()
    with contextlib.redirect_stdout(s):
        try:
            exec(code, {})
        except:
            print(traceback.format_exc())
    return s.getvalue()

@itchat.msg_register(ct.TEXT, isGroupChat=True)
def text_reply(msg):
    #time.sleep(10)
    if msg.user.nickName not in Config.GROUPS or msg.msgId in history:
        return
    try:
        openai.api_key = 'Your OpenAI API'
        messages = [ {"role": "system", "content": 
                    "You are Scotty the CMU mascot. You knows everything about CMU (motto is 'my heart is in my work'). You respond to inputs with an English meme no longer than 5 words in quotation marks. Be humorous yet nerdy. English only. NO EXTRA TEXTS SHOULD BE APPENDED."} ]
        messages.append(
            {"role": "user", "content": msg.content},
        )
        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages
        )
        text = chat.choices[0].message.content
        text = text.split('"')[1]
        print(f"Scotty: {text}")
        if len(text.split(' ')) <= 8:
            try: 
                generator_messages = [ {"role": "system", "content": \
                    "You are an emotion classifier. You should answer the user's input with only ONE single emotional adjective (e.g., happy, sad, angry, confused, etc.) in English only. You should NOT append any punctuations or other texts after the word."} ]
                generator = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=generator_messages
                )
                prompt = generator.choices[0].message.content if generator.choices[0].message.content.isascii() else ""
                prompt = prompt.split(" ")[0]
                if prompt[-1] == '.':
                    prompt = prompt[:len(prompt)-1]
                prompt += " real black Scotty Terrier wearing a thin triangular Tartan scarf"
            except openai.error.RateLimitError:
                print('rate error for emotion generator')
                prompt = "real black Scotty Terrier wearing a thin triangular Tartan scarf"
            print('Image prompt:', prompt)
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="512x512",
            )
            url = response["data"][0]["url"]
            file_name = Config.IMG_PATH+'/tmp.png'
            res = requests.get(url, stream = True)
            if res.status_code == 200:
                with open(file_name,'wb') as f:
                    shutil.copyfileobj(res.raw, f)
                print('Image sucessfully downloaded: ', file_name)
            else:
                print('Image couldn\'t be retrieved')
            path = file_name

            # path = random.choice(Config.IMG_LIST)
            image = cv2.imread(path)
            font = cv2.FONT_HERSHEY_DUPLEX
            def get_optimal_font_scale(text, width):
                for scale in reversed(range(0, 60, 1)):
                    textSize = cv2.getTextSize(text, fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=scale/10, thickness=1)
                    new_width = textSize[0][0]
                    if (new_width <= width):
                        return scale/10
                return 1
            fontScale = get_optimal_font_scale(text, image.shape[0])
            color = (255, 255, 255)
            thickness = 3
            textsize = cv2.getTextSize(text, font, fontScale, 2)[0]
            textX = (image.shape[1] - textsize[0]) // 2
            textY = (image.shape[0] + textsize[1]) // 2
            org = (textX, textY)
            image = cv2.putText(image, text, org, font, 
                            fontScale, color, thickness, cv2.LINE_AA)
            # image = cv2.putText(image,"text",(180,150),cv2.FONT_HERSHEY_COMPLEX,3,(255,255,255),16,cv2.LINE_AA)
            image = cv2.putText(image, text, org, font, 
                            fontScale, (0,0,0), 2, cv2.LINE_AA)
            cv2.imwrite(Config.IMG_PATH+'/temp.png', image)        
            msg.user.send_image(Config.IMG_PATH+'/temp.png')
    except openai.error.RateLimitError:
        print('rate error for Scotty GPT.')
    return

if os.path.exists(Config.IMG_PATH):
    for f in os.listdir(Config.IMG_PATH):
        if f[0] != '.':
            os.remove(os.path.join(Config.IMG_PATH, f))
else:
    os.makedirs(Config.IMG_PATH)

history.clear()

itchat.auto_login(hotReload=True) 
itchat.run()