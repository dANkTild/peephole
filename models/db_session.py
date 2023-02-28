import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

__factory: AsyncSession = None


def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    conn_str = f'sqlite+aiosqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")

    engine = create_async_engine(conn_str, echo=False)
    __factory = async_sessionmaker(bind=engine)

    from . import __all_models

    async def init_models():
        async with engine.begin() as conn:
            # await conn.run_sync(SqlAlchemyBase.metadata.drop_all)
            await conn.run_sync(SqlAlchemyBase.metadata.create_all)

    asyncio.run(init_models())


def create_session() -> AsyncSession:
    global __factory
    return __factory()
