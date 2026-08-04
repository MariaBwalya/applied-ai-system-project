import requests

from pawpal_system import Pet
from ai.pet_photos import get_cat_photo_url, get_dog_photo_url, get_pet_photo_url
from tests.fakes import FakeHttpGet, FakeHttpResponse

DOG_BREED_MAP_RESPONSE = FakeHttpResponse(json_data={
    "status": "success",
    "message": {"collie": ["border"], "labrador": [], "hound": ["afghan"]},
})
DOG_IMAGE_RESPONSE = FakeHttpResponse(json_data={
    "status": "success", "message": "https://images.dog.ceo/breeds/collie-border/x.jpg",
})
DOG_RANDOM_RESPONSE = FakeHttpResponse(json_data={
    "status": "success", "message": "https://images.dog.ceo/random/y.jpg",
})

CAT_BREEDS_RESPONSE = FakeHttpResponse(json_data=[
    {"id": "beng", "name": "Bengal"}, {"id": "siam", "name": "Siamese"},
])
CAT_SEARCH_RESPONSE = FakeHttpResponse(json_data=[
    {"id": "abc", "url": "https://cdn2.thecatapi.com/images/abc.jpg"},
])
CAT_GENERIC_RESPONSE = FakeHttpResponse(json_data=[
    {"id": "xyz", "url": "https://cdn2.thecatapi.com/images/xyz.jpg"},
])


def _dog(breed="Border Collie"):
    return Pet(name="Rex", species="dog", age=4, breed=breed)


def _cat(breed="Bengal"):
    return Pet(name="Tom", species="cat", age=2, breed=breed)


def test_get_dog_photo_url_returns_breed_specific_image_for_multiword_breed():
    fake = FakeHttpGet([DOG_BREED_MAP_RESPONSE, DOG_IMAGE_RESPONSE])
    url = get_dog_photo_url("Border Collie", http_get=fake)
    assert url == "https://images.dog.ceo/breeds/collie-border/x.jpg"
    assert "collie/border" in fake.calls_seen[1]["url"]


def test_get_dog_photo_url_unknown_breed_falls_back_to_random_image():
    fake = FakeHttpGet([DOG_BREED_MAP_RESPONSE, DOG_RANDOM_RESPONSE])
    url = get_dog_photo_url("Not A Real Breed", http_get=fake)
    assert url == "https://images.dog.ceo/random/y.jpg"


def test_get_dog_photo_url_breed_list_unavailable_falls_back_to_random_image():
    fake = FakeHttpGet([FakeHttpResponse(status_code=500), DOG_RANDOM_RESPONSE])
    url = get_dog_photo_url("Border Collie", http_get=fake)
    assert url == "https://images.dog.ceo/random/y.jpg"
    assert len(fake.calls_seen) == 2


def test_get_cat_photo_url_returns_image_for_known_breed():
    fake = FakeHttpGet([CAT_BREEDS_RESPONSE, CAT_SEARCH_RESPONSE])
    url = get_cat_photo_url("Bengal", http_get=fake)
    assert url == "https://cdn2.thecatapi.com/images/abc.jpg"
    assert fake.calls_seen[1]["params"]["breed_ids"] == "beng"


def test_get_cat_photo_url_coat_pattern_term_falls_back_to_random_image():
    fake = FakeHttpGet([CAT_BREEDS_RESPONSE, CAT_GENERIC_RESPONSE])
    url = get_cat_photo_url("tabby", http_get=fake)
    assert url == "https://cdn2.thecatapi.com/images/xyz.jpg"
    assert fake.calls_seen[1]["params"] is None


def test_get_cat_photo_url_empty_search_result_falls_back_to_random_image():
    fake = FakeHttpGet([CAT_BREEDS_RESPONSE, FakeHttpResponse(json_data=[]), CAT_GENERIC_RESPONSE])
    url = get_cat_photo_url("Bengal", http_get=fake)
    assert url == "https://cdn2.thecatapi.com/images/xyz.jpg"


def test_get_pet_photo_url_network_error_returns_none_without_raising():
    fake = FakeHttpGet([requests.RequestException("network down")] * 3)
    assert get_pet_photo_url(_dog(), http_get=fake) is None


def test_get_pet_photo_url_returns_none_for_species_other_without_any_network_call():
    fake = FakeHttpGet([])
    pet = Pet(name="Rio", species="other", age=1, breed="Parakeet")
    assert get_pet_photo_url(pet, http_get=fake) is None
    assert fake.calls_seen == []


def test_get_pet_photo_url_dispatches_dog_species_to_dog_ceo():
    fake = FakeHttpGet([DOG_BREED_MAP_RESPONSE, DOG_IMAGE_RESPONSE])
    get_pet_photo_url(_dog(), http_get=fake)
    assert "dog.ceo" in fake.calls_seen[0]["url"]


def test_get_pet_photo_url_dispatches_cat_species_to_thecatapi():
    fake = FakeHttpGet([CAT_BREEDS_RESPONSE, CAT_SEARCH_RESPONSE])
    get_pet_photo_url(_cat(), http_get=fake)
    assert "thecatapi.com" in fake.calls_seen[0]["url"]


def test_dog_breed_map_is_fetched_once_and_cached_across_lookups():
    fake = FakeHttpGet([DOG_BREED_MAP_RESPONSE, DOG_IMAGE_RESPONSE, DOG_IMAGE_RESPONSE])
    get_dog_photo_url("Border Collie", http_get=fake)
    get_dog_photo_url("Afghan Hound", http_get=fake)
    list_calls = [c for c in fake.calls_seen if "breeds/list/all" in c["url"]]
    assert len(list_calls) == 1


def test_cat_breed_list_is_fetched_once_and_cached_across_lookups():
    fake = FakeHttpGet([CAT_BREEDS_RESPONSE, CAT_SEARCH_RESPONSE, CAT_SEARCH_RESPONSE])
    get_cat_photo_url("Bengal", http_get=fake)
    get_cat_photo_url("Siamese", http_get=fake)
    breeds_calls = [c for c in fake.calls_seen if c["url"] == "https://api.thecatapi.com/v1/breeds"]
    assert len(breeds_calls) == 1


def test_get_dog_photo_url_never_raises_on_request_exception():
    fake = FakeHttpGet([requests.RequestException("down")] * 3)
    assert get_dog_photo_url("Labrador", http_get=fake) is None


def test_get_dog_photo_url_never_raises_on_malformed_json():
    fake = FakeHttpGet([FakeHttpResponse(json_data={"status": "success", "message": {"labrador": []}}),
                        FakeHttpResponse(raise_on_json=True),
                        FakeHttpResponse(raise_on_json=True)])
    assert get_dog_photo_url("Labrador", http_get=fake) is None


def test_get_cat_photo_url_never_raises_on_request_exception():
    fake = FakeHttpGet([requests.RequestException("down")] * 3)
    assert get_cat_photo_url("Bengal", http_get=fake) is None


def test_cat_api_key_included_as_header_when_env_var_set(monkeypatch):
    monkeypatch.setenv("CAT_API_KEY", "test-key-123")
    monkeypatch.setattr("ai.pet_photos.load_dotenv", lambda *a, **k: None)
    fake = FakeHttpGet([CAT_BREEDS_RESPONSE, CAT_SEARCH_RESPONSE])
    get_cat_photo_url("Bengal", http_get=fake)
    assert fake.calls_seen[0]["headers"] == {"x-api-key": "test-key-123"}


def test_cat_api_key_omitted_when_env_var_absent(monkeypatch):
    monkeypatch.delenv("CAT_API_KEY", raising=False)
    monkeypatch.setattr("ai.pet_photos.load_dotenv", lambda *a, **k: None)
    fake = FakeHttpGet([CAT_BREEDS_RESPONSE, CAT_SEARCH_RESPONSE])
    get_cat_photo_url("Siamese", http_get=fake)
    assert fake.calls_seen[0]["headers"] is None