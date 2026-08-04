import streamlit as st
import streamlit.components.v1 as components
from pawpal_system import (
    Owner,
    Pet,
    Task,
    MultiPetScheduler,
    RECURRENCE_OPTIONS,
    compute_end_time,
    confirm_concurrent_group,
    find_time_conflicts,
    unscheduled_minutes_needed,
)
from ai.llm_client import LLMConfigError, get_default_llm_client
from ai.parser import parse_pet_description, parse_tasks_from_description, suggest_tasks_for_pet
from ai.pet_photos import get_pet_photo_url

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ---------------------------------------------------------------------------
# Landing page styling — scoped to st.container(key=...) classes so it only
# ever touches the pre-onboarding hero/timeline/CTA/signup-card elements.
# ---------------------------------------------------------------------------
st.html("""
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&display=swap" rel="stylesheet">
<style>
.st-key-hero_section {
    position: relative;
    left: 50%;
    right: 50%;
    width: 100vw !important;
    max-width: 100vw !important;
    margin-left: -50vw;
    margin-right: -50vw;
    margin-top: -1rem;
    margin-bottom: 1.5rem;
    min-height: 480px;
    box-sizing: border-box;
    overflow: hidden;
    background-image:
        linear-gradient(100deg, rgba(15,15,25,0.35) 0%, rgba(15,15,25,0.15) 45%, rgba(15,15,25,0.02) 70%),
        url('app/static/HeroPic.png');
    background-size: cover;
    background-position: center 35%;
    display: flex;
    align-items: center;
    padding: 3rem 3rem 3rem 4rem;
}
.st-key-hero_section h1,
.st-key-hero_section h3,
.st-key-hero_section p,
.st-key-hero_section span {
    color: #ffffff !important;
}
.st-key-hero_text_box {
    max-width: 520px;
    background: rgba(0,0,0,0.25);
    border-radius: 24px;
    padding: 2rem 2.5rem;
}
.st-key-hero_text_box h3 {
    font-family: lucida calligraphy;
    font-weight: 80;
    font-size: 1.1rem;
    line-height: 1.2;
}

.st-key-signup_zone {
    max-width: 640px;
    margin-left: auto;
    margin-right: auto;
    background: radial-gradient(circle at 30% 20%, rgba(123,104,238,0.20), transparent 60%),
                radial-gradient(circle at 80% 80%, rgba(79,124,255,0.18), transparent 55%),
                linear-gradient(135deg, rgba(155,107,255,0.10), rgba(79,124,255,0.10));
    border-radius: 28px;
    padding: 2rem 2rem;
}
@media (prefers-color-scheme: dark) {
    .st-key-signup_zone {
        background: radial-gradient(circle at 30% 20%, rgba(123,104,238,0.16), transparent 60%),
                    radial-gradient(circle at 80% 80%, rgba(79,124,255,0.14), transparent 55%),
                    linear-gradient(135deg, rgba(155,107,255,0.08), rgba(79,124,255,0.08));
    }
}

.st-key-create_profile_btn button {
    font-size: 1.1rem !important;
    padding: 0.7rem 2.4rem !important;
    border-radius: 999px !important;
    box-shadow: 0 8px 20px rgba(108,99,255,0.35);
}

.st-key-form_glass_card {
    background: rgba(255,255,255,0.5);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.65);
    border-radius: 24px;
    padding: 1.75rem 1.75rem 0.5rem;
    box-shadow: 0 8px 32px rgba(31,38,135,0.15);
}
@media (prefers-color-scheme: dark) {
    .st-key-form_glass_card {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.14);
        box-shadow: 0 8px 32px rgba(0,0,0,0.35);
    }
}
</style>
""")

# A JS-driven carousel (not pure-CSS) so it can support click-driven prev/next
# navigation in addition to auto-advance -- rendered via components.html since
# st.html()'s injected <script> tags don't execute (it's not a sandboxed
# iframe), while components.html gives a real iframe with working JS.
_CAROUSEL_ITEMS = [
    ("app/static/Feeding.png", "Feed"),
    ("app/static/Playtime.png", "Play"),
    ("app/static/MedTime.png", "Meds"),
    ("app/static/LitterCleanup.png", "Litter"),
    ("app/static/Grooming.png", "Groom"),
]
_CAROUSEL_HTML = """
<div id="pp-wrap">
  <button id="pp-prev" class="pp-arrow" aria-label="Previous">&#8249;</button>
  <div id="pp-stage">
    {items}
  </div>
  <button id="pp-next" class="pp-arrow" aria-label="Next">&#8250;</button>
</div>
<style>
  html, body {{ margin: 0; padding: 0; background: transparent; }}
  #pp-wrap {{ position: relative; max-width: 1040px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  #pp-stage {{ position: relative; height: 300px; margin: 0 60px; overflow: hidden; }}
  .pp-item {{
    position: absolute;
    top: 50%;
    left: 50%;
    width: 230px;
    height: 158px;
    margin-top: -79px;
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 12px 28px rgba(0,0,0,0.28);
  }}
  .pp-item img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
  .pp-label {{
    position: absolute;
    left: 0; right: 0; bottom: 0;
    padding: 0.5rem 0.6rem 0.4rem;
    background: linear-gradient(0deg, rgba(0,0,0,0.75), transparent);
    color: #ffffff;
    font-weight: 700;
    font-size: 1rem;
    text-align: center;
  }}
  .pp-arrow {{
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: rgba(0,0,0,0.5);
    color: #fff;
    border: none;
    cursor: pointer;
    font-size: 1.5rem;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s ease;
    z-index: 30;
  }}
  .pp-arrow:hover {{ background: rgba(0,0,0,0.75); }}
  #pp-prev {{ left: 0; }}
  #pp-next {{ right: 0; }}
</style>
<script>
(function() {{
  var stage = document.getElementById('pp-stage');
  var items = Array.prototype.slice.call(stage.querySelectorAll('.pp-item'));
  var N = items.length;
  var SLOT = 210;
  var HALF = Math.floor(N / 2);
  var pos = 0;

  function scaleFor(rel) {{ return rel === 0 ? 1.35 : (Math.abs(rel) === 1 ? 0.85 : 0.68); }}
  function opacityFor(rel) {{ return rel === 0 ? 1 : (Math.abs(rel) === 1 ? 0.75 : 0.4); }}
  function filterFor(rel) {{
    if (rel === 0) return 'grayscale(0%) brightness(1)';
    if (Math.abs(rel) === 1) return 'grayscale(35%) brightness(0.9)';
    return 'grayscale(75%) brightness(0.8)';
  }}
  function zFor(rel) {{ return 10 - Math.abs(rel); }}

  function relOf(i) {{
    var r = ((i - pos) % N + N) % N;
    if (r > HALF) r -= N;
    return r;
  }}

  function place(el, rel, animate) {{
    el.style.transition = animate
      ? 'transform 0.7s cubic-bezier(.4,0,.2,1), filter 0.7s ease'
      : 'none';
    el.style.transform = 'translateX(-50%) translateX(' + (rel * SLOT) + 'px) scale(' + scaleFor(rel) + ')';
    el.style.zIndex = zFor(rel);
    el.style.filter = filterFor(rel);
  }}

  // Initial layout, no animation.
  items.forEach(function(el) {{
    var i = parseInt(el.dataset.i, 10);
    var rel = relOf(i);
    place(el, rel, false);
    el.style.opacity = opacityFor(rel);
    el.dataset.rel = rel;
  }});

  function render() {{
    items.forEach(function(el) {{
      var i = parseInt(el.dataset.i, 10);
      var rel = relOf(i);
      var prevRel = parseInt(el.dataset.rel, 10);
      var wraps = Math.abs(rel - prevRel) > 1;
      if (wraps) {{
        // This item would have to visibly slide all the way across --
        // fade it out, snap it to its new slot with no transition, then
        // fade it back in, so it reads as "gone, then reappears" instead.
        el.style.transition = 'opacity 0.3s ease';
        el.style.opacity = '0';
        setTimeout(function() {{
          place(el, rel, false);
          void el.offsetWidth;
          el.style.transition = 'opacity 0.4s ease';
          el.style.opacity = opacityFor(rel);
        }}, 300);
      }} else {{
        place(el, rel, true);
        el.style.opacity = opacityFor(rel);
      }}
      el.dataset.rel = rel;
    }});
  }}

  function next() {{ pos = (pos + 1) % N; render(); }}
  function prev() {{ pos = (pos - 1 + N) % N; render(); }}

  var timer;
  function startTimer() {{ timer = setInterval(next, 4200); }}
  function resetTimer() {{ clearInterval(timer); startTimer(); }}

  document.getElementById('pp-next').addEventListener('click', function() {{ next(); resetTimer(); }});
  document.getElementById('pp-prev').addEventListener('click', function() {{ prev(); resetTimer(); }});

  startTimer();
}})();
</script>
"""
_CAROUSEL_HTML = _CAROUSEL_HTML.format(items="\n    ".join(
    f'<div class="pp-item" data-i="{i}"><img src="{src}" alt="{label}"><div class="pp-label">{label}</div></div>'
    for i, (src, label) in enumerate(_CAROUSEL_ITEMS)
))

# ---------------------------------------------------------------------------
# Helpers — display formatting only, no business logic
# ---------------------------------------------------------------------------
# Display-only labels for RECURRENCE_OPTIONS — the backend keeps the raw
# "daily"/"weekly"/"once" strings, this is purely what the selectboxes show.
_RECURRENCE_LABELS = {"daily": "Daily", "weekly": "Weekly", "once": "One-time"}


def _to_12h(time_str: str) -> str:
    h, m = map(int, time_str.split(":"))
    period = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12:02d}:{m:02d} {period}"


def _to_24h(hour12: int, minute: int, period: str) -> str:
    """Combine a 12-hour clock entry (hour/minute/AM-PM boxes) into 'HH:MM' 24h."""
    h = hour12 % 12
    if period == "PM":
        h += 12
    return f"{h:02d}:{minute:02d}"


def _from_24h(time_str: str) -> tuple[int, int, str]:
    """Split 'HH:MM' 24h into (hour12, minute, AM/PM) for pre-filling the boxes."""
    h, m = map(int, time_str.split(":"))
    period = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return h12, m, period


def _get_ai_client():
    """Build the Gemini client fresh each run, or None if no GEMINI_API_KEY
    is configured -- the AI entry sections degrade to a disabled state
    rather than erroring. Not cached: construction is cheap (no network
    call happens until .generate() is actually invoked), and caching here
    would freeze a stale None from before .env was set until server restart."""
    try:
        return get_default_llm_client()
    except LLMConfigError:
        return None


def _species_emoji(species: str) -> str:
    s = species.strip().lower()
    if s == "dog":
        return "🐶"
    if s == "cat":
        return "🐱"
    return "🐾"


def _render_avatar(image_source, fallback_emoji: str, width: int = 80) -> None:
    """Renders a photo (URL or raw bytes) if given, else a fixed-size emoji
    placeholder in a bordered box -- one fallback idiom reused everywhere
    (owner profile picture, pet photos)."""
    if image_source:
        st.image(image_source, width=width)
    else:
        st.markdown(
            f"<div style='width:{width}px;height:{width}px;display:flex;"
            f"align-items:center;justify-content:center;font-size:{width // 2}px;"
            f"border:1px solid rgba(128,128,128,0.35);border-radius:8px;'>"
            f"{fallback_emoji}</div>",
            unsafe_allow_html=True,
        )


def _pet_photo_url(pet: Pet) -> str | None:
    """Fetches (and caches) a pet's photo URL, once per pet, so Streamlit's
    rerun-the-whole-script-on-every-click model doesn't hammer the photo
    APIs on every unrelated interaction."""
    cache = st.session_state.pet_photo_cache
    pid = id(pet)
    if pid not in cache:
        cache[pid] = get_pet_photo_url(pet)
    return cache[pid]


def _pet_index_by_identity(pet: Pet) -> int:
    """Finds a pet's list index by object identity, not equality -- Pet is a
    plain dataclass with a field-based __eq__, so two pets with identical
    field values (e.g. same name/species/age, no tasks yet) could otherwise
    collide under list.index()/list.remove()."""
    return next(i for i, p in enumerate(st.session_state.pets) if p is pet)


def _render_task_batch_preview(batch_result, pet: Pet, session_key: str) -> None:
    """Shared preview/confirm UI for a ParsedTaskBatchResult, used by both
    the free-text task parser and the AI task-suggestion feature -- both
    return the same shape, so one component handles both."""
    if batch_result.error:
        st.error(batch_result.error)
        return

    selections = []
    with st.form(f"batch_form_{session_key}"):
        for idx, t in enumerate(batch_result.tasks):
            time_note = f" at {_to_12h(t.preferred_time)}" if t.preferred_time else ""
            bg_note = "  *(bg)*" if not t.owner_required else ""
            checked = st.checkbox(
                f"{t.title} - {t.duration_minutes} min [{t.priority}]{bg_note}{time_note}",
                value=True, key=f"{session_key}_sel_{idx}",
            )
            selections.append(checked)
            for w in batch_result.warnings:
                if w.startswith(f"task {idx + 1}:"):
                    st.caption(f"Note: {w.split(':', 1)[1].strip()}")

        add_col, discard_col = st.columns(2)
        with add_col:
            submitted_add = st.form_submit_button("Add Selected", type="primary")
        with discard_col:
            submitted_discard = st.form_submit_button("Discard All")

    if batch_result.dropped:
        with st.expander(f"{len(batch_result.dropped)} suggestion(s) not included"):
            for d in batch_result.dropped:
                st.caption(d)

    if submitted_add:
        for keep, t in zip(selections, batch_result.tasks):
            if keep:
                pet.add_task(t)
        st.session_state.plan = None
        st.session_state[session_key] = None
        st.rerun()
    if submitted_discard:
        st.session_state[session_key] = None
        st.rerun()


def _render_owner_form(is_edit: bool, bordered: bool = True) -> None:
    """Owner info form, shared between the pre-onboarding landing view and
    the post-onboarding sidebar's inline edit-profile flow."""
    o = st.session_state.owner
    with st.form("owner_form", border=bordered):
        owner_name = st.text_input("Your name", value=o.name if o else "Jordan", key="owner_name_input")
        avail_mins = st.number_input(
            "Available time today (minutes)", min_value=10, max_value=480,
            value=o.available_minutes if o else 120, key="owner_avail_mins_input",
        )
        preferences = st.text_input(
            "Any preferences? (optional)", value=o.preferences if o else "", key="owner_preferences_input",
        )
        photo_file = st.file_uploader(
            "Profile picture (optional)", type=["png", "jpg", "jpeg"], key="owner_photo_uploader",
        )
        submit_label = "Save changes" if is_edit else "Get Started"
        if st.form_submit_button(submit_label, type="primary"):
            st.session_state.owner = Owner(
                name=owner_name,
                available_minutes=int(avail_mins),
                preferences=preferences,
            )
            if photo_file is not None:
                st.session_state.owner_photo_bytes = photo_file.getvalue()
            if is_edit:
                st.session_state.editing_owner = False
            st.rerun()


# ---------------------------------------------------------------------------
# Initialise session state once
# Streamlit re-runs the entire script on every button click or widget change.
# session_state is the only storage that survives across those re-runs.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None
if "show_signup_form" not in st.session_state:
    st.session_state.show_signup_form = False
if "owner_photo_bytes" not in st.session_state:
    st.session_state.owner_photo_bytes = None
if "editing_owner" not in st.session_state:
    st.session_state.editing_owner = False
if "pets" not in st.session_state:
    st.session_state.pets = []
if "plan" not in st.session_state:
    st.session_state.plan = None
if "overflow_ack_signature" not in st.session_state:
    # Remembers which exact overflow (which tasks + what available_minutes) the
    # user already dismissed via "Push overflow to next day" — see the Schedule
    # page below for how this self-invalidates when either one changes.
    st.session_state.overflow_ack_signature = None
if "editing_task" not in st.session_state:
    st.session_state.editing_task = None  # (pet_index, task_index) of the row being edited
if "ai_pet_preview" not in st.session_state:
    st.session_state.ai_pet_preview = None
if "pet_photo_cache" not in st.session_state:
    st.session_state.pet_photo_cache = {}


# ---------------------------------------------------------------------------
# Gate: landing/welcome view until an owner is saved, then unlock everything
# ---------------------------------------------------------------------------
if st.session_state.owner is None:
    with st.container(key="hero_section"):
        with st.container(key="hero_text_box"):
            st.title("🐾 PawPal+")
            st.subheader('"Every pet\'s day, perfectly planned."')

    st.space("large")

    with st.container(key="features_section"):
        st.markdown("#### A day in the life, sorted")
        st.write(
            "Feeding, walks, meds, and playtime, all folded into one smart "
            "daily schedule built around your time, for every pet in your home."
        )
        components.html(_CAROUSEL_HTML, height=340, scrolling=False)

        st.space("medium")

        with st.container(horizontal=True):
            with st.container(border=True):
                st.markdown("🐾 **Multi-pet friendly**")
                st.caption("Every dog, cat, and critter gets their own routine.")
            with st.container(border=True):
                st.markdown("⏱️ **Smart time management**")
                st.caption("Tasks are fit into the minutes you actually have today.")
            with st.container(border=True):
                st.markdown("💬 **Plain-English entry**")
                st.caption("Describe care in your own words, AI turns it into tasks.")
            with st.container(border=True):
                st.markdown("✅ **Conflict detection**")
                st.caption("Catches overlapping care times before they become a problem.")

    st.space("large")

    with st.container(key="signup_zone"):
        with st.container(key="cta_section", horizontal_alignment="center"):
            st.subheader("Let's get started", text_alignment="center")
            st.markdown("Set up your profile, it takes less than a minute.", text_alignment="center")
            if not st.session_state.show_signup_form:
                if st.button("Create Profile", key="create_profile_btn", type="primary", icon="🐾"):
                    st.session_state.show_signup_form = True
                    st.rerun()

    if st.session_state.show_signup_form:
        st.space("medium")
        left, mid, right = st.columns([1, 1.3, 1])
        with mid:
            with st.container(key="form_glass_card"):
                st.markdown("#### Tell us about you")
                _render_owner_form(is_edit=False, bordered=False)
                if st.button("‹ Back", key="signup_back_btn"):
                    st.session_state.show_signup_form = False
                    st.rerun()

else:
    st.title("🐾 PawPal+")
    # -----------------------------------------------------------------------
    # Sidebar — persistent profile card + at-a-glance status
    # -----------------------------------------------------------------------
    with st.sidebar:
        if st.session_state.editing_owner:
            st.subheader("Edit profile")
            if st.session_state.owner_photo_bytes:
                st.caption("Current photo, upload a new one below to replace it")
                _render_avatar(st.session_state.owner_photo_bytes, "🧑", width=64)
            _render_owner_form(is_edit=True)
            if st.button("Cancel"):
                st.session_state.editing_owner = False
                st.rerun()
        else:
            o = st.session_state.owner
            avatar_col, info_col = st.columns([1, 2])
            with avatar_col:
                _render_avatar(st.session_state.owner_photo_bytes, "🧑", width=64)
            with info_col:
                st.write(f"**{o.name}**")
                st.caption(f"{o.available_minutes} min available")
            if st.button("✏️ Edit profile"):
                st.session_state.editing_owner = True
                st.rerun()

        # Always visible, regardless of edit mode — nothing here is actually
        # affected by editing the owner's profile, it just used to be hidden
        # behind this same if/else by mistake.
        st.divider()
        st.metric("Pets", len(st.session_state.pets))
        st.metric("Tasks", sum(len(p.tasks) for p in st.session_state.pets))
        st.caption("Plan generated" if st.session_state.plan else "No plan yet")

    # -----------------------------------------------------------------------
    # Navbar
    # -----------------------------------------------------------------------
    page = st.segmented_control(
        "Navigate",
        ["🐶 Pets", "📋 Tasks", "🗓️ Schedule"],
        default="🐶 Pets",
        key="current_page",
        label_visibility="collapsed",
    ) or "🐶 Pets"
    st.divider()

    # -----------------------------------------------------------------------
    # Pets page
    # -----------------------------------------------------------------------
    if page == "🐶 Pets":
        st.subheader("Pets")

        with st.form("add_pet_form"):
            pet_name = st.text_input("Pet name", value="Bella", key="add_pet_name")
            species = st.selectbox("Species", ["dog", "cat", "other"], key="add_pet_species")
            # Always rendered (not conditional on species) — widgets inside a form don't
            # rerun the script on change, so `if species == "other"` here would still be
            # reflecting last run's selection.
            custom_species = st.text_input("If Other, please specify", key="add_pet_custom_species")
            age = st.number_input("Age (years)", min_value=0, max_value=30, value=3, key="add_pet_age")
            breed = st.text_input("Breed (optional)", key="add_pet_breed")
            if st.form_submit_button("Add Pet", type="primary"):
                final_species = custom_species.strip() if species == "other" and custom_species.strip() else species
                st.session_state.pets.append(
                    Pet(name=pet_name, species=final_species, age=int(age), breed=breed)
                )

        with st.expander("Describe your pet in plain English"):
            ai_client = _get_ai_client()
            if ai_client is None:
                st.caption("AI entry unavailable, set GEMINI_API_KEY in a .env file to enable this.")
            else:
                pet_nl_text = st.text_area(
                    "e.g. \"Bella is a 3 year old Labrador\"", key="ai_pet_text"
                )
                if st.button("Parse with AI", key="ai_pet_parse_btn"):
                    try:
                        st.session_state.ai_pet_preview = parse_pet_description(pet_nl_text, ai_client)
                    except Exception:
                        st.session_state.ai_pet_preview = None
                        st.error("AI parsing failed unexpectedly, please use the form above instead.")

                preview = st.session_state.ai_pet_preview
                if preview is not None:
                    if preview.error:
                        st.error(preview.error)
                    else:
                        p = preview.pet
                        breed_note = f", {p.breed}" if p.breed else ""
                        st.write(f"**{p.name}** ({p.species}, age {p.age}{breed_note})")
                        for warning in preview.warnings:
                            st.caption(f"Note: {warning}")
                        confirm_col, discard_col = st.columns(2)
                        with confirm_col:
                            if st.button("Add this pet", key="ai_pet_confirm_btn"):
                                st.session_state.pets.append(p)
                                st.session_state.ai_pet_preview = None
                                st.rerun()
                        with discard_col:
                            if st.button("Discard", key="ai_pet_discard_btn"):
                                st.session_state.ai_pet_preview = None
                                st.rerun()

        st.divider()

        if not st.session_state.pets:
            st.info("No pets yet. Add one above.")
        else:
            for pet in st.session_state.pets:
                pid = id(pet)
                with st.container(border=True):
                    photo_col, info_col, action_col = st.columns([1, 3, 1])
                    with photo_col:
                        _render_avatar(_pet_photo_url(pet), _species_emoji(pet.species), width=100)
                    with info_col:
                        st.write(f"**{pet.name}**")
                        breed_bit = f" · {pet.breed}" if pet.breed else ""
                        st.caption(f"{pet.species.title()}{breed_bit} · {pet.age}y")
                        st.caption(f"🗒️ {len(pet.tasks)} task(s)")
                    with action_col:
                        if st.button("🗑️ Remove", key=f"remove_pet_{pid}"):
                            st.session_state.pets.pop(_pet_index_by_identity(pet))
                            st.session_state.pet_photo_cache.pop(pid, None)
                            st.session_state.pop(f"ai_task_batch_suggested_{pid}", None)
                            st.session_state.pop(f"ai_task_batch_parsed_{pid}", None)
                            st.session_state.plan = None
                            st.rerun()
                        if st.button("✨ Suggest tasks", key=f"suggest_tasks_{pid}"):
                            ai_client = _get_ai_client()
                            if ai_client is None:
                                st.error("Set GEMINI_API_KEY in .env to use AI suggestions.")
                            else:
                                st.session_state[f"ai_task_batch_suggested_{pid}"] = suggest_tasks_for_pet(pet, ai_client)
                                st.rerun()

                    suggested_key = f"ai_task_batch_suggested_{pid}"
                    suggested_batch = st.session_state.get(suggested_key)
                    if suggested_batch is not None:
                        st.markdown(f"**AI-suggested tasks for {pet.name}:**")
                        _render_task_batch_preview(suggested_batch, pet, suggested_key)

    # -----------------------------------------------------------------------
    # Tasks page
    # -----------------------------------------------------------------------
    elif page == "📋 Tasks":
        st.subheader("Tasks")

        if not st.session_state.pets:
            st.info("Add a pet first, in the Pets section.")
        else:
            pet_names = [p.name for p in st.session_state.pets]
            selected_pet_name = st.selectbox("Select pet", pet_names, key="tasks_pet_selector")
            selected_pet_index = pet_names.index(selected_pet_name)
            selected_pet = st.session_state.pets[selected_pet_index]
            pid = id(selected_pet)

            with st.expander("➕ Add manually", expanded=True):
                with st.form("add_task_form"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        task_title = st.text_input("Task title", value="Morning walk", key="add_task_title")
                    with col2:
                        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20, key="add_task_duration")
                    with col3:
                        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2, key="add_task_priority")
                    with col4:
                        recurrence = st.selectbox(
                            "Repeats", RECURRENCE_OPTIONS, index=0,
                            format_func=lambda r: _RECURRENCE_LABELS[r], key="add_task_recurrence",
                        )
                    owner_required = st.checkbox("Requires owner's presence", value=True, key="add_task_owner_required")

                    has_anchor = st.checkbox(
                        "Anchor to a specific time (e.g. medication with breakfast)", value=True, key="add_task_has_anchor",
                    )
                    # Checked by default — the boxes below are always visible, so defaulting to
                    # anchored avoids silently discarding a time the owner just filled in.
                    # Not `disabled=not has_anchor` — widgets inside a form don't rerun on change,
                    # so the disabled state would reflect last run's checkbox value, not this one.
                    st.caption("Preferred time (uncheck the box above for flexible timing instead)")
                    h_col, m_col, ap_col = st.columns(3)
                    with h_col:
                        anchor_hour = st.number_input(
                            "Hour", min_value=1, max_value=12, value=8, step=1, format="%02d", key="add_task_hour",
                        )
                    with m_col:
                        anchor_minute = st.number_input(
                            "Minute", min_value=0, max_value=59, value=0, step=1, format="%02d", key="add_task_minute",
                        )
                    with ap_col:
                        anchor_period = st.radio("AM/PM", ["AM", "PM"], horizontal=True, key="add_task_period")

                    if st.form_submit_button("Add Task", type="primary"):
                        selected_pet.add_task(  # calls Pet.add_task() from backend
                            Task(
                                title=task_title,
                                duration_minutes=int(duration),
                                priority=priority,
                                recurrence=recurrence,
                                owner_required=owner_required,
                                preferred_time=_to_24h(anchor_hour, anchor_minute, anchor_period) if has_anchor else None,
                            )
                        )
                        st.session_state.plan = None  # plan is stale without this task

            parsed_key = f"ai_task_batch_parsed_{pid}"
            if parsed_key not in st.session_state:
                st.session_state[parsed_key] = None

            with st.expander(f"💬 Describe a task for {selected_pet.name} in plain English"):
                ai_client = _get_ai_client()
                if ai_client is None:
                    st.caption("AI entry unavailable, set GEMINI_API_KEY in a .env file to enable this.")
                else:
                    task_nl_text = st.text_area(
                        "e.g. \"Give her meds with breakfast, then a 30 min walk\"",
                        key=f"ai_task_text_{pid}",
                    )
                    if st.button("Parse with AI", key=f"ai_task_parse_btn_{pid}"):
                        try:
                            st.session_state[parsed_key] = parse_tasks_from_description(
                                task_nl_text, selected_pet, ai_client
                            )
                        except Exception:
                            st.session_state[parsed_key] = None
                            st.error("AI parsing failed unexpectedly, please use the form above instead.")

            parsed_batch = st.session_state.get(parsed_key)
            if parsed_batch is not None:
                _render_task_batch_preview(parsed_batch, selected_pet, parsed_key)

            st.divider()

            # Display current tasks per pet, with inline edit/remove before scheduling
            for pi, pet in enumerate(st.session_state.pets):
                if not pet.tasks:
                    continue
                st.markdown(f"**{pet.name}'s tasks:**")
                for ti, task in enumerate(pet.tasks):
                    if st.session_state.editing_task == (pi, ti):
                        with st.container(border=True):
                            e_title = st.text_input("Task title", value=task.title, key=f"edit_title_{pi}_{ti}")
                            e_col1, e_col2, e_col3 = st.columns(3)
                            with e_col1:
                                e_duration = st.number_input(
                                    "Duration (min)", min_value=1, max_value=240,
                                    value=task.duration_minutes, key=f"edit_duration_{pi}_{ti}",
                                )
                            with e_col2:
                                e_priority = st.selectbox(
                                    "Priority", ["low", "medium", "high"],
                                    index=["low", "medium", "high"].index(task.priority),
                                    key=f"edit_priority_{pi}_{ti}",
                                )
                            with e_col3:
                                e_recurrence = st.selectbox(
                                    "Repeats", RECURRENCE_OPTIONS,
                                    index=RECURRENCE_OPTIONS.index(task.recurrence),
                                    format_func=lambda r: _RECURRENCE_LABELS[r],
                                    key=f"edit_recurrence_{pi}_{ti}",
                                )
                            e_owner_required = st.checkbox(
                                "Requires owner's presence", value=task.owner_required,
                                key=f"edit_owner_required_{pi}_{ti}",
                            )
                            e_has_anchor = st.checkbox(
                                "Anchor to a specific time", value=task.preferred_time is not None,
                                key=f"edit_has_anchor_{pi}_{ti}",
                            )
                            if task.preferred_time:
                                default_hour, default_minute, default_period = _from_24h(task.preferred_time)
                            else:
                                default_hour, default_minute, default_period = 8, 0, "AM"
                            st.caption("Preferred time (used only if anchored, above)")
                            e_h_col, e_m_col, e_ap_col = st.columns(3)
                            with e_h_col:
                                e_hour = st.number_input(
                                    "Hour", min_value=1, max_value=12, value=default_hour, step=1,
                                    format="%02d", key=f"edit_hour_{pi}_{ti}",
                                )
                            with e_m_col:
                                e_minute = st.number_input(
                                    "Minute", min_value=0, max_value=59, value=default_minute, step=1,
                                    format="%02d", key=f"edit_minute_{pi}_{ti}",
                                )
                            with e_ap_col:
                                e_period = st.radio(
                                    "AM/PM", ["AM", "PM"], index=["AM", "PM"].index(default_period),
                                    horizontal=True, key=f"edit_period_{pi}_{ti}",
                                )
                            save_col, cancel_col = st.columns(2)
                            with save_col:
                                if st.button("Save", key=f"save_task_{pi}_{ti}"):
                                    task.apply_edit(
                                        title=e_title,
                                        duration_minutes=int(e_duration),
                                        priority=e_priority,
                                        recurrence=e_recurrence,
                                        owner_required=e_owner_required,
                                        preferred_time=_to_24h(e_hour, e_minute, e_period) if e_has_anchor else None,
                                    )
                                    st.session_state.editing_task = None
                                    st.session_state.plan = None
                                    st.rerun()
                            with cancel_col:
                                if st.button("Cancel", key=f"cancel_task_{pi}_{ti}"):
                                    st.session_state.editing_task = None
                                    st.rerun()
                    else:
                        if task.preferred_time:
                            end_time = compute_end_time(task.preferred_time, task.duration_minutes)
                            time_tag = f"  *({_to_12h(task.preferred_time)} – {_to_12h(end_time)})*"
                        else:
                            time_tag = ""
                        recur_tag = f"  *({_RECURRENCE_LABELS[task.recurrence].lower()})*"
                        row_col, edit_col, remove_col = st.columns([6, 1, 1])
                        with row_col:
                            st.write(f"  • {task.title} - {task.duration_minutes} min [{task.priority}]{recur_tag}{'  *(bg)*' if not task.owner_required else ''}{time_tag}")
                        with edit_col:
                            if st.button("Edit", key=f"edit_task_{pi}_{ti}"):
                                st.session_state.editing_task = (pi, ti)
                                st.rerun()
                        with remove_col:
                            if st.button("Remove", key=f"remove_task_{pi}_{ti}"):
                                pet.tasks.pop(ti)
                                st.session_state.editing_task = None  # index may now be stale
                                st.session_state.plan = None
                                st.rerun()

    # -----------------------------------------------------------------------
    # Schedule page
    # -----------------------------------------------------------------------
    else:
        st.subheader("Generate Schedule")

        pet_tasks = [(pet, pet.tasks) for pet in st.session_state.pets if pet.tasks]
        has_tasks = bool(pet_tasks)
        pending_conflicts = find_time_conflicts(pet_tasks) if has_tasks else []

        if pending_conflicts:
            st.warning("Some tasks share the same preferred time. Resolve these before generating a schedule:")
            for group in pending_conflicts:
                time_str = group[0][1].preferred_time
                # A task joining an already-confirmed group (e.g. it silently inherited a
                # time it wasn't meant to share) needs different, more pointed wording than
                # a brand-new pairing — otherwise it's easy to reflexively click "Yes" and
                # sweep an unintended task into an existing simultaneous block.
                confirmed = [(pet, task) for pet, task in group if task.concurrent_group == time_str]
                new_members = [(pet, task) for pet, task in group if task.concurrent_group != time_str]
                new_names = ", ".join(f"{pet.name}'s “{task.title}”" for pet, task in new_members)

                if confirmed:
                    confirmed_names = ", ".join(f"{pet.name}'s “{task.title}”" for pet, task in confirmed)
                    st.write(
                        f"**{_to_12h(time_str)}** - {new_names} also wants this time, "
                        f"same as your already-confirmed {confirmed_names}."
                    )
                    yes_label = f"Yes, include {new_names} too"
                    no_caption = f"If No: use Edit above to change {new_names}'s preferred time."
                else:
                    all_names = ", ".join(f"{pet.name}'s “{task.title}”" for pet, task in group)
                    st.write(f"**{_to_12h(time_str)}** - {all_names}")
                    yes_label = f"Yes, all {len(group)} at the same time" if len(group) > 2 else "Yes, same time"
                    no_caption = "If No: use Edit above to change one of these tasks' preferred time."

                yes_col, no_col = st.columns(2)
                with yes_col:
                    if st.button(yes_label, key=f"conflict_yes_{time_str}"):
                        confirm_concurrent_group(group)
                        st.session_state.plan = None
                        st.rerun()
                with no_col:
                    if st.button("No, different times", key=f"conflict_no_{time_str}"):
                        st.rerun()
                st.caption(no_caption)

        # Pre-flight overflow check: run the real scheduler once, eagerly, purely to
        # see if anything would be dropped — same "detect before the button unlocks"
        # idea as pending_conflicts above. generate_plan() only reads Task/Owner/Pet
        # and returns a fresh plan, so calling it here (and again for real on click,
        # below) is cheap and has no side effects.
        preview_plan = (
            MultiPetScheduler(owner=st.session_state.owner, pet_tasks=pet_tasks).generate_plan()
            if has_tasks and st.session_state.owner is not None and not pending_conflicts
            else None
        )
        overflow_units = preview_plan.unscheduled if preview_plan else []

        # Identifies *this specific* overflow (which tasks, at what available_minutes).
        # Comparing against the last acknowledged signature — rather than a plain
        # bool flag — means a stale "yes, push to tomorrow" auto-clears the moment
        # the task set or available time actually changes, with no need to hunt
        # down every place that already resets st.session_state.plan.
        overflow_signature = (
            frozenset(id(task) for _, task in overflow_units),
            st.session_state.owner.available_minutes if st.session_state.owner else None,
        )
        overflow_pending = bool(overflow_units) and st.session_state.overflow_ack_signature != overflow_signature

        if overflow_pending:
            # unscheduled_minutes_needed (not a naive sum) so a confirmed concurrent
            # group only counts once here too, matching how the scheduler charges it.
            needed_minutes = preview_plan.total_owner_minutes + unscheduled_minutes_needed(overflow_units)
            overflow_names = ", ".join(f"{pet.name}'s “{task.title}”" for pet, task in overflow_units)
            st.warning(
                f"Not enough time today to fit: {overflow_names}. "
                f"You have {st.session_state.owner.available_minutes} min available; "
                f"{needed_minutes} min would be needed to fit everything due today."
            )
            edit_col, ack_col = st.columns(2)
            with edit_col:
                # Prefilled with exactly enough minutes to fit everything due today.
                suggested_avail = st.number_input(
                    "Update available time (min)", min_value=10, max_value=480,
                    value=min(needed_minutes, 480), key="overflow_avail_input",
                )
                if st.button("Update available time", key="overflow_update_avail_btn"):
                    st.session_state.owner.available_minutes = int(suggested_avail)
                    st.session_state.plan = None  # old plan is stale, time budget changed
                    st.rerun()
            with ack_col:
                st.caption(
                    "Or leave today as-is — any unfinished due task simply stays due "
                    "and will be picked up next time you generate a schedule."
                )
                # No data actually moves here — a due task that doesn't get scheduled
                # today naturally stays due (see Task.is_due), so "pushing" it to
                # tomorrow just means: stop warning about it and let generation proceed.
                if st.button("Push overflow to next day", key="overflow_ack_btn"):
                    st.session_state.overflow_ack_signature = overflow_signature
                    st.rerun()

        can_generate = (
            st.session_state.owner is not None and has_tasks
            and not pending_conflicts and not overflow_pending
        )

        if not can_generate and not pending_conflicts and not overflow_pending:
            st.caption("Add at least one pet with a task, in the Pets/Tasks sections, to continue.")

        if st.button("Generate schedule", disabled=not can_generate, type="primary"):
            # Clear stale checkbox state from any previous plan
            for key in list(st.session_state.keys()):
                if key.startswith("done_"):
                    del st.session_state[key]

            scheduler = MultiPetScheduler(owner=st.session_state.owner, pet_tasks=pet_tasks)
            st.session_state.plan = scheduler.generate_plan()

        if st.session_state.plan:
            plan = st.session_state.plan
            owner = st.session_state.owner

            st.markdown(f"### Daily Plan - {owner.name}")

            if not plan.scheduled_slots:
                st.warning("No tasks fit within the available time.")
            else:
                slots = sorted(plan.scheduled_slots, key=lambda s: (s[0], s[3]))  # time, bg last

                for i, (time, pet, task, is_bg) in enumerate(slots):
                    col1, col2 = st.columns([1, 6])
                    with col1:
                        done = st.checkbox("", value=task.completed, key=f"done_{i}")
                        if done:
                            task.mark_complete()  # stamps last_completed_date for is_due()
                        else:
                            task.completed = False
                    with col2:
                        bg_tag = " *(bg)*" if is_bg else ""
                        line = f"**{_to_12h(time)}** - [{pet.name}] {task.title}{bg_tag} ({task.duration_minutes} min)"
                        st.markdown(f"~~{line}~~" if task.completed else line)

                completed_count = sum(1 for _, _, t, _ in slots if t.completed)
                st.caption(f"Progress: {completed_count}/{len(slots)} tasks done  |  Owner time: {plan.total_owner_minutes} min")

                if any(s[3] for s in slots):
                    st.caption("*(bg) = runs in background, no owner needed*")

                if plan.unscheduled:
                    st.warning(
                        "Not scheduled today (ran out of owner time): "
                        + ", ".join(f"{task.title} ({pet.name})" for pet, task in plan.unscheduled)
                    )

                if plan.missed_anchors:
                    st.info(
                        "Missed preferred time: "
                        + ", ".join(
                            f"{task.title} ({pet.name}) wanted {_to_12h(task.preferred_time)}"
                            for pet, task in plan.missed_anchors
                        )
                    )

                with st.expander("Why was this plan chosen?"):
                    for _, pet, task, is_bg in slots:
                        bg_note = " - no owner needed" if is_bg else ""
                        st.write(f"• **{task.title}** [{pet.name}] - {task.priority} priority{bg_note}")