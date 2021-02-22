#!/usr/bin/python

from pyowm import OWM
from pyowm.utils.config import get_config_from
from datetime import datetime
from matplotlib import dates
import telebot
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import re
import logging
import os
import sys
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

owm_id = config.get('id', 'owm') # -> "value1"
bot_id = config.get('id', 'bot') # -> "value2"
#print config.get('main', 'key3') # -> "value3"

config_dict = get_config_from('config_dict.json')

logging.basicConfig(filename=os.path.basename(sys.argv[0])+'.log', level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

owm = OWM(owm_id, config_dict)
bot = telebot.TeleBot(bot_id)
mgr = owm.weather_manager()

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

            answer = "В городе " + place + " сейчас " + w.detailed_status + "\n"
            answer += "Температура воздуха колеблется в районе " + str(temp) + "℃\n"
            answer += "Скорость ветра достигает " + str(wind_speed) + " м/с\n"

            l = len(forecast)

            x = []
            y = []
            y0 = [0]*l
            ymax = [0]*l
            ymin = [0]*l

            for weather in forecast:
                x.append(datetime.strptime(weather.reference_time('iso')[0:19], '%Y-%m-%d %H:%M:%S'))
                y.append(weather.temperature('celsius')["temp"])

            npmaxy = np.max(y)
            npminy = np.min(y)

            if (npmaxy<0):
                ymax = [0 for i in ymax]
            else:
                ymax = [npmaxy for i in ymax]

            if (npminy>0):
                ymin = [0 for i in ymin]
            else:
                ymin = [npminy for i in ymin]



            plt.figure(figsize=(12, 12))

            fig, ax, = plt.subplots()

            ax.plot(x, y, '-r', alpha = 0.7, label = 't℃', lw = 2, mec='b', mew=2, ms=10)
            ax.plot(x, y0, color = 'black', lw = 0.1)
            ax.plot(x, ymax, alpha = 0)
            ax.plot(x, ymin, alpha = 0)

            ax.fill_between(x, y0, ymin, color = '#539ecd', alpha = 0.2)
            ax.fill_between(x, y0, ymax, color = 'orange', alpha = 0.2)
            fig.suptitle(place + ", прогноз на 5 дней", fontsize=12)
            ax.tick_params(axis = 'x', which = 'major', labelsize = 8, labelrotation = 90)
            ax.tick_params(axis = 'x', which = 'minor', labelsize = 6, labelrotation = 90)
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
