"""
ReelTrip — Flight Agent Server (Port 8001)  v10.0
==================================================
Changes in v10.0 (Definitive Fix — from forensic debug HTML analysis):
  Correct 3-step Google Flights flow per actual DOM behaviour:
  Step 1 — Click entire pIav2d li row (not a nested chevron button).
  Step 2 — Click 'Select flight' button (aria-label='Select flight').
  Step 3 — Click 'Done' button (jsname='McfNlf') — was missing in all prior versions.
  Repeat for return flight, then hit first Continue on Booking Options page.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import quote_plus

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Selenium imports (graceful import so server starts even without selenium) ──
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import (
        TimeoutException,
        NoSuchElementException,
        ElementNotInteractableException,
        WebDriverException,
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("flight_agent_server")

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="ReelTrip Flight Agent Server", version="10.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory status store ────────────────────────────────────────────────────
_status_store: Dict[str, Dict[str, Dict[str, Any]]] = {}
_status_lock = threading.Lock()

AGENT_TIMEOUT_SECONDS = 300  # Increased to 5 minutes


# ═══════════════════════════════════════════════════════════════════════════════
# STATUS HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def write_status(
    session_id: str,
    flight_id: str,
    status: str,
    message: str = "",
    error_detail: Optional[str] = None,
    booking_url: Optional[str] = None,
) -> None:
    """Thread-safe status update — matches FlightCard.tsx STATUS_STEPS keys exactly."""
    if not message or message.strip() == "":
        message = {
            "initializing":           "Agent starting...",
            "opening_browser":        "Opening Chrome and loading Google Flights...",
            "searching_flights":      "Searching for available flights...",
            "filling_cities":         "Route details confirmed...",
            "selecting_date":         "Travel dates confirmed...",
            "selecting_best_option":  "Selecting best flight option...",
            "proceeding_to_booking":  "Navigating to booking page...",
            "booking_page_open":      "Booking page ready! Check your Chrome window.",
            "error":                  "An error occurred. Use the manual Google Flights link.",
        }.get(status, f"Status: {status}")

    with _status_lock:
        if session_id not in _status_store:
            _status_store[session_id] = {}
        entry = _status_store[session_id].setdefault(flight_id, {})
        entry["status"]       = status
        entry["message"]      = message
        entry["error_detail"] = error_detail
        entry["timestamp"]    = time.time()
        if booking_url:
            entry["booking_url"] = booking_url
    logger.info(f"[{session_id}/{flight_id}] STATUS={status} | {message}")


def read_status(session_id: str, flight_id: str) -> Optional[Dict[str, Any]]:
    with _status_lock:
        return _status_store.get(session_id, {}).get(flight_id)

def safe_error_message(e: Exception) -> str:
    """Always return a non-empty, human-readable error string."""
    msg = str(e)
    if not msg or msg.strip() == "":
        msg = type(e).__name__
    return msg[:200]

def format_selenium_error(e: Exception) -> str:
    """Selenium-specific error formatting."""
    error_type = type(e).__name__

    SELENIUM_ERROR_MAP = {
        "TimeoutException":           "Timed out waiting for flight results to load. Google Flights may be slow.",
        "NoSuchElementException":     "Could not find flight selection button. Google Flights UI may have changed.",
        "ElementNotInteractableException": "Flight button found but not clickable. Page may have an overlay.",
        "StaleElementReferenceException": "Page changed unexpectedly during selection. Try again.",
        "WebDriverException":         "Chrome browser encountered an error. Check if Chrome is installed.",
        "ElementClickInterceptedException": "Another element is blocking the flight button (possible overlay).",
    }

    return SELENIUM_ERROR_MAP.get(error_type, f"{error_type}: {safe_error_message(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# SCREENSHOT HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def take_debug_screenshot(driver: Any, label: str, session_id: str) -> str:
    """Save a debug screenshot; returns the path."""
    try:
        screenshots_dir = os.path.join(os.path.dirname(__file__), "debug_screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        safe_sid = session_id.replace("-", "")[:12]
        path = os.path.join(screenshots_dir, f"{safe_sid}_{label}_{timestamp}.png")
        if driver:
            driver.save_screenshot(path)
            logger.info(f"[screenshot] {path}")
        return path
    except Exception as exc:
        logger.warning(f"Screenshot failed: {exc}")
        return ""


def save_debug_info(driver: Any, label: str, session_id: str) -> None:
    """Save screenshot + full page HTML for maximum debugging info."""
    try:
        screenshots_dir = os.path.join(os.path.dirname(__file__), "debug_screenshots")
        html_dir = os.path.join(os.path.dirname(__file__), "debug_html")
        os.makedirs(screenshots_dir, exist_ok=True)
        os.makedirs(html_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        safe_sid = session_id.replace("-", "")[:12]

        # Screenshot
        screenshot_path = os.path.join(screenshots_dir, f"{safe_sid}_{label}_{timestamp}.png")
        driver.save_screenshot(screenshot_path)

        # Full page HTML
        html_path = os.path.join(html_dir, f"{safe_sid}_{label}_{timestamp}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        logger.info(f"[debug] Screenshot: {screenshot_path}")
        logger.info(f"[debug] HTML: {html_path}")
        logger.info(f"[debug] Title: {driver.title}")
        logger.info(f"[debug] URL: {driver.current_url}")
    except Exception as exc:
        logger.warning(f"save_debug_info failed: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
# CHROMEDRIVER FACTORY  (Anti-bot detection)
# ═══════════════════════════════════════════════════════════════════════════════

def create_driver() -> Any:
    """Create a Chrome WebDriver with anti-detection options applied."""
    options = Options()

    # Anti-detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Realistic browser profile
    options.add_argument("--window-size=1366,768")
    options.add_argument("--start-maximized")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    # Stability
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=en-IN")
    options.add_argument("--accept-lang=en-IN,en")

    # Do NOT use headless — Google detects it
    # options.add_argument("--headless")  ← NEVER add this

    driver = webdriver.Chrome(options=options)

    # Remove navigator.webdriver flag + spoof plugins/languages
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en'] });
        """
    })

    driver.set_window_size(1366, 768)
    return driver


# ═══════════════════════════════════════════════════════════════════════════════
# GOOGLE FLIGHTS URL BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def build_google_flights_url(
    origin_iata: str,
    dest_iata: str,
    travel_date: str,
    return_date: Optional[str],
    num_passengers: int,
) -> str:
    """
    Build a Google Flights URL with origin, destination, and dates pre-filled.
    travel_date format: "YYYY-MM-DD"
    return_date format: "YYYY-MM-DD" or None for one-way
    """
    base = "https://www.google.com/travel/flights"

    origin_part = origin_iata if origin_iata else "origin"
    dest_part   = dest_iata   if dest_iata   else "destination"

    if travel_date and return_date:
        q = f"Flights from {origin_part} to {dest_part} on {travel_date} returning {return_date}"
    elif travel_date:
        q = f"Flights from {origin_part} to {dest_part} on {travel_date}"
    else:
        q = f"Flights from {origin_part} to {dest_part}"

    return f"{base}?q={quote_plus(q)}&curr=INR"


# ═══════════════════════════════════════════════════════════════════════════════
# CONSENT BANNER DISMISSAL
# ═══════════════════════════════════════════════════════════════════════════════

def dismiss_consent_banner(driver: Any) -> None:
    consent_xpaths = [
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i agree')]",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'reject all')]",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
    ]
    for xpath in consent_xpaths:
        try:
            btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(1)
            logger.info("Consent banner dismissed.")
            return
        except Exception:
            continue
    logger.info("No consent banner found.")


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-HEALING SELECTOR SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# SELECTOR CONSTANTS  (v10.0 — Forensic analysis of real debug HTML files)
# ═══════════════════════════════════════════════════════════════════════════════

# ── ROW SELECTORS: click the entire pIav2d li row — NOT a nested button ──────
# pIav2d is the confirmed class for Google Flights result rows (from debug HTML)
FLIGHT_ROW_SELECTORS = [
    (By.XPATH, "(//li[contains(@class,'pIav2d')])[1]"),
    (By.XPATH, "(//li[.//span[contains(text(),'₹')]])[1]"),
    (By.XPATH, "(//div[@role='main']//ul/li)[1]"),
    (By.XPATH, "(//li[.//div[contains(text(),'hr') or contains(text(),' h ')]])[1]"),
]

# Keep alias so any remaining references to CHEVRON_SELECTORS still work
CHEVRON_SELECTORS = FLIGHT_ROW_SELECTORS

# ── "Select flight" button: aria-label is the most stable attribute ──────────
# Confirmed from debug HTML: <button aria-label="Select flight" ...>
SELECT_FLIGHT_BUTTON_SELECTORS = [
    (By.XPATH, "(//button[@aria-label='Select flight'])[1]"),
    (By.XPATH, "(//button[.//span[normalize-space(.)='Select flight']])[1]"),
    (By.XPATH, "(//button[.//span[@jsname='V67aGc'][normalize-space(.)='Select flight']])[1]"),
    (By.XPATH, "(//button[contains(@class,'my6Xrf') and contains(@class,'wJjnG')])[1]"),
]

# ── "Done" button: appears after clicking Select flight (MISSING STEP in v8) ─
# Confirmed from debug HTML: <button jsname="McfNlf">Done</button>
DONE_BUTTON_SELECTORS = [
    (By.XPATH, "//button[@jsname='McfNlf']"),
    (By.XPATH, "//button[@aria-label='Done']"),
    (By.XPATH, "//button[.//span[normalize-space(.)='Done']]"),
    (By.XPATH, "//button[contains(@class,'ksBjEc') and contains(@class,'lKxP2d')]"),
    (By.XPATH, "(//button[normalize-space(.)='Done'])[1]"),
]

# ── First "Continue" button on Booking Options page ──────────────────────────
FIRST_CONTINUE_BUTTON_SELECTORS = [
    (By.XPATH, "(//button[normalize-space(.)='Continue'])[1]"),
    (By.XPATH, "(//a[normalize-space(.)='Continue'])[1]"),
    (By.XPATH,
     "(//div[contains(@class,'booking') or .//div[contains(.,'Book with')]]"
     "//button[contains(.,'Continue')])[1]"),
    (By.XPATH, "(//button[contains(normalize-space(.),'Continue')])[1]"),
]

# ── Booking Options page detection signals ───────────────────────────────────
BOOKING_OPTIONS_PAGE_SIGNALS = [
    (By.XPATH, "//div[contains(., 'Booking options')]"),
    (By.XPATH, "//div[contains(., 'Book with')]"),
    (By.XPATH, "//div[contains(., 'Selected flights')]"),
    (By.XPATH, "//button[normalize-space(.)='Continue']"),
    (By.XPATH, "//a[normalize-space(.)='Continue']"),
]

# ── Return flight page detection signals ─────────────────────────────────────
RETURN_PAGE_SIGNALS = [
    (By.XPATH, "//h1[contains(., 'returning') or contains(., 'Return')]"),
    (By.XPATH, "//h2[contains(., 'returning') or contains(., 'Return')]"),
    (By.XPATH, "//div[contains(., 'returning flights')]"),
    (By.XPATH, "//span[contains(., 'Choose return')]"),
    (By.XPATH, "//div[contains(., 'Top returning')]"),
]

# ── Airline/OTA website domains (agent stops here) ───────────────────────────
AIRLINE_WEBSITE_SIGNALS = [
    "airarabia.com", "gotogate.com", "cleartrip.com", "makemytrip.com",
    "kiwi.com", "trip.com", "flightnetwork.com", "budgetair.com",
]


# ═══════════════════════════════════════════════════════════════════════════════
# CORE HELPER UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def safe_scroll_and_click(driver: Any, element: Any) -> None:
    """Scroll into view, then try ActionChains click, fall back to JS click."""
    driver.execute_script(
        "arguments[0].scrollIntoView({behavior:'smooth', block:'center'});",
        element
    )
    time.sleep(0.6)
    try:
        ActionChains(driver).move_to_element(element).click().perform()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


# Keep old alias so nothing else breaks
safe_scroll_and_js_click = safe_scroll_and_click


def find_and_click_first_match(
    driver: Any,
    selectors: list,
    timeout: int = 20,
    label: str = "element",
) -> bool:
    """
    Try selectors in order. For each selector, check quickly (3s) whether it
    exists. Only spend the full timeout on the FIRST selector that is found.
    Returns True on success, False if every selector fails.
    """
    QUICK_CHECK_TIMEOUT = 3  # seconds per selector for existence check

    for by, selector in selectors:
        try:
            # Quick check: does this element exist at all?
            element = WebDriverWait(driver, QUICK_CHECK_TIMEOUT).until(
                EC.presence_of_element_located((by, selector))
            )
            # Element exists — now wait for it to be clickable (full timeout)
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            safe_scroll_and_click(driver, element)
            logger.info(f"[Agent] ✓ Clicked {label}: {selector[:70]}")
            return True
        except Exception as exc:
            logger.debug(f"[Agent] ✗ {label} [{selector[:60]}]: {type(exc).__name__}")
            continue

    logger.warning(f"[Agent] All selectors failed for: {label}")
    return False


def click_to_expand(driver: Any, element: Any) -> bool:
    """
    DEPRECATED — the 'Select flight' buttons exist in DOM before any row is
    clicked, so the old confirmation check was a false positive.
    This stub is kept so nothing referencing it crashes; it is not called by
    the new step functions.
    """
    return False


def step_click_done(driver: Any, session_id: str, flight_id: str, label: str = "") -> bool:
    """
    Click the 'Done' button that appears after 'Select flight' is clicked.
    This is the missing step that was causing the entire flow to stall.
    Returns True if Done was clicked, False if not found (non-fatal).
    """
    write_status(session_id, flight_id, "selecting_best_option",
                 f"Confirming {label} selection...")
    logger.info(f"[Agent] Looking for Done button after {label} Select flight...")

    for by, selector in DONE_BUTTON_SELECTORS:
        try:
            element = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((by, selector))
            )
            safe_scroll_and_click(driver, element)
            logger.info(f"[Agent] ✓ Done clicked via: {selector[:60]}")
            time.sleep(2)
            return True
        except Exception as exc:
            logger.debug(f"[Agent] Done selector failed [{selector[:50]}]: {type(exc).__name__}")
            continue

    logger.warning(f"[Agent] Done button not found after {label} Select flight — continuing anyway")
    return False


def wait_for_any(
    driver: Any,
    selectors: list,
    timeout: int = 25,
) -> Any:
    """Wait until ANY selector is present; return the element or None."""
    for by, selector in selectors:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except Exception:
            continue
    return None


def is_on_booking_options_page(driver: Any) -> bool:
    """True when the Booking Options page (Image 6) is visible."""
    for by, selector in BOOKING_OPTIONS_PAGE_SIGNALS:
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((by, selector))
            )
            return True
        except Exception:
            continue
    return False


def is_on_airline_website(driver: Any) -> bool:
    """True once the browser has left Google and landed on a carrier / OTA."""
    current_url = driver.current_url.lower()
    return (
        "google.com" not in current_url
        and (
            any(site in current_url for site in AIRLINE_WEBSITE_SIGNALS)
            or len(current_url) > 10
        )
    )


# Kept for backwards-compat (find_element_with_fallback was used by old steps)
def find_element_with_fallback(
    driver: Any,
    selector_list: list,
    timeout: int = 15,
    label: str = "element",
) -> Any:
    from selenium.common.exceptions import TimeoutException as _TE
    last_exc: Optional[Exception] = None
    for by, selector in selector_list:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            logger.info(f"[selector] Found {label} via: {selector}")
            return element
        except Exception as exc:
            last_exc = exc
            logger.debug(f"[selector] Failed {selector}: {exc}")
            continue
    raise _TE(f"All selectors failed for '{label}'. Last error: {last_exc}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE STATE & OVERLAY HANDLING
# ═══════════════════════════════════════════════════════════════════════════════

def handle_page_state(driver: Any, session_id: str, flight_id: str) -> None:
    """Dismiss consent banners, travel advisories, and sort by Cheapest."""
    dismiss_consent_banner(driver)

    # Travel restricted / Airspace closure banner
    try:
        banners = driver.find_elements(
            By.XPATH,
            "//div[contains(., 'Travel restricted') or contains(., 'Airspace closure')]",
        )
        if banners:
            driver.execute_script(
                "arguments[0].scrollIntoView(); window.scrollBy(0,300);", banners[0]
            )
            time.sleep(1)
            write_status(session_id, flight_id, "searching_flights", "Travel advisory noted. Scrolling past...")
    except Exception:
        pass

    # Sort by Cheapest tab
    try:
        cheap_tab = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "//div[@role='tab'][contains(., 'Cheapest')] | "
                 "//button[contains(., 'Cheapest')]")
            )
        )
        cheap_tab.click()
        time.sleep(2)
        write_status(session_id, flight_id, "searching_flights", "Sorted by cheapest price.")
    except Exception:
        pass

    # Dismiss "Prices are estimates" / modal
    try:
        dismiss_btns = driver.find_elements(
            By.XPATH,
            "//button[contains(., 'Got it') or contains(., 'Dismiss') or contains(., 'Close')]",
        )
        if dismiss_btns:
            dismiss_btns[0].click()
            time.sleep(1)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT FLOW STEPS  (v10.0 — 3-step row→select→done flow)
# ═══════════════════════════════════════════════════════════════════════════════

def step_open_google_flights(
    driver: Any, payload: Dict[str, Any], session_id: str, flight_id: str
) -> None:
    url = build_google_flights_url(
        payload.get("origin", {}).get("iata", ""),
        payload.get("destination", {}).get("iata", ""),
        payload.get("travel_date", ""),
        payload.get("return_date"),
        int(payload.get("num_passengers", 1)),
    )
    write_status(session_id, flight_id, "opening_browser", "Loading Google Flights...", booking_url=url)
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    save_debug_info(driver, "page_initial_load", session_id)
    handle_page_state(driver, session_id, flight_id)


def step_wait_for_results(driver: Any, session_id: str, flight_id: str) -> None:
    write_status(session_id, flight_id, "searching_flights",
                 "Waiting for Google Flights results...")

    RESULT_SIGNALS = [
        (By.XPATH, "//li[.//span[contains(text(),'₹')]]"),
        (By.XPATH, "//div[@role='main']//ul/li"),
        (By.XPATH, "//div[contains(., 'Top departing')]"),
        (By.XPATH, "//li[.//span[contains(text(),'hr') or contains(text(),' h ')]]"),
    ]
    result = wait_for_any(driver, RESULT_SIGNALS, timeout=25)
    if not result:
        save_debug_info(driver, "no_results_detected", session_id)
        raise Exception(
            "Flight results did not load. "
            "Check debug_screenshots/page_initial_load.png"
        )
    save_debug_info(driver, "results_visible", session_id)
    time.sleep(2)
    # Do NOT write filling_cities or selecting_date here — run_full_booking_flow does it


def payload_date_str(driver: Any) -> str:
    """Best-effort: return current page URL fragment as a date hint."""
    try:
        return driver.current_url.split("q=")[1][:40]
    except Exception:
        return "(see URL)"


# ═══════════════════════════════════════════════════════════════════════════════
# JAVASCRIPT-BASED FLIGHT INTERACTION HELPERS
# These bypass Selenium's EC.element_to_be_clickable checks which fail on
# Google Flights due to layered UI containers. JS clicks work reliably.
# ═══════════════════════════════════════════════════════════════════════════════

def _click_first_flight_row(driver: Any, session_id: str, label: str) -> bool:
    """
    Click the first visible flight row in Google Flights results.
    Uses pIav2d li class (confirmed from debug HTML).
    Falls back to generic ul/li selectors.
    Returns True if a row was clicked.
    """
    ROW_SELECTORS = [
        # PRIMARY: pIav2d confirmed class from debug HTML analysis
        (By.XPATH, "(//li[contains(@class,'pIav2d')])[1]"),
        # FALLBACK 1: First li containing INR price
        (By.XPATH, "(//li[.//span[contains(text(),'₹')]])[1]"),
        # FALLBACK 2: First li in main results area
        (By.XPATH, "(//div[@role='main']//ul/li)[1]"),
        # FALLBACK 3: Duration-based li
        (By.XPATH, "(//li[.//div[contains(text(),'hr ')]])[1]"),
    ]

    for by, selector in ROW_SELECTORS:
        try:
            element = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((by, selector))
            )
            # Scroll into view
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});",
                element
            )
            time.sleep(0.5)
            # Try ActionChains first (most natural), fall back to JS click
            try:
                ActionChains(driver).move_to_element(element).click().perform()
            except Exception:
                driver.execute_script("arguments[0].click();", element)
            logger.info(f"[Agent] ✓ {label} row clicked: {selector[:60]}")
            return True
        except Exception as exc:
            logger.debug(f"[Agent] Row selector failed [{selector[:50]}]: {type(exc).__name__}")
            continue

    return False


def _js_click_select_flight(driver: Any) -> None:
    """
    Click 'Select flight' button via JavaScript.
    Finds the FIRST VISIBLE button with aria-label='Select flight'
    and dispatches a real click event. Bypasses EC.element_to_be_clickable.

    JS logic:
    1. Get ALL buttons with aria-label='Select flight'
    2. Find the first one where offsetParent !== null (i.e. visible in layout)
    3. Scroll it into view and click it
    4. If no visible one found, click the first one anyway (JS ignores display)
    """
    js_click_script = """
    var buttons = document.querySelectorAll("button[aria-label='Select flight']");
    var clicked = false;

    // Try to find a visible button first
    for (var i = 0; i < buttons.length; i++) {
        var b = buttons[i];
        if (b.offsetParent !== null) {
            b.scrollIntoView({behavior: 'smooth', block: 'center'});
            b.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            clicked = true;
            break;
        }
    }

    // If no visible button found, click the first one anyway
    if (!clicked && buttons.length > 0) {
        buttons[0].scrollIntoView({behavior: 'smooth', block: 'center'});
        buttons[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        clicked = true;
    }

    return clicked;
    """
    result = driver.execute_script(js_click_script)
    if result:
        logger.info("[Agent] ✓ Select flight button clicked via JavaScript")
    else:
        logger.warning("[Agent] ⚠ Select flight button not found via JS — page may have changed")
        # Try XPath fallback even if JS failed
        try:
            btn = driver.find_element(By.XPATH, "//button[@aria-label='Select flight']")
            driver.execute_script("arguments[0].click();", btn)
            logger.info("[Agent] ✓ Select flight clicked via XPath fallback")
        except Exception:
            logger.warning("[Agent] Select flight XPath fallback also failed")


def _js_click_done(driver: Any) -> None:
    """
    Click 'Done' button via JavaScript.
    Done button appears after 'Select flight' is clicked — it confirms the selection
    and advances to the next screen.

    Tries jsname='McfNlf' first (most specific, confirmed from debug HTML),
    then aria-label='Done', then span text='Done'.
    """
    js_done_script = """
    var done = null;

    // Strategy 1: jsname='McfNlf' (confirmed from debug HTML files)
    done = document.querySelector("button[jsname='McfNlf']");

    // Strategy 2: aria-label='Done'
    if (!done) {
        done = document.querySelector("button[aria-label='Done']");
    }

    // Strategy 3: span containing 'Done' inside a button
    if (!done) {
        var spans = document.querySelectorAll("span");
        for (var s of spans) {
            if (s.textContent.trim() === 'Done') {
                var parent = s.closest('button');
                if (parent) { done = parent; break; }
            }
        }
    }

    // Strategy 4: any button with exact text 'Done'
    if (!done) {
        var allBtns = document.querySelectorAll("button");
        for (var b of allBtns) {
            if (b.textContent.trim() === 'Done') { done = b; break; }
        }
    }

    if (done) {
        done.scrollIntoView({behavior: 'smooth', block: 'center'});
        done.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        return true;
    }
    return false;
    """
    result = driver.execute_script(js_done_script)
    if result:
        logger.info("[Agent] ✓ Done button clicked via JavaScript")
    else:
        logger.warning("[Agent] ⚠ Done button not found — may not be required on this flow")
        # Non-fatal: some Google Flights flows don't show Done (one-way, direct booking)


# ── Outbound flight selection ─────────────────────────────────────────────────

def step_select_outbound_flight(
    driver: Any, payload: Dict[str, Any], session_id: str, flight_id: str
) -> str:
    """
    Correct 3-action flow (confirmed from debug HTML analysis):
    Action 1: Click pIav2d li row  (entire flight row)
    Action 2: JS-click 'Select flight' button (aria-label='Select flight')
    Action 3: JS-click 'Done' button (jsname='McfNlf' OR aria-label='Done')
    """
    write_status(session_id, flight_id, "selecting_best_option",
                 "Selecting cheapest outbound flight...")
    save_debug_info(driver, "outbound_before_click", session_id)

    # ── ACTION 1: Click the first pIav2d li (entire flight row) ──────────────
    logger.info("[Agent] Clicking first outbound flight row (pIav2d li)...")

    row_clicked = _click_first_flight_row(driver, session_id, "outbound")

    if not row_clicked:
        save_debug_info(driver, "outbound_row_failed", session_id)
        raise Exception(
            "Could not click outbound flight row. "
            "Check debug_html/outbound_before_click*.html — "
            "look for li.pIav2d or the first li in the flight list."
        )

    save_debug_info(driver, "outbound_after_row_click", session_id)
    time.sleep(3)  # Wait for row expansion animation

    # ── ACTION 2: JS-click 'Select flight' button ─────────────────────────────
    write_status(session_id, flight_id, "selecting_best_option",
                 "Clicking Select flight for outbound...")
    logger.info("[Agent] JS-clicking Select flight button...")

    _js_click_select_flight(driver)
    save_debug_info(driver, "outbound_select_flight_clicked", session_id)
    time.sleep(2)

    # ── ACTION 3: JS-click 'Done' button ─────────────────────────────────────
    write_status(session_id, flight_id, "selecting_best_option",
                 "Confirming outbound selection...")
    logger.info("[Agent] JS-clicking Done button...")

    _js_click_done(driver)
    save_debug_info(driver, "outbound_done_clicked", session_id)
    time.sleep(3)  # Wait for next screen to load (return flights OR booking options)

    write_status(session_id, flight_id, "selecting_best_option",
                 "Outbound confirmed. Loading next screen...")

    if is_on_booking_options_page(driver):
        logger.info("[Agent] Jumped directly to booking options after outbound.")
        return "booking_options"
    return "return_selection"


# ── Return flight selection ───────────────────────────────────────────────────

def step_select_return_flight(
    driver: Any, payload: Dict[str, Any], session_id: str, flight_id: str
) -> str:
    """
    Same 3-action flow for return flight.
    Action 1: Click first pIav2d li in return flight list
    Action 2: JS-click 'Select flight'
    Action 3: JS-click 'Done'
    Then booking options page appears.
    """
    write_status(session_id, flight_id, "selecting_best_option",
                 "Waiting for return flights...")
    save_debug_info(driver, "return_screen_start", session_id)

    # Wait for return flight list to be ready
    RETURN_SIGNALS = [
        (By.XPATH, "//div[contains(., 'Top returning')]"),
        (By.XPATH, "//span[contains(., 'returning')]"),
        (By.XPATH, "(//li[contains(@class,'pIav2d')])[1]"),
        (By.XPATH, "(//div[@role='main']//ul/li)[1]"),
    ]
    page_ready = wait_for_any(driver, RETURN_SIGNALS, timeout=20)
    if not page_ready:
        if is_on_booking_options_page(driver):
            write_status(session_id, flight_id, "selecting_best_option",
                         "Skipped to booking options.")
            return "booking_options"
        logger.warning("[Agent] Return page signals not detected — attempting anyway.")

    time.sleep(2)
    save_debug_info(driver, "return_results_loaded", session_id)

    # ── ACTION 1: Click first return flight row ───────────────────────────────
    write_status(session_id, flight_id, "selecting_best_option",
                 "Selecting cheapest return flight...")
    logger.info("[Agent] Clicking first return flight row (pIav2d li)...")

    row_clicked = _click_first_flight_row(driver, session_id, "return")

    if not row_clicked:
        save_debug_info(driver, "return_row_failed", session_id)
        raise Exception(
            "Could not click return flight row. "
            "Check debug_html/return_results_loaded*.html"
        )

    save_debug_info(driver, "return_after_row_click", session_id)
    time.sleep(3)

    # ── ACTION 2: JS-click 'Select flight' ────────────────────────────────────
    write_status(session_id, flight_id, "selecting_best_option",
                 "Clicking Select flight for return...")
    logger.info("[Agent] JS-clicking Select flight button...")

    _js_click_select_flight(driver)
    save_debug_info(driver, "return_select_flight_clicked", session_id)
    time.sleep(2)

    # ── ACTION 3: JS-click 'Done' ─────────────────────────────────────────────
    write_status(session_id, flight_id, "selecting_best_option",
                 "Confirming return selection...")
    logger.info("[Agent] JS-clicking Done button...")

    _js_click_done(driver)
    save_debug_info(driver, "return_done_clicked", session_id)
    time.sleep(3)

    write_status(session_id, flight_id, "selecting_best_option",
                 "Return confirmed. Loading booking options...")
    return "continue"


# ── STEP 5: Click first Continue on Booking Options page ─────────────────────

def step_click_first_booking_option(
    driver: Any, session_id: str, flight_id: str
) -> None:
    """
    Wait for Booking Options page, then JS-click the FIRST Continue button.
    Continue button is next to the first booking provider (e.g. Air Arabia).
    """
    write_status(session_id, flight_id, "proceeding_to_booking",
                 "Waiting for booking options...")
    save_debug_info(driver, "booking_options_page", session_id)

    # Wait for booking options page to load
    BOOKING_SIGNALS = [
        (By.XPATH, "//div[contains(., 'Booking options')]"),
        (By.XPATH, "//div[contains(., 'Book with')]"),
        (By.XPATH, "//div[contains(., 'Selected flights')]"),
        (By.XPATH, "//button[normalize-space(.)='Continue']"),
        (By.XPATH, "//a[normalize-space(.)='Continue']"),
    ]
    page_found = wait_for_any(driver, BOOKING_SIGNALS, timeout=25)

    if not page_found:
        save_debug_info(driver, "booking_options_not_found", session_id)
        raise Exception(
            "Booking options page did not load after both flights selected. "
            "Check debug_html/return_done_clicked*.html to see current page state."
        )

    time.sleep(2)
    save_debug_info(driver, "booking_options_ready", session_id)
    write_status(session_id, flight_id, "proceeding_to_booking",
                 "Clicking first booking option...")

    # JS-click the first Continue button
    js_continue_script = """
    var clicked = false;

    // Strategy 1: exact text 'Continue' in button
    var buttons = document.querySelectorAll("button, a");
    for (var el of buttons) {
        if (el.textContent.trim() === 'Continue') {
            el.scrollIntoView({behavior: 'smooth', block: 'center'});
            el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            clicked = true;
            break;
        }
    }

    // Strategy 2: any element containing only 'Continue' text
    if (!clicked) {
        var all = document.querySelectorAll("*");
        for (var el of all) {
            if (el.children.length === 0 && el.textContent.trim() === 'Continue') {
                var btn = el.closest('button') || el.closest('a') || el;
                btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                clicked = true;
                break;
            }
        }
    }

    return clicked;
    """

    result = driver.execute_script(js_continue_script)
    if result:
        logger.info("[Agent] ✓ First Continue button clicked via JavaScript")
    else:
        save_debug_info(driver, "continue_button_not_found", session_id)
        raise Exception(
            "Could not click Continue button on booking options page. "
            "Check debug_html/booking_options_ready*.html — "
            "look for the 'Continue' button HTML and update the JS selector."
        )

    save_debug_info(driver, "after_continue_click", session_id)
    write_status(session_id, flight_id, "proceeding_to_booking",
                 "Redirecting to booking site...")
    time.sleep(5)  # Wait for redirect to airline/OTA website


# ── STEP 6: Confirm arrival at airline website ───────────────────────────────

def step_confirm_airline_website(
    driver: Any, session_id: str, flight_id: str
) -> None:
    """
    IMAGE 7:
    Confirm Chrome landed on airline / OTA website.
    Agent's automated work is done — browser stays open for the user.
    """
    save_debug_info(driver, "final_booking_site", session_id)
    current_url = driver.current_url

    if is_on_airline_website(driver):
        write_status(
            session_id, flight_id, "booking_page_open",
            "Booking website is ready! Complete your booking in Chrome.",
            booking_url=current_url,
        )
        logger.info(f"[Agent] ✅ Successfully reached booking website: {current_url[:80]}")
    else:
        write_status(
            session_id, flight_id, "booking_page_open",
            "Booking page is open. Check your Chrome window.",
            booking_url=current_url,
        )
        logger.warning(f"[Agent] ⚠ Unexpected URL after Continue: {current_url[:80]}")
        save_debug_info(driver, "unexpected_url_after_continue", session_id)


# ── Keep-alive ───────────────────────────────────────────────────────────────

def keep_browser_alive(driver: Any, session_id: str, flight_id: str) -> None:
    """Keep the thread alive (up to 30 min) so Chrome stays open for the user."""
    max_wait_seconds = 1800
    poll_interval    = 10
    elapsed          = 0
    while elapsed < max_wait_seconds:
        try:
            _ = driver.current_url
            time.sleep(poll_interval)
            elapsed += poll_interval
        except Exception:
            logger.info("[Agent] Chrome was closed by user. Agent complete.")
            break
    logger.info("[Agent] Agent session ended.")


# ── Master flow controller ─────────────────────────────────────────────────

def run_full_booking_flow(driver: Any, payload: Dict[str, Any], session_id: str) -> None:
    """
    Master controller — executes the exact 6-step Google Flights flow.

    Phase 1 → Open Google Flights
    Phase 2 → Handle overlays
    Phase 3 → Wait for results
    Phase 4 → Select outbound (chevron → 'Select flight')
    Phase 5 → Select return   (chevron → 'Select flight')   [round-trip only]
    Phase 6 → Click first Continue on Booking Options page
    Phase 7 → Confirm airline website reached
    Phase 8 → Keep browser open for user
    """
    flight_id = payload.get("flight_id", "leg_1")
    is_round_trip = (
        payload.get("trip_type") == "round_trip"
        and payload.get("return_date") is not None
    )

    try:
        # ── Phase 1-2: Open & handle overlays ─────────────────────────
        step_open_google_flights(driver, payload, session_id, flight_id)
        # NOTE: dismiss_consent_banner is already called inside step_open_google_flights
        # Do NOT call it again here

        # ── Phase 3: Wait for results ──────────────────────────────────
        step_wait_for_results(driver, session_id, flight_id)

        # Write CORRECT status keys (matching FlightBookingStatus type):
        write_status(
            session_id, flight_id, "filling_cities",
            f"Route: {payload.get('origin',{}).get('iata','?')} → "
            f"{payload.get('destination',{}).get('iata','?')}"
        )
        write_status(
            session_id, flight_id, "selecting_date",
            f"Dates: {payload.get('travel_date','')}"
            + (f" → {payload.get('return_date','')}" if is_round_trip else "")
        )

        # ── Phase 4: Select outbound (chevron → Select flight) ─────────
        outbound_result = step_select_outbound_flight(driver, payload, session_id, flight_id)

        # ── Phase 5: Select return (chevron → Select flight) ───────────
        if outbound_result != "booking_options" and is_round_trip:
            time.sleep(2)
            return_result = step_select_return_flight(driver, payload, session_id, flight_id)
            # If return step already landed on booking options, skip Phase 6 wait
            if return_result == "booking_options":
                pass  # fall through to Phase 6 which detects it

        # ── Phase 6: Click first Continue on Booking Options ───────────
        time.sleep(2)
        step_click_first_booking_option(driver, session_id, flight_id)

        # ── Phase 7: Confirm airline website ───────────────────────────
        time.sleep(3)
        step_confirm_airline_website(driver, session_id, flight_id)

        # ── Phase 8: Stay alive while user completes booking ───────────
        keep_browser_alive(driver, session_id, flight_id)

    except Exception as e:
        logger.error(f"Error in booking flow: {e}")
        save_debug_info(driver, "unexpected_error", session_id)
        os.makedirs("./logs", exist_ok=True)
        with open(f"./logs/{session_id}_{flight_id}_error.log", "w") as f:
            traceback.print_exc(file=f)
        raise


def flight_agent_thread(payload: Dict[str, Any]) -> None:
    session_id  = payload.get("session_id", "unknown")
    flight_id   = payload.get("flight_id", "leg_1")
    travel_date = payload.get("travel_date", "")

    if not travel_date:
        write_status(session_id, flight_id, "error", "Travel date is missing.")
        return

    driver = None
    timeout_timer: Optional[threading.Timer] = None

    def _handle_timeout() -> None:
        write_status(session_id, flight_id, "error", "Agent timed out — please use the manual Google Flights link.")
        try:
            if driver:
                take_debug_screenshot(driver, "timeout", session_id)
                driver.quit()
        except:
            pass

    try:
        if not SELENIUM_AVAILABLE:
            raise ImportError("selenium is not installed. Run: pip install selenium")

        write_status(session_id, flight_id, "opening_browser", "Launching Chrome...")
        driver = create_driver()

        timeout_timer = threading.Timer(AGENT_TIMEOUT_SECONDS, _handle_timeout)
        timeout_timer.daemon = True
        timeout_timer.start()

        run_full_booking_flow(driver, payload, session_id)

    except Exception as exc:
        error_msg = format_selenium_error(exc)
        logger.error(f"[{session_id}/{flight_id}] Error: {error_msg}")
        if driver:
            take_debug_screenshot(driver, "error_exception", session_id)
        
        os.makedirs("./logs", exist_ok=True)
        with open(f"./logs/{session_id}_{flight_id}_error.log", "w") as f:
            traceback.print_exc(file=f)

        write_status(
            session_id, flight_id, "error",
            error_msg,
            error_detail=safe_error_message(exc),
        )
    finally:
        if timeout_timer:
            timeout_timer.cancel()
        
        if driver:
            current_status = read_status(session_id, flight_id)
            if current_status and current_status.get("status") == "error":
                time.sleep(5)
                try:
                    driver.quit()
                except:
                    pass
            # Success paths intentionally don't quit driver


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "10.0.0",
        "selenium_available": SELENIUM_AVAILABLE,
        "active_sessions": len(_status_store),
    }


@app.post("/trigger-flight")
async def trigger_flight(request_data: dict):
    session_id  = request_data.get("session_id", "")
    flight_id   = request_data.get("flight_id", "leg_1")
    travel_date = request_data.get("travel_date", "")

    if not session_id:
        return JSONResponse(status_code=400, content={"error": "session_id is required"})

    if not travel_date:
        return JSONResponse(status_code=400, content={"error": "travel_date is required."})

    existing = read_status(session_id, flight_id)
    if existing and existing.get("status") not in (None, "error", "booking_page_open"):
        return {"status": "already_running", "message": f"Agent already active for {session_id}/{flight_id}"}

    write_status(session_id, flight_id, "initializing", "Agent starting...")

    thread = threading.Thread(
        target=flight_agent_thread,
        args=(request_data,),
        daemon=True,
        name=f"flight-agent-{session_id[:8]}-{flight_id}",
    )
    thread.start()

    logger.info(f"Triggered flight agent thread for {session_id}/{flight_id} | date={travel_date}")
    return {"status": "agent_started", "session_id": session_id, "flight_id": flight_id}


@app.get("/flight-status/{session_id}/{flight_id}")
async def get_flight_status(session_id: str, flight_id: str):
    entry = read_status(session_id, flight_id)
    if not entry:
        return JSONResponse(
            status_code=404,
            content={
                "status":       "initializing",
                "message":      "Agent is starting up...",
                "error_detail": None,
                "timestamp":    time.time()
            },
        )
    return {
        "status":       entry.get("status", "error"),
        "message":      entry.get("message") or "No message available",
        "error_detail": entry.get("error_detail", None),
        "timestamp":    entry.get("timestamp", time.time()),
        "booking_url":  entry.get("booking_url", None)
    }


@app.delete("/flight-status/{session_id}/{flight_id}")
async def clear_flight_status(session_id: str, flight_id: str):
    with _status_lock:
        if session_id in _status_store:
            _status_store[session_id].pop(flight_id, None)
    return {"cleared": True}


if __name__ == "__main__":
    uvicorn.run("flight_agent_server:app", host="0.0.0.0", port=8001, reload=False, log_level="info")
