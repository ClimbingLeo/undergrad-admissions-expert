import os
import re
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))


@pytest.fixture(scope="session")
def tmp_db(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "test.db"
    os.environ["SIBO_DB_PATH"] = str(path)
    from sibo import config
    config.DB_PATH = path
    from sibo import db
    from sibo.cli import seed_demo
    from sibo.ingest.run import ingest
    conn = db.connect(path)
    db.init_schema(conn)
    ingest(conn, config.SOURCE_ROOT, verbose=False)
    seed_demo(conn)
    conn.close()
    return path


@pytest.fixture()
def conn(tmp_db):
    from sibo import db
    c = db.connect(tmp_db)
    yield c
    c.close()


def _csrf(text):
    return re.search(r'name="csrf" (?:value|content)="([^"]+)"', text).group(1)


@pytest.fixture()
def login(tmp_db):
    from fastapi.testclient import TestClient
    from sibo.web.main import app

    def _login(email):
        c = TestClient(app)
        c.__enter__()
        tok = _csrf(c.get("/login").text)
        r = c.post("/login", data={"email": email, "password": "demo1234", "csrf": tok}, follow_redirects=False)
        assert r.status_code == 303
        c.csrf = _csrf(c.get("/students").text)
        return c
    return _login
