import telebot
from telebot import types
from enum import Enum
import sqlite3
import dbcontrol as dbc
import devmode as dm
import credit
from datetime import datetime
from dateutil.relativedelta import relativedelta

# for env
import os
from dotenv import load_dotenv, dotenv_values
load_dotenv()

date_format = "%d.%m.%Y"

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))

dbc.db_connect()
dbc.db_new()

# Developer tools

@bot.message_handler(commands=['dev','dbnew','dbdrop','dbinfo','dbadd','dbedit','regnew','selfreg','test'])
def dev_command(message):
	if dm.is_dev(message.chat.id) == False:
		return
	match message.text[1:]:
		case 'dev':
			bot.send_message(message.chat.id, 'Available commands:\nDatabase management\n/dbinfo\n/dbadd\n/dbdrop\n/dbnew\n/dbedit\nUser management\n/regnew\n/selfreg\nOther\n/test')
		case 'dbnew':
			dbc.db_new()
		case 'dbdrop':
			dbc.db_drop()
		case 'dbinfo':
			dbc.db_show_info(bot, message)
		case 'dbadd':
			bot.send_message(message.chat.id, 'Format: datatype user value')
			bot.register_next_step_handler(message, h_db_add)
		case 'dbedit':
			bot.send_message(message.chat.id, 'Format: datatype user new_value')
			bot.register_next_step_handler(message, h_db_edit)
		case 'regnew':
			bot.send_message(message.chat.id, 'Enter new name and ID')
			bot.register_next_step_handler(message, h_db_reg)
		case 'selfreg':
			dbc.db_add_essentials(dm.dev_id(), 'Developer')
		case 'test':
			return

def h_db_add(message):
	dbc.db_add_elem(message.text.split())

def h_db_reg(message):
	txt = message.text.split()
	dbc.db_add_essentials(txt[1], txt[0])

def h_db_edit(message):
	txt = message.text.split()
	dbc.db_change(txt[0], txt[1], txt[2])

# User control

def check_verification(chat_id):
	if dbc.db_get('Verification', chat_id) == 'Success':
		return True
	else:
		return False

# Bot functions

@bot.message_handler(commands=['start'])
def start(message):
	bank_name = os.getenv("BANK_NAME")
	if not check_verification(message.chat.id):
		bot.send_message(message.chat.id, 'Вы не зарегестрированы. Запросите создание аккаунта.')
	else:
		bot.send_message(message.chat.id, f'Вас приветствует {bank_name}.\nНачните ввод команды с /')

@bot.message_handler(commands=['credit'])
def credit_main(message):
	if not check_verification(message.chat.id):
		return
	if credit.can(dbc.db_get('ActiveCredit', message.chat.id)) == True:
		bot.send_message(message.chat.id, 'Введите сумму кредита:')
		bot.register_next_step_handler(message, new_credit)
	else:
		bot.send_message(message.chat.id, 'Невозможно взять новый кредит пока не выплачен предыдущий.')

def new_credit(message):
	amount = message.text
	is_amount_ok = True
	if amount.isnumeric() == False:
		bot.send_message(message.chat.id, 'Неверное число')
		is_amount_ok = False
		bot.register_next_step_handler(message, new_credit)
		return
	if int(amount) <= 0:
		bot.send_message(message.chat.id, 'Неверное число')
		is_amount_ok = False
		bot.register_next_step_handler(message, new_credit)
		return
	if is_amount_ok == True:
		markup = types.InlineKeyboardMarkup()
		markup.add(types.InlineKeyboardButton('Подтвердить', callback_data = 'request_credit'))
		markup.add(types.InlineKeyboardButton('Изменить сумму', callback_data = 'change_credit'))
		markup.add(types.InlineKeyboardButton('Отменить', callback_data = 'cancel_credit'))
		bot.send_message(message.chat.id, f'Вы собираетесь взять кредит на {amount} руб.', reply_markup = markup)
		dbc.db_change('ExpectedCredit', message.chat.id, amount)

def get_credit_request(who):
	markup = types.InlineKeyboardMarkup()
	yes = types.InlineKeyboardButton('Одобрить', callback_data='yes_credit')
	no = types.InlineKeyboardButton('Отклонить', callback_data='no_credit')
	markup.row(yes, no)
	amount = dbc.db_get('ExpectedCredit', who)
	who_name = dbc.db_get('IDtoName', who)
	bot.send_message(dm.dev_id(), f'Пользователь {who_name} хочет кредит на {amount} руб.', reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: True)
def callback_credit(callback):
# Dev side
	if callback.data == 'yes_credit':
		# Индексы из сообщения в функции get_credit_request()
		who_id = dbc.db_name_to_id(callback.message.text.split()[1])
		amount = callback.message.text.split()[5]
		bot.edit_message_text('Кредит одобрен.', callback.message.chat.id, callback.message.message_id)
		dbc.db_change('CreditInitial', who_id, amount)
		dbc.db_change('ActiveCredit', who_id, 'Yes')
		dbc.db_change('ExpectedCredit', who_id, 'None')
		dbc.db_change('CreditDay', who_id, datetime.today().strftime(date_format))
		dbc.db_change('InterestDay', who_id, datetime.strftime(datetime.today() + relativedelta(days = credit.calculate_interest_days(amount)), date_format))
	if callback.data == 'no_credit':
		bot.edit_message_text('Кредит отклонен.', callback.message.chat.id, callback.message.message_id)
# User side
	match callback.data:
		case 'request_credit':
			bot.edit_message_text('Заявка на кредит отправлена...', callback.message.chat.id, callback.message.message_id)
			get_credit_request(callback.message.chat.id)
		case 'change_credit':
			bot.edit_message_text('Введите новую сумму кредита.', callback.message.chat.id, callback.message.message_id)
			bot.register_next_step_handler(callback.message, new_credit)
		case 'cancel_credit':
			bot.edit_message_text('Взятие кредита отменено.',callback.message.chat.id, callback.message.message_id)
			dbc.db_change('ExpectedCredit', callback.message.chat.id, 'None')

@bot.message_handler(commands=['details'])
def details_main(message):
	if not check_verification(message.chat.id):
		return
	if dbc.db_get('ActiveCredit', message.chat.id) == 'No':
		bot.send_message(message.chat.id, 'У вас нет активного кредита.')
	else:
		initial = dbc.db_get('CreditInitial', message.chat.id)
		interest = dbc.db_get('CreditInterest', message.chat.id)
		credit_day = dbc.db_get('CreditDay', message.chat.id)
		interest_day = dbc.db_get('InterestDay', message.chat.id)
		days_delta = datetime.today() - datetime.strptime(interest_day, date_format)
		interest_days = abs(days_delta.days)
		amount = credit.calculate_total(initial, interest, interest_days) 
		dbc.db_change('CreditAmount', message.chat.id, amount)
		bot.send_message(message.chat.id, f'У вас есть активный кредит.\nВзят {credit_day}\nПервоначальная сумма: {initial}\nТекущая сумма: {amount:.2f}\nПроцент за день: {interest}%\nПроценты начисляются с {interest_day}\nПроцентных дней: {interest_days}')

#@bot.message_handler()
#def main(message):

bot.polling(none_stop=True)
dbc.db_close()
