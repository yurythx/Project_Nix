from datetime import datetime

def format_datetime(dt: datetime, fmt: str = "%d/%m/%Y %H:%M") -> str:
    """Formata um datetime para string legível"""
    if not dt:
        return "-"
    return dt.strftime(fmt) 