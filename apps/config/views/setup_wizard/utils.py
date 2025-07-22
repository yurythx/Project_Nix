from pathlib import Path

def to_str_path(obj):
    """Converte todos os objetos Path em um dict/list para str recursivamente"""
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: to_str_path(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_str_path(i) for i in obj]
    else:
        return obj 