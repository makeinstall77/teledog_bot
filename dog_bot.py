#!/usr/bin/python

from pyowm import OWM
from pyowm.utils.config import get_config_from
from datetime import datetime, timedelta
from matplotlib import dates
from matplotlib.font_manager import FontProperties
from configparser import ConfigParser
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
#logging_level = config.get('log', 'level')

#config owm init
config_dict = get_config_from('config_dict.json')

#setup logging
logging.basicConfig(filename=os.path.basename(sys.argv[0])+'.log', level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

#init
owm = OWM(owm_id, config_dict)
bot = telebot.TeleBot(bot_id)
mgr = owm.weather_manager()
#prop = FontProperties(fname='/System/Library/Fonts/Apple Color Emoji.ttc')

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

@bot.message_handler(content_types=['text'])


def message_worker(message):
    t = message.text
    place = ""
    if (t.lower() == "погода"):
        place = "Владивосток"
    else:
        if (t.lower().count('погода')):
            t = t.lower().replace('погода', '')
            t = (re.sub(r'\b\w{1,2}\b', '', t))
            place = t.replace(' ', '').title()
    if (place):
        logging.warning(place)
        try:
            observation = mgr.weather_at_place(place)
            w = observation.weather
            forecaster = mgr.forecast_at_place(place, '3h')
            forecast = forecaster.forecast
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

            fdate = [] #forecast date
            ftemp = [] #forecast temperature
            y0 = [0]*l #0-level
            ymax = [0]*l #max level for graph
            ymin = [0]*l #min level for graph
            emo = []
            emodate = []
            #getting five days forecast
            for weather in forecast:
                fdate.append(datetime.strptime(weather.reference_time('iso')[0:19], '%Y-%m-%d %H:%M:%S'))
                ftemp.append(weather.temperature('celsius')["temp"])
                print(str(weather.detailed_status))
                emo.append(emonize(str(weather.detailed_status)))
                emodate.append(datetime.strptime(weather.reference_time('iso')[0:19], '%Y-%m-%d %H:%M:%S')-timedelta(hours=2))
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
            plt.figure(figsize=(17, 17))
            fig, ax, = plt.subplots()

            ax.plot(fdate, ftemp, '-r', alpha = 0.7, label = 't℃', lw = 2, mec='b', mew=2, ms=10) #forecast temperature curve
            ax.plot(fdate, y0, color = 'black', lw = 0.1) #0-level
            ax.plot(fdate, ymax, alpha = 0) #max level
            ax.plot(fdate, ymin, alpha = 0) #min level

            ax.fill_between(fdate, y0, ymin, color = '#539ecd', alpha = 0.2) #sub zero
            ax.fill_between(fdate, y0, ymax, color = 'orange', alpha = 0.2) #warm zone

            print(fdate)
            print(emodate)

            for x, val in zip(emodate, emo):
                plt.text(x, npminy-2, val, {'family':'Noto Sans Symbols2'})

            fig.suptitle(place + ", прогноз на 5 дней", fontsize=12)

            #axis ticks and labels
            ax.tick_params(axis = 'x', which = 'major', labelsize = 8, labelrotation = 90) #date on x
            ax.tick_params(axis = 'x', which = 'minor', labelsize = 6, labelrotation = 90) #time on x
            ax.minorticks_on()
            ax.grid(which='minor', color = 'gray', linestyle = ':',alpha=0.2)
            ax.tick_params(axis = 'x', which = 'minor', labelsize = 6, labelrotation = 90)
            majorfmt = dates.DateFormatter('%m %d')
            minorfmt = dates.DateFormatter('%H:%M')
            ax.xaxis.set_major_formatter(majorfmt)
            ax.xaxis.set_minor_formatter(minorfmt)
            ax.xaxis.set_major_locator(dates.DayLocator())
            ax.xaxis.set_minor_locator(dates.HourLocator(interval=3))

            plt.margins(0, 0)
            plt.legend()
            plt.grid(True)

            fig.savefig('fig.png')
            img = open('fig.png', 'rb')

            bot.send_photo(message.chat.id, img, caption = answer)
        except Exception as e:
            logging.error(e)
            pass
        #answer = "Неправильный город"

bot.polling(none_stop = True)
