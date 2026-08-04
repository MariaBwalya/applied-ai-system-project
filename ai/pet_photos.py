"""Pet photo lookup via Dog CEO API (dogs) and TheCatAPI (cats).

Plain REST wrappers, no LLM/Streamlit dependency -- keeps this module
framework-agnostic and unit-testable like the rest of `ai/`. Every public
function is guaranteed to never raise and to degrade to `None` (no photo)
on any unresolved breed, API failure, or network error.
"""
import os
from functools import lru_cache

import requests
from dotenv import load_dotenv

from pawpal_system import Pet

DEFAULT_TIMEOUT_SECONDS = 5.0

_DOG_LIST_URL = "https://dog.ceo/api/breeds/list/all"
_DOG_BREED_IMAGE_URL_TMPL = "https://dog.ceo/api/breed/{path}/images/random"
_DOG_RANDOM_URL = "https://dog.ceo/api/breeds/image/random"
_CAT_BREEDS_URL = "https://api.thecatapi.com/v1/breeds"
_CAT_SEARCH_URL = "https://api.thecatapi.com/v1/images/search"


class _BreedListUnavailable(Exception):
    """Internal sentinel -- never surfaced to callers. Not cached by
    lru_cache, so a transient outage doesn't stay "broken" forever."""


def _safe_get(http_get, url, *, params=None, timeout=DEFAULT_TIMEOUT_SECONDS, headers=None):
    """-> parsed JSON body on HTTP 200 with a valid JSON body, else None.
    Never raises."""
    try:
        response = http_get(url, params=params, timeout=timeout, headers=headers)
    except requests.RequestException:
        return None
    if getattr(response, "status_code", None) != 200:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def _cat_headers() -> dict | None:
    load_dotenv()
    key = os.environ.get("CAT_API_KEY")
    return {"x-api-key": key} if key else None


@lru_cache(maxsize=1)
def _cached_dog_breed_map(http_get) -> dict:
    data = _safe_get(http_get, _DOG_LIST_URL)
    if not isinstance(data, dict) or data.get("status") != "success" or not isinstance(data.get("message"), dict):
        raise _BreedListUnavailable()
    return data["message"]


def _get_dog_breed_map(http_get) -> dict | None:
    try:
        return _cached_dog_breed_map(http_get)
    except _BreedListUnavailable:
        return None


@lru_cache(maxsize=1)
def _cached_cat_breed_list(http_get) -> list:
    data = _safe_get(http_get, _CAT_BREEDS_URL, headers=_cat_headers())
    if not isinstance(data, list):
        raise _BreedListUnavailable()
    return data


def _get_cat_breed_list(http_get) -> list | None:
    try:
        return _cached_cat_breed_list(http_get)
    except _BreedListUnavailable:
        return None


def _find_dog_breed_path(breed_map: dict, breed: str) -> str | None:
    """Case-insensitive match of a free-text breed string against Dog CEO's
    main-breed/sub-breed map. Breed naming order isn't a simple slugify
    (e.g. "German Shepherd" -> "german/shepherd", "Border Collie" ->
    "collie/border") so both word orders are checked."""
    breed_lower = breed.strip().lower()
    if not breed_lower:
        return None

    if breed_lower in breed_map:
        return breed_lower  # main breed alone works even if it has sub-breeds

    words = breed_lower.split()
    for main, subs in breed_map.items():
        for sub in subs:
            if breed_lower in (f"{main} {sub}", f"{sub} {main}"):
                return f"{main}/{sub}"

    for word in words:
        if word in breed_map:
            return word

    for main, subs in breed_map.items():
        for sub in subs:
            if sub in words:
                return f"{main}/{sub}"

    return None


def _find_cat_breed_id(breed_list: list, breed: str) -> str | None:
    """Case-insensitive exact match against each entry's "name". Returns
    None for coat-pattern terms like "tabby" that aren't real breeds --
    expected, callers fall back to a generic image."""
    breed_lower = breed.strip().lower()
    if not breed_lower:
        return None
    for entry in breed_list:
        name = entry.get("name") if isinstance(entry, dict) else None
        if isinstance(name, str) and name.strip().lower() == breed_lower:
            return entry.get("id")
    return None


def get_dog_photo_url(breed: str, *, http_get=requests.get, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> str | None:
    breed_map = _get_dog_breed_map(http_get)
    if breed_map:
        path = _find_dog_breed_path(breed_map, breed)
        if path:
            data = _safe_get(http_get, _DOG_BREED_IMAGE_URL_TMPL.format(path=path), timeout=timeout)
            if isinstance(data, dict) and data.get("status") == "success" and data.get("message"):
                return data["message"]

    data = _safe_get(http_get, _DOG_RANDOM_URL, timeout=timeout)
    if isinstance(data, dict) and data.get("status") == "success" and data.get("message"):
        return data["message"]
    return None


def get_cat_photo_url(breed: str, *, http_get=requests.get, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> str | None:
    headers = _cat_headers()
    breed_list = _get_cat_breed_list(http_get)
    if breed_list:
        breed_id = _find_cat_breed_id(breed_list, breed)
        if breed_id:
            data = _safe_get(
                http_get, _CAT_SEARCH_URL, params={"breed_ids": breed_id, "limit": 1},
                timeout=timeout, headers=headers,
            )
            if isinstance(data, list) and data and isinstance(data[0], dict) and data[0].get("url"):
                return data[0]["url"]

    data = _safe_get(http_get, _CAT_SEARCH_URL, timeout=timeout, headers=headers)
    if isinstance(data, list) and data and isinstance(data[0], dict) and data[0].get("url"):
        return data[0]["url"]
    return None


def get_pet_photo_url(pet: Pet, *, http_get=requests.get, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> str | None:
    """Single entry point for the UI. Never raises, never hangs -- callers
    can call this on every rerun without risking a frozen page, though the
    UI should still cache the result per pet to avoid refetching on every
    unrelated interaction."""
    try:
        species = pet.species.strip().lower()
        if species == "dog":
            return get_dog_photo_url(pet.breed, http_get=http_get, timeout=timeout)
        if species == "cat":
            return get_cat_photo_url(pet.breed, http_get=http_get, timeout=timeout)
        return None
    except Exception:
        return None