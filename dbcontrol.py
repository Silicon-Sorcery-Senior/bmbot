import sqlite3

conn = None
cur = None

# Подключиться к базе данных
def db_connect():
	global conn
	global cur
	conn = sqlite3.connect('database.sql', check_same_thread = False)
	cur = conn.cursor()

# Отключиться от базы данных
def db_close():
	global conn
	global cur
	cur.close()
	conn.close()

# Создать новую базу данных
def db_new():
	cur.execute('CREATE TABLE IF NOT EXISTS alldata (rowid INTEGER PRIMARY KEY, datatype VARCHAR(42), user VARCHAR(42), value VARCHAR(42))')
	conn.commit()

# Показать базу данных
def db_show_info(bot, message):
	try:
		cur.execute('SELECT * FROM alldata')
	except:
		bot.send_message(message.chat.id, 'Database does not exist.')
	dbdata = cur.fetchall()
	info = ''
	for el in dbdata:
		info += f'ID: {el[0]}   datatype: {el[1]}   user: {el[2]}   value: {el[3]}\n'
	if info == '':
		info = 'Database is empty.'
	bot.send_message(message.chat.id, info)

# Добавить элемент в базу данных
def db_add_elem(elem):
	cur.execute(f'INSERT INTO alldata (datatype, user, value) VALUES ("{elem[0]}", "{elem[1]}", "{elem[2]}")')
	conn.commit()

# Удалить базу данных
def db_drop():
	cur.execute('DROP TABLE alldata')
	conn.commit()

# Добавить необходимые данные пользователя
def db_add_essentials(chat_id, name):
#	db_add_elem(['',chat_id,])
	db_add_elem(['Verification',chat_id,'Success'])
	db_add_elem(['IDtoName',chat_id,name])
	db_add_elem(['ActiveCredit',chat_id,'No'])
	db_add_elem(['CreditAmount',chat_id,'0'])
	db_add_elem(['TrustIndex',chat_id,'1'])
	db_add_elem(['CreditInterest',chat_id,'1'])
	db_add_elem(['CreditDay',chat_id,'01.01.1970'])
	db_add_elem(['InterestDay',chat_id,'01.01.1970'])
	db_add_elem(['ExpectedCredit',chat_id,'None'])
	db_add_elem(['CreditInitial',chat_id,'0'])

# Получить данные из базы данных
def db_get(datatype, chat_id):
	cur.execute(f'SELECT * FROM alldata WHERE datatype = "{datatype}" AND user = "{chat_id}"')
	dbdata = cur.fetchone()
	if not dbdata:
		return 'NotFound'
	conn.commit()
	return dbdata[3]

# Изменить данные в базе данных
def db_change(datatype, chat_id, value):
	cur.execute(f'UPDATE alldata SET value = "{value}" WHERE datatype = "{datatype}" AND user = "{chat_id}"')
	conn.commit()

# Поиск chat.id по имени
def db_name_to_id(name):
	cur.execute(f'SELECT * FROM alldata WHERE datatype = "IDtoName" AND value = "{name}"')
	dbdata = cur.fetchone()
	if not dbdata:
		return 'NotFound'
	conn.commit()
	return dbdata[2]

