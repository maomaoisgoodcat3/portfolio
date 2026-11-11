from sqlalchemy.engine import URL, make_url


def normalize_database_url(value: str) -> URL:
    url = make_url(value)
    if url.drivername in {"postgres", "postgresql", "postgresql+psycopg2"}:
        return url.set(drivername="postgresql+psycopg")
    return url
