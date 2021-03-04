#!/usr/bin/python

from mpl_toolkits.axes_grid1 import host_subplot
from pyowm import OWM
from pyowm.utils.config import get_config_from
from datetime import datetime, timedelta
from matplotlib import dates
from matplotlib.font_manager import FontProperties
from configparser import ConfigParser
from PIL import Image, ImageDraw
import face_recognition
import mpl_toolkits.axisartist as AA
import telebot
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import re
import logging
import os
import sys


#config init


config = ConfigParser()
config.read('config.ini')
owm_id = config.get('id', 'owm')
bot_id = config.get('id', 'bot')

cam = []
for i in range (4):
    camset = {'login':config.get('cam'+str(i), 'login'), 'password':config.get('cam'+str(i), 'password'), 'ip':config.get('cam'+str(i), 'ip'), 'name':config.get('cam'+str(i), 'name')}
    cam.append(camset)

#logging_level = config.get('log', 'level')

#config owm init
config_dict = get_config_from('config_dict.json')

#setup logging
logging.basicConfig(filename=os.path.basename(sys.argv[0])+'.log', level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

#init
try:
    owm = OWM(owm_id, config_dict)
    bot = telebot.TeleBot(bot_id)
    mgr = owm.weather_manager()
except:
    pass

#извлечение аргументов из комманды от бота
def extract_arg(arg):
    return arg.split(maxsplit=1)[1:]

def get_command(arg):
    return arg.split(' ', 1)[0]

def emonize(x):
    return {
        'ясно': "☀",
        'облачно с прояснениями': "🌤",
        'небольшая облачность': "⛅",
        'переменная облачность': "🌥",
        'пасмурно': "☁",
        'небольшой снег': "🌨",
        'снег': "🌨",
        'дождь': "🌧",
        'небольшой дождь': "🌦",
    }.get(x, "🐕")

def send_camera_image(cam_index, message):
    try:
        msg = cam[cam_index]['name']
        logging.warning('cam'+str(cam_index))
        link = 'http://'+cam[cam_index]['login']+':'+cam[cam_index]['password']+'@'+cam[cam_index]['ip']+'/ISAPI/Streaming/channels/101/picture/'
        imageFile = './img/photo_'+'cam'+str(cam_index)+"_"+str(datetime.timestamp(datetime.now()))+'.jpg'
        os.system('wget '+link+' -O '+imageFile)
        img = open(imageFile, 'rb')
        
        # image = face_recognition.load_image_file(imageFile)
        # face_locations = face_recognition.face_locations(image)
        # face_landmarks_list = face_recognition.face_landmarks(image)
        
        # if (len(face_locations) > 0):
            # msg += ". Найдены лица на фото в количестве: " + str(len(face_locations))
            
            # logging.warning(len(face_locations))
            # pil_image = Image.fromarray(image)
            # draw = ImageDraw.Draw(pil_image)
                
            # for face_location in face_locations:
                # top, right, bottom, left = face_location
                # draw.rectangle(((left, top), (right, bottom)), outline=(0, 0, 255))
                
            # pil_image.save(imageFile)
            # img = open(imageFile, 'rb')
    
        bot.send_photo(message.chat.id, img, caption=msg)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        try:
            bot.reply_to(message, e)
        except:
            pass

# @bot.message_handler(content_types=['photo'])
# def handle_docs_photo(message):
    # try:
        # file_info = bot.get_file(message.photo[len(message.photo)-1].file_id)
        # downloaded_file = bot.download_file(file_info.file_path)

        # src='./downloads/'+file_info.file_path;
        # with open(src, 'wb') as new_file:
           # new_file.write(downloaded_file)
        # bot.reply_to(message, "Ищу лица на фото...") 
        
        # image = face_recognition.load_image_file(src)
        # face_locations = face_recognition.face_locations(image)
        # msg = ""
        
        # if (len(face_locations) > 0):
            # msg += "Найдены лица на фото в количестве: " + str(len(face_locations))
            # logging.warning(len(face_locations))
            # pil_image = Image.fromarray(image)
            # draw = ImageDraw.Draw(pil_image)
            
            # for face_location in face_locations:
                # top, right, bottom, left = face_location
                # draw.rectangle(((left, top), (right, bottom)), outline=(0, 0, 255))
                
            # pil_image.save(src)
            # img = open(src, 'rb')
        
            # bot.send_photo(message.chat.id, img, caption=msg)
        # else:
            # bot.reply_to(message, "Лиц не обнаружено") 

    # except Exception as e:
        # bot.reply_to(message, e)

@bot.message_handler(commands=['cam_room'])
def send_cam1_img(message):
    send_camera_image(1, message)

@bot.message_handler(commands=['cam_box'])
def send_cam3_img(message):
    send_camera_image(3, message)

@bot.message_handler(commands=['cam_gate'])
def send_cam2_img(message):
    send_camera_image(2, message)

@bot.message_handler(commands=['cam_parking'])
def send_cam0_img(message):
    send_camera_image(0, message)


#@bot.message_handler(commands=['weather'])
@bot.message_handler(content_types=['text'])
def message_worker(message):
    _command = get_command(message.text).lower()
    try:
        if (_command == 'погода'):
            t = extract_arg(message.text)
            place = ""
            if not t:
                place = "Владивосток"
            else:
                place = t[0].title()
            if (place):
                logging.warning(place)
                w =  mgr.weather_at_place(place).weather
                forecast = mgr.forecast_at_place(place, '3h').forecast
                temp_min = w.temperature('celsius')["temp_min"]
                temp_max = w.temperature('celsius')["temp_max"]
                temp = w.temperature('celsius')["temp"]
                wind_speed = w.wind()["speed"]
                hum = w.humidity
                pres = w.pressure
                
                answer = "В городе " + place + " сейчас " + w.detailed_status + " " + emonize(w.detailed_status) + "\n"
                answer += "Температура воздуха колеблется в районе " + str(temp) + "℃\n"
                answer += "Скорость ветра достигает " + str(wind_speed) + " м/с\n"
                answer += "Влажность воздуха: " + str(hum) + "%\n"
                answer += "Атмосферное давление: "+str(round(pres.get('press')/1.333223684))+" мм рт. ст."

                l = len(forecast)

                fpres = []
                fdate = [] #forecast date
                ftemp = [] #forecast temperature
                fhum = [] #forecast humidity
                y0 = [0]*l #0-level
                ymax = [0]*l #max level for graph
                ymin = [0]*l #min level for graph
                emo = []
                emodate = []
                snow = []
                rain = []

                #getting five days forecast
                for weather in forecast:
                    fdate.append(datetime.strptime(weather.reference_time('iso')[0:19], '%Y-%m-%d %H:%M:%S'))
                    ftemp.append(weather.temperature('celsius')["temp"])
                    fpres.append(round(weather.pressure.get('sea_level')/1.333223684))
                    emo.append(emonize(str(weather.detailed_status)))
                    emodate.append(datetime.strptime(weather.reference_time('iso')[0:19], '%Y-%m-%d %H:%M:%S')-timedelta(hours=2))
                    fhum.append(weather.humidity)
                    
                    if (weather.snow.get('3h') == None):
                        snow.append(0)
                    else:
                        snow.append(weather.snow.get('3h'))
                        
                    if (weather.rain.get('3h') == None):
                        rain.append(0)
                    else:
                        rain.append(weather.rain.get('3h'))

                #max and min temperature range for coloring graph
                npmaxy = np.max(ftemp)
                npminy = np.min(ftemp)
                if (npmaxy<0):
                    ymax = [0 for i in ymax]
                else:
                    ymax = [npmaxy for i in ymax]

                if (npminy>0):
                    ymin = [0 for i in ymin]
                else:
                    ymin = [npminy for i in ymin]

                #plot init
                plt.figure(figsize=(15, 10))
                fig, ax = plt.subplots(nrows=1, ncols=1)
                ax2 = ax.twinx()
                ax3 = ax.twinx()
                ax5 = ax.twinx()
                ax4 = ax.twinx()

                ax.plot(fdate, ymax, alpha = 0) #max level
                ax.plot(fdate, ymin, alpha = 0) #min level
                ax.plot(fdate, y0, color = 'black', lw = 0.1) #0-level
                ax.fill_between(fdate, y0, ymax, color = 'orange', alpha = 0.2) #warm zone
                ax.fill_between(fdate, y0, ymin, color = '#539ecd', alpha = 0.2) #sub zero

                ax.plot(fdate, ftemp, '-r', alpha = 0.7, label = 't℃', lw = 2, mec='b', mew=2, ms=10) #forecast temperature curve
                ax2.plot(fdate, fhum, '-b', alpha = 0.7, label="Влажность", lw = 1, mec='b', mew=2, ms=10) 
                ax2.yaxis.set_label_position('right') 
                ax4.yaxis.set_label_position('right')
                ax3.yaxis.set_label_position('right')
                ax4.plot(fdate, fpres, '-k', alpha = 0.5, label="Давление", lw = 0.5)
                ax3.bar(fdate, snow, color = 'blue', alpha = 0.3, width = 0.12, label = 'Снег', align='edge')
                ax5.bar(fdate, rain, color = 'blue', alpha = 0.3, width = 0.12, label = 'Дождь', align='edge')

                #emoji, snow, rain bar
                pp = 1
                xx = 1
                flag = 1
                bottom, top = ax.get_ylim()
                for x, val, s, x1, p, r in zip(emodate, emo, snow, fdate, fpres, rain):
                    ax.text(x, bottom, val, {'family':'Noto Sans Symbols2', 'size':10}) #emoji
                    if (p > pp):
                        if (flag != 1):
                            ax4.text(xx, pp, pp, alpha = 0.4, fontsize = 6)
                        flag = 1
                    else:
                        if (p < pp):
                            if (flag != -1):
                                ax4.text(xx, pp, pp, alpha = 0.4, fontsize = 6)
                            flag = -1
                    pp = p
                    xx = x
                    
                    if (s > 0.1):
                        ax3.text(x1, s/2, str(round(s*100)), {'size':6})
                        
                    if (r > 0.1):
                        ax5.text(x1, r/2, str(round(r*100)), {'size':6})
                        
                fig.suptitle(place + ", прогноз на 5 дней", fontsize=12)

                #axis ticks and labels
                ax.tick_params(axis = 'y', colors = 'red')
                ax2.tick_params(axis = 'y', colors = 'blue')

                ax.tick_params(axis = 'x', which = 'major', labelsize = 7, labelrotation = 90, pad = 15) #date on x
                ax.tick_params(axis = 'x', which = 'minor', labelsize = 5, labelrotation = 90, pad = 15) #time on x
                ax.minorticks_on()
                ax2.minorticks_on()

                ax.grid(which='minor', color = 'gray', linestyle = ':',alpha=0.2)
                ax.tick_params(axis = 'x', which = 'minor', labelsize = 6, labelrotation = 90)
                majorfmt = dates.DateFormatter('%m %d')
                minorfmt = dates.DateFormatter('%H:%M')
                ax.xaxis.set_major_formatter(majorfmt)
                ax.xaxis.set_minor_formatter(minorfmt)
                ax.xaxis.set_major_locator(dates.DayLocator())
                ax.xaxis.set_minor_locator(dates.HourLocator(interval=3))

                ax3.get_xaxis().set_visible(False)
                ax3.get_yaxis().set_visible(False)
                ax5.get_xaxis().set_visible(False)
                ax5.get_yaxis().set_visible(False)
                ax4.get_yaxis().set_visible(False)
                ax.margins(0, 0)
                ax2.margins(0, 0)
                ax4.margins(0, 0)

                ax.legend()
                ax2.legend()
                ax4.legend()

                plt.grid(True)
                plt.autoscale(tight=True)
                plt.subplots_adjust(bottom = 0.2, top = 0.92, left = 0.08, right = 0.95)
                fig.canvas.draw()
                fig.tight_layout()

                imageFile = './img/forecast_'+place+"_"+str(datetime.timestamp(datetime.now()))+'.png'

                fig.savefig(imageFile, bbox_inches='tight')

                img = open(imageFile, 'rb')

                bot.send_photo(message.chat.id, img, caption = answer)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        try:
            bot.reply_to(message, e)
        except:
            pass
        pass
try:
	bot.polling(none_stop = True)
except:
	pass
