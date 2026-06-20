# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, MONGO_DB

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]

    # TTL index: auto-delete expired sessions after 2 hours
    await db.sessions.create_index("expires_at", expireAfterSeconds=0)
    # Ensure session lookup is fast
    await db.sessions.create_index("session_id", unique=True)
    # User indices
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    print("✅  MongoDB connected")


async def close_db():
    global client
    if client:
        client.close()
        print("🔌  MongoDB connection closed")


def get_db():
    return db
