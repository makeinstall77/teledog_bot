#!/usr/bin/python

from mpl_toolkits.axes_grid1 import host_subplot
from pyowm import OWM
from pyowm.utils.config import get_config_from
from datetime import datetime, timedelta
from matplotlib import dates
from matplotlib.font_manager import FontProperties
from configparser import ConfigParser
#from pandas import DataFrame
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

            #emoji bar
            pp = 1
            xx = 1
            flag = 1
            bottom, top = ax.get_ylim()
            for x, val, s, x1, p in zip(emodate, emo, snow, fdate, fpres):
                ax.text(x, bottom-2.2, val, {'family':'Noto Sans Symbols2', 'size':10})
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
            fig.suptitle(place + ", прогноз на 5 дней", fontsize=12)


            #axis ticks and labels
            ax.tick_params(axis = 'y', colors = 'red')
            ax2.tick_params(axis = 'y', colors = 'blue')

            ax.tick_params(axis = 'x', which = 'major', labelsize = 7, labelrotation = 90) #date on x
            ax.tick_params(axis = 'x', which = 'minor', labelsize = 5, labelrotation = 90) #time on x
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
#            ax3.axis('off') 
            ax3.get_xaxis().set_visible(False)
            ax3.get_yaxis().set_visible(False)
            ax4.get_yaxis().set_visible(False)
            ax.margins(0, 0)
            ax2.margins(0, 0)
#            ax3.margins(-0.4, -0.4)
            ax4.margins(0, 0)

            ax.legend()
            ax2.legend()
            ax4.legend()

            plt.grid(True)
            plt.autoscale(tight=True)
            plt.subplots_adjust(bottom = 0.2, top = 0.92, left = 0.08, right = 0.95)
            fig.canvas.draw()
            fig.tight_layout()

            fig.savefig('fig.png', bbox_inches='tight')

            img = open('fig.png', 'rb')

            bot.send_photo(message.chat.id, img, caption = answer)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(exc_type, fname, exc_tb.tb_lineno)
            pass
        #answer = "Неправильный город"

bot.polling(none_stop = True)
