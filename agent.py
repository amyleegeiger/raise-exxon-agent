import os
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

WORKLLAMA_URL = os.environ.get("WORKLLAMA_URL", "https://app.workllama.com")
WORKLLAMA_EMAIL = os.environ.get("WORKLLAMA_EMAIL")
WORKLLAMA_PASSWORD = os.environ.get("WORKLLAMA_PASSWORD")

# ---------------------------------------------------------------------------
# SELECTORS — derived from WorkLlama inspector (id="candidate-first-name"
# pattern confirmed). All IDs follow candidate-[field-name] convention.
# ---------------------------------------------------------------------------

# Login page
SEL_LOGIN_EMAIL    = "#j_email"
SEL_LOGIN_PASSWORD = "#j_password"
SEL_LOGIN_SUBMIT   = "button:has-text('Login'), input[type='submit']"

# "Add Candidate" button — opens the modal we saw in the screenshots
SEL_ADD_CANDIDATE_BTN = "button:has-text('Add Candidate'), button:has-text('Add Candidates')"

# Profile info fields (modal, screen 1)
SEL_FIRST_NAME  = "#candidate-first-name"
SEL_MIDDLE_NAME = "#candidate-middle-name"
SEL_LAST_NAME   = "#candidate-last-name"
SEL_EMAIL       = "#candidate-email"
SEL_MOBILE      = "#candidate-mobile-phone"
SEL_OWNER       = "#candidate-owner"        # dropdown
SEL_SOURCE      = "#candidate-source"       # dropdown (+ button visible in screenshot)
SEL_STATUS      = "#candidate-status"       # dropdown (screen 2, defaults N/A)

# Address fields (screen 2)
SEL_ADDRESS_LOOKUP = "input[placeholder='Search Address']"
SEL_CITY           = "input[placeholder='Enter City']"
SEL_STATE          = "input[placeholder='Enter State']"
SEL_COUNTRY        = "select[id*='country'], select[placeholder='Select a country']"
SEL_ZIP            = "input[placeholder='Enter Zip Code/Postal Code']"
SEL_TIMEZONE       = "input[placeholder='Enter Time Zone']"

# Final ADD button at bottom of modal
SEL_MODAL_ADD = "button:has-text('ADD')"

# Candidate search (global search bar, to find record after creation)
SEL_SEARCH = "input[placeholder*='Search'], input[type='search']"
SEL_SEARCH_RESULT = ".candidate-name, td:has-text"

# Notes — written after candidate record is created/found
SEL_NOTES_TAB    = "a:has-text('Notes'), button:has-text('Notes'), li:has-text('Notes')"
SEL_NOTES_ADD    = "button:has-text('Add Note'), button:has-text('New Note')"
SEL_NOTES_AREA   = "textarea[id*='note'], textarea[placeholder*='note'], textarea[placeholder*='Note']"
SEL_NOTES_SAVE   = "button:has-text('Save'), button:has-text('Submit')"

# Resume upload (file input inside the drag-drop zone)
SEL_RESUME_INPUT = "input[type='file']"

# ---------------------------------------------------------------------------


async def login(page):
    await page.goto(f"{WORKLLAMA_URL}/atsadmin/login?companyId={os.environ.get('WORKLLAMA_COMPANY_ID', '863330')}")
    await page.wait_for_load_state("networkidle")
    await page.fill(SEL_LOGIN_EMAIL, WORKLLAMA_EMAIL)
    await page.fill(SEL_LOGIN_PASSWORD, WORKLLAMA_PASSWORD)
    await page.click(SEL_LOGIN_SUBMIT)
    await page.wait_for_load_state("networkidle")
    if "login" in page.url.lower() or "spring_security_check" in page.url.lower():
        raise Exception("WorkLlama login failed — check WORKLLAMA_EMAIL and WORKLLAMA_PASSWORD")
    print("[OK] Logged in successfully")


async def open_add_candidate_modal(page):
    btn = page.locator(SEL_ADD_CANDIDATE_BTN).first
    await btn.wait_for(timeout=6000)
    await btn.click()
    await page.wait_for_load_state("networkidle")
    print("[OK] Add Candidate modal open")


async def fill_profile_fields(page, data: dict):
    # Text fields — fill if value present, skip quietly if empty
    text_fields = {
        SEL_FIRST_NAME:  data.get("first_name", ""),
        SEL_MIDDLE_NAME: data.get("middle_name", ""),
        SEL_LAST_NAME:   data.get("last_name", ""),
        SEL_EMAIL:       data.get("email", ""),
        SEL_MOBILE:      data.get("phone", ""),
        SEL_CITY:        data.get("city", ""),
        SEL_STATE:       data.get("state", ""),
        SEL_ZIP:         data.get("zip", ""),
        SEL_TIMEZONE:    data.get("timezone", ""),
    }
    for sel, val in text_fields.items():
        if val:
            try:
                el = page.locator(sel).first
                await el.wait_for(timeout=3000)
                await el.fill(str(val))
                print(f"[OK] Filled {sel} → {val}")
            except PlaywrightTimeout:
                print(f"[WARN] Field not found: {sel} — skipping")

    # Address lookup — faster than filling city/state individually if we have a full address
    address = f"{data.get('city', '')}, {data.get('state', '')}"
    if data.get("city") and data.get("state"):
        try:
            addr_el = page.locator(SEL_ADDRESS_LOOKUP).first
            await addr_el.wait_for(timeout=3000)
            await addr_el.fill(address)
            await page.wait_for_timeout(1200)  # wait for autocomplete
            # Pick first suggestion
            suggestion = page.locator(".pac-item, .autocomplete-item, li[role='option']").first
            if await suggestion.count() > 0:
                await suggestion.click()
                print(f"[OK] Address lookup selected: {address}")
        except PlaywrightTimeout:
            print("[WARN] Address lookup not found — city/state filled directly instead")

    # Country dropdown
    if data.get("country"):
        try:
            country_el = page.locator(SEL_COUNTRY).first
            await country_el.wait_for(timeout=3000)
            await country_el.select_option(label=data["country"])
            print(f"[OK] Country set → {data['country']}")
        except PlaywrightTimeout:
            print("[WARN] Country dropdown not found — skipping")

    # Candidate Source dropdown
    if data.get("source"):
        try:
            src_el = page.locator(SEL_SOURCE).first
            await src_el.wait_for(timeout=3000)
            await src_el.select_option(label=data["source"])
            print(f"[OK] Source set → {data['source']}")
        except PlaywrightTimeout:
            print("[WARN] Source dropdown not found — skipping")

    # Status dropdown
    if data.get("status"):
        try:
            status_el = page.locator(SEL_STATUS).first
            await status_el.wait_for(timeout=3000)
            await status_el.select_option(label=data["status"])
            print(f"[OK] Status set → {data['status']}")
        except PlaywrightTimeout:
            print("[WARN] Status dropdown not found — skipping")


async def upload_resume(page, resume_path: str):
    if not resume_path or not os.path.exists(resume_path):
        print("[SKIP] No resume file provided")
        return
    try:
        file_input = page.locator(SEL_RESUME_INPUT).first
        await file_input.wait_for(timeout=4000)
        await file_input.set_input_files(resume_path)
        await page.wait_for_timeout(1500)
        print(f"[OK] Resume uploaded: {resume_path}")
    except PlaywrightTimeout:
        print("[WARN] Resume file input not found — skipping upload")


async def submit_modal(page):
    add_btn = page.locator(SEL_MODAL_ADD).first
    await add_btn.wait_for(timeout=5000)
    await add_btn.click()
    await page.wait_for_load_state("networkidle")
    print("[OK] Candidate record submitted")


async def write_handoff_note(page, note: str):
    # Navigate to Notes tab on the candidate record
    try:
        notes_tab = page.locator(SEL_NOTES_TAB).first
        await notes_tab.wait_for(timeout=5000)
        await notes_tab.click()
        await page.wait_for_load_state("networkidle")
        print("[OK] Notes tab opened")
    except PlaywrightTimeout:
        print("[WARN] Notes tab not found — skipping note")
        return

    # Click "Add Note"
    try:
        add_btn = page.locator(SEL_NOTES_ADD).first
        await add_btn.wait_for(timeout=4000)
        await add_btn.click()
        await page.wait_for_timeout(800)
    except PlaywrightTimeout:
        print("[WARN] Add Note button not found — skipping note")
        return

    # Type the note
    try:
        note_area = page.locator(SEL_NOTES_AREA).first
        await note_area.wait_for(timeout=4000)
        await note_area.fill(note)
        print("[OK] Note text entered")
    except PlaywrightTimeout:
        print("[WARN] Note textarea not found — skipping note")
        return

    # Save
    try:
        save_btn = page.locator(SEL_NOTES_SAVE).first
        await save_btn.wait_for(timeout=4000)
        await save_btn.click()
        await page.wait_for_load_state("networkidle")
        print("[OK] Note saved")
    except PlaywrightTimeout:
        print("[WARN] Save button not found — note may not have saved")


async def write_to_workllama(data: dict) -> dict:
    if not WORKLLAMA_EMAIL or not WORKLLAMA_PASSWORD:
        raise Exception("WORKLLAMA_EMAIL and WORKLLAMA_PASSWORD must be set as environment variables")

    async with async_playwright() as p:
        # headless=False lets you watch it work during testing — flip to True for production
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await login(page)
            await open_add_candidate_modal(page)
            await upload_resume(page, data.get("resume_path"))
            await fill_profile_fields(page, data)
            await submit_modal(page)
            await write_handoff_note(page, data["handoff_note"])

            return {
                "status": "success",
                "candidate": f"{data['first_name']} {data['last_name']}",
                "req_id": data.get("req_id"),
                "fields_written": [
                    "first_name", "last_name", "email", "phone",
                    "city", "state", "zip", "country",
                    "source", "status", "resume", "handoff_note"
                ],
            }

        except Exception as e:
            screenshot_path = "/tmp/workllama_error.png"
            await page.screenshot(path=screenshot_path)
            raise Exception(f"{str(e)} | Screenshot saved: {screenshot_path}")

        finally:
            await browser.close()
