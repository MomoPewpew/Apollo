from os.path import isfile
from sqlite3 import connect
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

DB_PATH = "./data/db/database.db"
BUILD_PATH = "./data/db/build.sql"

cxn = connect(DB_PATH, check_same_thread=False)
cur = cxn.cursor()

def with_commit(func) -> None:
    def inner(*args, **kwargs):
        func(*args, **kwargs)
        commit()
    
    return inner

@with_commit
def build() -> None:
    if isfile(BUILD_PATH):
        scriptexec(BUILD_PATH)

def commit() -> None:
    print("Committing database...")
    cxn.commit()

def autosave(sched: AsyncIOScheduler) -> None:
    sched.add_job(commit, CronTrigger(second=0))

def close() -> None:
    cxn.close()

def field(command: str, *values) -> Any:
    cur.execute(command, tuple(values))

    if (fetch := cur.fetchone()) is not None:
        return fetch[0]

def column(command: str, *values) -> list[Any]:
    cur.execute(command, tuple(values))

    return [item[0] for item in cur.fetchall()]

def record(command: str, *values) -> list[Any]:
    cur.execute(command, tuple(values))

    return cur.fetchone()

def records(command: str, *values) -> list[list[Any]]:
    cur.execute(command, tuple(values))

    return cur.fetchall()

def execute(command: str, *values) -> None:
    cur.execute(command, tuple(values))

def multiexec(command: str, valueset) -> None:
    cur.executemany(command, valueset)

def scriptexec(path) -> None:
    with open(path, "r", encoding="utf-8") as script:
        cur.executescript(script.read())