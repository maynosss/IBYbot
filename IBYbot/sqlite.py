import sqlite3 as sq

#class IBYdb:

async def db_start():
    global db, cur

    db = sq.connect('ibydb.db')
    cur = db.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS profile(user_id TEXT PRIMARY KEY, profilename TEXT UNIQUE NOT NULL, birthday TEXT NOT NULL, profilenumber TEXT UNIQUE NOT NULL)")

    db.commit()

async def create_profile(user_id):
    user = cur.execute("SELECT 1 FROM profile WHERE user_id == '{key}'".format(key=user_id)).fetchone()
    if not user:
        cur.execute("INSERT INTO profile VALUES(?, ?, ?, ?)", (user_id, '', '', ''))
        db.commit()


async def edit_profile(state, user_id):
    async with state.proxy() as data:
        cur.execute("UPDATE profile SET name = '{}', birthday = '{}', number = '{}' WHERE user_id == '{}'".format(
            user_id, data['name'], data['birthday'], data['number']))
        db.commit()