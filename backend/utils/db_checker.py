from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


def check_database(engine: Engine, label: str, user: str) -> dict[str, str]:
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    "SELECT DATABASE() AS db_name, "
                    "CURRENT_USER() AS current_user_name, "
                    "1 AS alive"
                )
            )
            row = result.mappings().first()

            if row and row["alive"] == 1:
                return {
                    "name": label,
                    "status": "ok",
                    "database": str(row["db_name"] or ""),
                    "user": user,
                    "current_user": str(row["current_user_name"] or ""),
                }

            return {
                "name": label,
                "status": "fail",
                "database": "",
                "user": user,
                "current_user": "",
            }

    except SQLAlchemyError as exc:
        return {
            "name": label,
            "status": "error",
            "database": "",
            "user": user,
            "current_user": "",
            "detail": str(exc),
        }
