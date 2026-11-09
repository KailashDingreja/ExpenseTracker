from ledgify import config


def get_all(conn) -> dict:
    d = dict(config.DEFAULT_SETTINGS)
    d.update({r["key"]: r["value"] for r in conn.execute("SELECT key,value FROM settings")})
    return d


def set_value(conn, key, value):
    with conn:
        conn.execute(
            "INSERT INTO settings(key,value) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
