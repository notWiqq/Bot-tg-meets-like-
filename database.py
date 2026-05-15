import aiosqlite

async def init_db():
    async with aiosqlite.connect("users_data.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users 
                            (user_id INTEGER PRIMARY KEY, username TEXT, stack TEXT, description TEXT)''')
        await db.commit()


async def save_user(user_id, username, nickname, stack, description):
    async with aiosqlite.connect("users_data.db") as db:
        await db.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)", 
                         (user_id, username, nickname, stack, description))
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect("users_data.db") as db:
        async with db.execute("SELECT stack, description FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() # Возвращает кортеж (stack, description) или None
        
async def get_random_user(exclude_user_id):
    async with aiosqlite.connect("users_data.db") as db:
        async with db.execute(
            "SELECT user_id, username, nickname, stack, description FROM users WHERE user_id != ? ORDER BY RANDOM() LIMIT 1", 
            (exclude_user_id,)
        ) as cursor:
            return await cursor.fetchone() 
        
async def init_db():
    async with aiosqlite.connect("users_data.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users 
                            (user_id INTEGER PRIMARY KEY, 
                             username TEXT, 
                             nickname TEXT, 
                             stack TEXT, 
                             description TEXT)''')
        # Создаем также таблицу для лайков, чтобы мэтчи работали
        await db.execute('''CREATE TABLE IF NOT EXISTS likes 
                            (from_user_id INTEGER, 
                             to_user_id INTEGER,
                             PRIMARY KEY (from_user_id, to_user_id))''')
        await db.commit()

async def add_like(from_id, to_id):
    async with aiosqlite.connect("users_data.db") as db:
        await db.execute("INSERT OR IGNORE INTO likes VALUES (?, ?)", (from_id, to_id))
        
        # Проверяем взаимность
        async with db.execute("SELECT 1 FROM likes WHERE from_user_id = ? AND to_user_id = ?", (to_id, from_id)) as cursor:
            is_match = await cursor.fetchone()
        
        await db.commit()
        
        if is_match:
            # Если мэтч, достаем юзернейм того, кого лайкнули
            async with db.execute("SELECT username FROM users WHERE user_id = ?", (to_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
        return None