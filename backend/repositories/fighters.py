from sqlalchemy import text
from db import SessionLocal

def get_fighter_by_name(name: str):
    session = SessionLocal()
    if "|" in name:
        full_name, nickname = name.split("|", 1)
    else:
        full_name, nickname = name, None

    query = """
        SELECT
            full_name,
            nickname,
            height,
            weight,
            reach,
            stance,
            wins,
            losses,
            draws
        FROM fighters
        WHERE LOWER(full_name) = LOWER(:full_name)
    """

    params = {"full_name": full_name}

    if nickname:
        query += " AND LOWER(nickname) = LOWER(:nickname)"
        params["nickname"] = nickname

    query += " LIMIT 1"

    result = session.execute(text(query), params).fetchone()
    session.close()

    if not result:
        return None

    return {
        "name": result.full_name,
        "nickname": result.nickname or "",
        "record": f"{result.wins}-{result.losses}-{result.draws}",
        "height": result.height or "-",
        "reach": result.reach or "-",
        "stance": result.stance or "-",
        "weight": result.weight or "-"
    }