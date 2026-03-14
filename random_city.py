import random
from cities_data import get_cities


def random_city(category: str = "all", count: int = 1) -> list[str]:
    pool = get_cities(category)
    return random.sample(pool, min(count, len(pool)))
