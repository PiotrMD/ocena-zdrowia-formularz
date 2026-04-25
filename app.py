import json
import os
import re
import smtplib
import tempfile
import uuid
from datetime import date, datetime
from email.message import EmailMessage
from typing import Any, Dict, List, Optional

import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# KONFIGURACJA STRONY
# =========================================================
st.set_page_config(
    page_title="Ocena stanu zdrowia – wywiad lekarski",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =========================================================
# CSS — Premium Design
# =========================================================
st.markdown(
    """
    <style>
    /* ── Ukryj chrome Streamlita ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {display: none !important;}

    /* ── Layout ── */
    html, body, .stApp {
        background-color: #f4f6fb !important;
    }
    .main .block-container {
        max-width: 860px;
        padding-top: 1.6rem;
        padding-bottom: 3rem;
    }

    /* ── Globalna czcionka ── */
    html, body, [class*="css"], p, label, span, div,
    input, textarea, select, button {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
    }

    /* ── HEADER CARD ── */
    .header-card {
        background: linear-gradient(145deg, #132743 0%, #1a3a5c 60%, #1e4876 100%);
        padding: 36px 44px 28px;
        border-radius: 22px;
        margin-bottom: 20px;
        text-align: center;
        color: white;
        box-shadow: 0 12px 40px rgba(19, 39, 67, 0.28), 0 2px 8px rgba(19, 39, 67, 0.12);
        position: relative;
        overflow: hidden;
    }
    .header-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, transparent 5%, #c9a84c 30%, #e8c96b 50%, #c9a84c 70%, transparent 95%);
    }
    .header-card::after {
        content: '';
        position: absolute;
        bottom: -40px; right: -40px;
        width: 180px; height: 180px;
        border-radius: 50%;
        background: rgba(201, 168, 76, 0.06);
        pointer-events: none;
    }
    .header-title {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        margin: 0 0 4px 0;
        color: #ffffff;
        text-transform: uppercase;
    }
    .header-subtitle {
        font-size: 1rem;
        font-weight: 400;
        letter-spacing: 0.08em;
        margin: 0 0 18px 0;
        color: rgba(255,255,255,0.72);
        text-transform: uppercase;
    }
    .header-divider {
        border: none;
        border-top: 1px solid rgba(201, 168, 76, 0.35);
        margin: 0 40px 14px;
    }
    .header-doctor {
        font-size: 1.05rem;
        color: rgba(255,255,255,0.88);
        font-weight: 500;
        margin: 0 0 3px 0;
        letter-spacing: 0.02em;
    }
    .header-site {
        font-size: 0.95rem;
        font-weight: 700;
        color: #c9a84c;
        letter-spacing: 0.06em;
        margin: 0 0 8px 0;
    }
    .header-contact {
        font-size: 0.83rem;
        color: rgba(255,255,255,0.52);
        margin: 0;
        letter-spacing: 0.01em;
    }

    /* ── WELCOME CARD ── */
    .welcome-card {
        background: #ffffff;
        padding: 28px 32px;
        border-radius: 18px;
        border: 1px solid rgba(19, 39, 67, 0.07);
        margin-bottom: 20px;
        box-shadow: 0 2px 14px rgba(19, 39, 67, 0.06);
        line-height: 1.8;
        color: #2c3e50;
        font-size: 0.97rem;
    }
    .welcome-privacy {
        margin-top: 18px;
        padding-top: 16px;
        border-top: 1px solid rgba(19, 39, 67, 0.07);
        font-size: 0.83rem;
        color: #8093a8;
        line-height: 1.65;
    }

    /* ── PROGRESS BOX ── */
    .progress-box {
        background: #ffffff;
        padding: 14px 20px 12px;
        border-radius: 14px;
        border: 1px solid rgba(19, 39, 67, 0.08);
        margin-bottom: 10px;
        box-shadow: 0 1px 6px rgba(19, 39, 67, 0.04);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .progress-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #8093a8;
    }
    .progress-step-name {
        font-size: 0.97rem;
        font-weight: 700;
        color: #132743;
        margin-top: 1px;
    }
    .progress-pct {
        font-size: 1.5rem;
        font-weight: 800;
        color: #c9a84c;
        letter-spacing: -0.02em;
        line-height: 1;
    }

    /* Streamlit progress bar override */
    [data-testid="stProgress"] {
        margin-top: 6px !important;
        margin-bottom: 18px !important;
    }
    [data-testid="stProgress"] > div {
        background-color: rgba(19, 39, 67, 0.07) !important;
        border-radius: 99px !important;
        height: 5px !important;
    }
    [data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, #1a3a5c 0%, #c9a84c 100%) !important;
        border-radius: 99px !important;
        transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    /* ── FORM CARD (st.form wrapper) ── */
    [data-testid="stForm"] {
        background: #ffffff !important;
        border-radius: 18px !important;
        border: 1px solid rgba(19, 39, 67, 0.08) !important;
        box-shadow: 0 2px 14px rgba(19, 39, 67, 0.05) !important;
        padding: 4px 8px 8px !important;
    }

    /* ── SECTION SUBHEADERS ── */
    h2[data-testid="stHeading"], h3[data-testid="stHeading"] {
        color: #132743 !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        letter-spacing: 0.01em !important;
        padding-bottom: 10px !important;
        border-bottom: 2px solid rgba(201, 168, 76, 0.3) !important;
        margin-bottom: 16px !important;
    }

    /* ── INPUTS & TEXTAREAS ── */
    [data-baseweb="input"],
    [data-baseweb="input"] > div,
    [data-baseweb="textarea"],
    [data-baseweb="textarea"] > div {
        border-radius: 10px !important;
        border: 1.5px solid rgba(19, 39, 67, 0.14) !important;
        background: #f7f9fc !important;
        box-shadow: none !important;
        transition: border-color 0.2s, box-shadow 0.2s, background 0.2s !important;
        min-height: 46px !important;
    }
    [data-baseweb="input"]:hover,
    [data-baseweb="input"] > div:hover,
    [data-baseweb="textarea"]:hover,
    [data-baseweb="textarea"] > div:hover {
        border-color: rgba(19, 39, 67, 0.32) !important;
        background: #f0f4fa !important;
    }
    [data-baseweb="input"]:focus-within,
    [data-baseweb="input"] > div:focus-within,
    [data-baseweb="textarea"]:focus-within,
    [data-baseweb="textarea"] > div:focus-within {
        border-color: #1a3a5c !important;
        box-shadow: 0 0 0 3px rgba(26, 58, 92, 0.12) !important;
        background: #ffffff !important;
    }
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        background: transparent !important;
        color: #132743 !important;
        font-weight: 400 !important;
        font-size: 0.97rem !important;
        padding: 4px 8px !important;
    }
    [data-baseweb="input"] input::placeholder,
    [data-baseweb="textarea"] textarea::placeholder {
        color: #a8b4c2 !important;
        font-weight: 300 !important;
        font-style: italic !important;
    }

    /* ── SELECT / COMBOBOX ── */
    [data-baseweb="select"] > div {
        border-radius: 10px !important;
        border: 1.5px solid rgba(19, 39, 67, 0.14) !important;
        background: #f7f9fc !important;
        box-shadow: none !important;
        min-height: 46px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    [data-baseweb="select"] > div:hover {
        border-color: rgba(19, 39, 67, 0.32) !important;
        background: #f0f4fa !important;
    }
    [data-baseweb="select"] > div:focus-within {
        border-color: #1a3a5c !important;
        box-shadow: 0 0 0 3px rgba(26, 58, 92, 0.12) !important;
        background: #ffffff !important;
    }

    /* Multiselect tags */
    [data-baseweb="tag"] {
        background: rgba(26, 58, 92, 0.1) !important;
        border-color: rgba(26, 58, 92, 0.2) !important;
        border-radius: 6px !important;
        color: #132743 !important;
    }

    /* ── SLIDER ── */
    [data-testid="stSlider"] [role="slider"] {
        background-color: #1a3a5c !important;
        border: 3px solid #ffffff !important;
        box-shadow: 0 0 0 2px #1a3a5c, 0 2px 6px rgba(26,58,92,0.3) !important;
    }
    [data-testid="stSlider"] [data-testid="stTickBar"] {
        color: #8093a8 !important;
    }
    /* filled track */
    [data-testid="stSlider"] > div > div > div:nth-child(2) {
        background: linear-gradient(90deg, #1a3a5c, #2e6da4) !important;
    }

    /* ── BUTTONS ── */

    /* Dalej → (form submit) */
    [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #1a3a5c 0%, #1d4a74 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.97rem !important;
        height: 52px !important;
        letter-spacing: 0.03em !important;
        box-shadow: 0 4px 16px rgba(26, 58, 92, 0.28) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(135deg, #1d4a74 0%, #245d8f 100%) !important;
        box-shadow: 0 6px 22px rgba(26, 58, 92, 0.38) !important;
        transform: translateY(-1px) !important;
    }

    /* Wstecz (secondary buttons) */
    button[data-testid="stBaseButton-secondary"] {
        border-radius: 12px !important;
        font-weight: 600 !important;
        height: 48px !important;
        border-color: rgba(19, 39, 67, 0.2) !important;
        color: #132743 !important;
        background: #ffffff !important;
        transition: all 0.18s ease !important;
    }
    button[data-testid="stBaseButton-secondary"]:hover {
        border-color: #1a3a5c !important;
        background: rgba(26, 58, 92, 0.04) !important;
    }

    /* Wyślij button */
    .send-button > button {
        width: 100%;
        height: 3.5rem;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        border-radius: 14px !important;
        background: linear-gradient(135deg, #1a3a5c 0%, #c9a84c 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 6px 22px rgba(26, 58, 92, 0.3) !important;
        letter-spacing: 0.04em !important;
        transition: all 0.2s ease !important;
    }
    .send-button > button:hover {
        box-shadow: 0 8px 28px rgba(26, 58, 92, 0.42) !important;
        transform: translateY(-1px) !important;
    }

    /* ── CHECKBOXES & RADIO ── */
    [data-testid="stCheckbox"] label,
    [data-testid="stRadio"] label {
        font-weight: 500 !important;
        color: #2c3e50 !important;
    }
    [data-baseweb="checkbox"] span:first-child {
        border-radius: 5px !important;
        border-color: rgba(19, 39, 67, 0.3) !important;
    }

    /* ── WIDGET LABELS ── */
    [data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] {
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        color: #5a6b7e !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        margin-bottom: 4px !important;
    }

    /* ── HR DIVIDER ── */
    hr {
        border: none !important;
        border-top: 1px solid rgba(19, 39, 67, 0.08) !important;
        margin: 1.25rem 0 !important;
    }

    /* ── NAV TOGGLE BUTTON ── */
    div[data-testid="stButton"]:has(button[data-testid="stBaseButton-secondary"]#_nav_toggle_button),
    [data-testid="stBaseButton-secondary"][key="_nav_toggle"] button {
        text-align: left !important;
    }

    /* ── PRIMARY BUTTONS (Dalej, nav kroków, aktywny język, Wyślij) ── */
    button[data-testid="stBaseButton-primary"],
    [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #1a3a5c 0%, #1d4a74 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        box-shadow: 0 2px 8px rgba(26, 58, 92, 0.2) !important;
        transition: all 0.18s ease !important;
    }
    button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(135deg, #1d4a74 0%, #245d8f 100%) !important;
        box-shadow: 0 4px 14px rgba(26, 58, 92, 0.3) !important;
        transform: translateY(-1px) !important;
    }

    /* ── ERROR BOX ── */
    .field-error-box {
        border: 1.5px solid #c0392b;
        border-left: 4px solid #c0392b;
        border-radius: 10px;
        padding: 10px 14px;
        color: #c0392b;
        background: rgba(192, 57, 43, 0.05);
        font-weight: 600;
        font-size: 0.9rem;
        margin-top: -0.1rem;
        margin-bottom: 0.85rem;
    }
    .field-anchor {
        position: relative;
        top: -95px;
        visibility: hidden;
    }

    /* ── VIDEO EMBED ── */
    .video-wrapper {
        position: relative;
        padding-bottom: 56.25%;
        height: 0;
        overflow: hidden;
        border-radius: 16px;
        box-shadow: 0 8px 30px rgba(19, 39, 67, 0.18);
        margin: 18px 0;
    }
    .video-wrapper iframe {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        border: 0;
    }

    /* ── HELP TEXT ── */
    [data-testid="stHelp"] {
        color: #8093a8 !important;
        font-size: 0.82rem !important;
    }

    /* ── SUCCESS PAGE ── */
    .success-card {
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        border: 1.5px solid rgba(34, 139, 69, 0.3);
        border-radius: 22px;
        padding: 48px 40px;
        text-align: center;
        box-shadow: 0 8px 30px rgba(34, 139, 69, 0.1);
        margin: 24px 0;
    }
    .success-icon {
        font-size: 3.5rem;
        margin-bottom: 16px;
        display: block;
    }
    .success-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #166534;
        margin-bottom: 14px;
    }
    .success-body {
        font-size: 1rem;
        color: #374151;
        line-height: 1.75;
    }

    /* ── RESPONSIVE — Mobile ── */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 0.5rem !important;
            padding-left: 0.75rem;
            padding-right: 0.75rem;
            padding-bottom: 3.5rem;
        }
        section[data-testid="stMain"] > div:first-child {
            padding-top: 0 !important;
        }
        div[data-testid="stRadio"],
        div[data-testid="stRadio"] > div,
        div[data-testid="stRadio"] > div > div {
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
        }
        .header-card { padding: 22px 20px 18px; border-radius: 16px; }
        .header-title { font-size: 1.5rem; letter-spacing: 0.08em; }
        .header-subtitle { font-size: 0.85rem; }
        .header-divider { margin: 0 16px 10px; }
        .header-doctor, .header-site { font-size: 0.9rem; }
        .header-contact { font-size: 0.78rem; }
        .welcome-card { padding: 18px 18px; font-size: 0.92rem; }
        .progress-box { flex-direction: column; align-items: flex-start; gap: 4px; }
        .progress-pct { font-size: 1.25rem; }
        /* Anty-zoom iOS */
        input[type="text"], input[type="email"], input[type="tel"],
        input[type="number"], textarea, select,
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea,
        [data-baseweb="select"] input {
            font-size: 16px !important;
            min-height: 46px;
        }
        [data-testid="stFormSubmitButton"] button,
        button[data-testid="stBaseButton-primary"] {
            min-height: 52px !important;
            font-size: 1rem !important;
        }
        button[data-testid="stBaseButton-secondary"] {
            min-height: 48px !important;
        }
        label, [data-testid="stWidgetLabel"] { font-size: 0.95rem !important; }
        [data-testid="stSlider"] { padding-top: 8px; padding-bottom: 8px; }
        [data-testid="stCheckbox"] label,
        [data-testid="stRadio"] label { font-size: 0.97rem !important; padding: 5px 0; }
        h2[data-testid="stHeading"], h3[data-testid="stHeading"] { font-size: 1rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Natychmiastowy feedback przy kliknięciu przycisków nawigacji
components.html(
    """
    <script>
    (function () {
        var NAV_WORDS = ['Dalej', 'Next', 'Wstecz', 'Back', 'Wyślij', 'Submit'];
        function isNav(btn) {
            var txt = (btn.textContent || '').trim();
            return NAV_WORDS.some(function (w) { return txt.indexOf(w) !== -1; });
        }
        function styleLangBtns() {
            try {
                window.parent.document.querySelectorAll('button').forEach(function (btn) {
                    var txt = (btn.textContent || '').trim();
                    if (txt === 'PL' || txt === 'EN') {
                        btn.style.setProperty('border-radius', '18px', 'important');
                        btn.style.setProperty('font-size', '0.8rem', 'important');
                        btn.style.setProperty('letter-spacing', '0.1em', 'important');
                        btn.style.setProperty('font-weight', '700', 'important');
                        btn.style.setProperty('white-space', 'nowrap', 'important');
                        btn.style.setProperty('overflow', 'hidden', 'important');
                        btn.style.setProperty('text-overflow', 'ellipsis', 'important');
                    }
                });
            } catch (e) {}
        }
        function attach() {
            styleLangBtns();
            try {
                window.parent.document.querySelectorAll('button').forEach(function (btn) {
                    if (btn._navBusy) return;
                    if (!isNav(btn)) return;
                    btn._navBusy = true;
                    btn.addEventListener('click', function () {
                        var el = this;
                        var txt = (el.textContent || '').trim();
                        el.style.opacity = '0.6';
                        el.style.pointerEvents = 'none';
                        if (txt.indexOf('Wyślij') !== -1 || txt.indexOf('Submit') !== -1) {
                            el.innerHTML = '&#9203; Wysyłanie…';
                            setTimeout(function() { el.disabled = true; }, 300);
                        }
                    });
                });
            } catch (e) {}
        }
        attach();
        try {
            new window.parent.MutationObserver(attach).observe(
                window.parent.document.body,
                { childList: true, subtree: true }
            );
        } catch (e) {}
    })();
    </script>
    """,
    height=0,
    scrolling=False,
)

# =========================================================
# TRANSLATIONS
# =========================================================
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "pl": {
        "header_title": "OCENA STANU ZDROWIA",
        "header_subtitle": "Wywiad lekarski",
        "header_contact": "Recepcja: +48 690 584 584 &nbsp;·&nbsp; English-speaking patients: +48 609 857 377",
        "welcome_text": (
            "Szanowni Państwo,<br><br>"
            "każda wizyta jest przygotowywana indywidualnie.<br>"
            "Bardzo proszę o szczere i możliwie dokładne odpowiedzi dotyczące stanu zdrowia.<br>"
            "Im więcej szczegółów, tym większa szansa na wcześniejsze wykrycie problemów i trafną ocenę sytuacji zdrowotnej.<br><br>"
            "W przypadku dzieci proszę o wypełnienie odpowiednich pól.<br><br>"
            "Serdecznie pozdrawiam i do zobaczenia na wizycie."
        ),
        "welcome_privacy": (
            "Formularz ma charakter informacyjny i służy przygotowaniu wizyty lekarskiej. "
            "Dane nie są przechowywane w bazie aplikacji. "
            "Po wysłaniu przekazywane są wyłącznie lekarzowi w formie wiadomości e-mail i dokumentu PDF."
        ),
        "send_btn": "✉ Wyślij formularz do lekarza",
        "sending": "Wysyłanie formularza…",
        "form_sent": "Formularz został wysłany. Dziękujemy.",
        "consent_true": "Oświadczam, że podane informacje są prawdziwe.",
        "consent_visit": "Wyrażam zgodę na wykorzystanie tych informacji wyłącznie przez lekarza do przygotowania wizyty.",
        "consent_privacy": "Przyjmuję do wiadomości, że formularz nie zapisuje danych w bazie aplikacji, a dokument wysyłany do lekarza zawiera ograniczone dane identyfikacyjne.",
        "contact_consent": "Wyrażam zgodę na kontakt telefoniczny lub mailowy w sprawach organizacyjnych związanych z wizytą.",
        "err_consent": "Zaznacz wszystkie wymagane zgody.",
        # ogólne
        "placeholder": "wybierz",
        # sekcja 1
        "sec_1": "1. Dane podstawowe",
        "visit_type_lbl": "Rodzaj wizyty",
        "first_name_lbl": "Imię",
        "last_name_lbl": "Nazwisko",
        "phone_lbl": "Telefon kontaktowy",
        "phone_help": "Może być z numerem kierunkowym albo bez, np. 690584584 lub +48690584584",
        "email_lbl": "Adres e-mail",
        "birth_date_lbl": "Data urodzenia",
        "nationality_lbl": "Narodowość",
        "sex_lbl": "Płeć",
        "sex_other_lbl": "Inna płeć — opisz",
        "current_status_lbl": "Aktualny status",
        "current_status_other_lbl": "Inny status — opisz",
        "profession_lbl": "Obecnie wykonywany zawód",
        # sekcja 2
        "sec_2": "2. Ocena ogólna",
        "physical_score_lbl": "Jak oceniasz swój stan fizyczny? 0 = bardzo zły, 10 = bardzo dobry",
        "mental_score_lbl": "Jak oceniasz swój stan psychiczny? 0 = bardzo zły, 10 = bardzo dobry",
        "weight_change_lbl": "Czy w ostatnim roku zmieniła się masa ciała?",
        "weight_change_grew_lbl": "O ile kg wzrosła masa ciała?",
        "weight_change_fell_lbl": "O ile kg spadła masa ciała?",
        "weight_kg_placeholder": "wpisz liczbę kg",
        # sekcja 4
        "sec_4": "4. Objawy główne",
        "symptom_lbl": "Objaw {n}",
        "symptom_since_lbl": "Od kiedy występuje objaw {n}?",
        "additional_symptoms_lbl": "Pozostałe dolegliwości, nawet mniej nasilone",
        # błędy walidacji
        "err_visit_type": "Wybierz rodzaj wizyty.",
        "err_first_name": "Wpisz imię.",
        "err_last_name": "Wpisz nazwisko.",
        "err_phone": "Wpisz poprawny numer telefonu. Może być z +48 albo bez.",
        "err_email": "Wpisz poprawny adres e-mail.",
        "err_birth_date": "Wybierz datę urodzenia.",
        # sekcja 3
        "sec_3": "3. Badania wykonane w ciągu ostatnich 2 lat",
        "tests_lbl": "Zaznacz wykonane badania",
        "tests_ph": "Wybierz badania",
        # sekcja 5
        "sec_5": "5. Charakter objawów",
        "symptom_pattern_lbl": "Czy objawy są stałe czy pojawiają się okresowo?",
        "symptom_periodicity_lbl": "Jeśli okresowe, napisz kiedy się pojawiają i jak często w ciągu roku",
        "symptom_past_lbl": "Czy podobne objawy występowały wcześniej? Jeśli tak, kiedy?",
        "worsening_factors_lbl": "Co powoduje pogorszenie objawów?",
        "worsening_factors_ph": "Wybierz czynniki pogorszenia",
        "worsening_other_lbl": "Inne czynniki pogorszenia — opisz jakie",
        "improvement_factors_lbl": "Co powoduje poprawę lub zmniejszenie objawów?",
        "improvement_factors_ph": "Wybierz czynniki poprawy",
        "improvement_other_lbl": "Inne czynniki poprawy — opisz jakie",
        # sekcja 6
        "sec_6": "6. Chronologia zdrowia i leki",
        "health_timeline_lbl": "Opisz przebieg zdrowia od pierwszych problemów zdrowotnych do dziś",
        "current_meds_lbl": "Jakie leki obecnie przyjmujesz? Podaj nazwę i dawkowanie. Najlepiej wpisuj każdy lek w osobnej linii.",
        # sekcja 7
        "sec_7": "7. Tryb życia",
        "lifestyle_lbl": "Tryb życia",
        "lifestyle_other_lbl": "Inny tryb życia — opisz",
        "stimulants_lbl": "Używki i codzienne nawyki",
        "stimulants_ph": "Wybierz używki i nawyki",
        "stimulants_other_lbl": "Inne używki lub nawyki — opisz jakie",
        "sleep_hours_lbl": "Ile średnio trwa sen na dobę?",
        # sekcja 8
        "sec_8": "8. Podróże",
        "travel_abroad_lbl": "Czy w ciągu ostatnich 3 miesięcy był wyjazd za granicę?",
        "travel_where_lbl": "Jeśli tak, to gdzie?",
        # sekcja 9
        "sec_9": "9. Zwierzęta",
        "animal_contact_lbl": "Czy w ostatnich miesiącach było pogryzienie, zadrapanie lub bliski kontakt ze zwierzęciem?",
        "animal_details_lbl": "Jeśli tak, opisz kiedy i jakie zwierzę",
        # sekcja 10
        "sec_10": "10. Urazy",
        "injuries_lbl": "Czy były duże urazy ciała? Podaj rok i opisz, np. upadek z wysokości, uraz komunikacyjny, pobicie, tonięcie, operacja",
        # sekcja 11
        "sec_11": "11. COVID-19",
        "covid_lbl": "Czy i kiedy wystąpiło zachorowanie na COVID-19?",
        "covid_details_lbl": "Jeśli tak, opisz kiedy i jaki był przebieg",
        # sekcja 12
        "sec_12": "12. Stres",
        "stress_lbl": "Czy w ciągu życia były silne reakcje stresowe lub trudne wydarzenia? Jeśli tak, opisz i podaj rok",
        # sekcja 13
        "sec_13": "13. Urodzenie i dzieciństwo",
        "birth_delivery_lbl": "Sposób porodu",
        "birth_delivery_other_lbl": "Inny sposób porodu — opisz",
        "birth_timing_lbl": "Czas porodu",
        "birth_timing_other_lbl": "Inny czas porodu — opisz",
        "green_water_lbl": "Czy były zielone wody płodowe?",
        "birth_info_other_lbl": "Inne informacje o urodzeniu",
        "breastfeeding_lbl": "Czy było karmienie mlekiem matki?",
        "childhood_diseases_lbl": "Poważne choroby w dzieciństwie",
        "childhood_diseases_ph": "Wybierz choroby dzieciństwa",
        "childhood_diseases_other_lbl": "Inne choroby dzieciństwa — opisz jakie",
        # sekcja 14
        "sec_14": "14. Objawy ogólne i neurologiczne",
        "fever_lbl": "Czy aktualnie występuje gorączka?",
        "if_yes_describe": "Jeśli tak, opisz dokładniej",
        "headache_lbl": "Czy występują bóle i zawroty głowy?",
        "headache_assoc_lbl": "Czy bólom głowy towarzyszą wymioty, omdlenia, zaburzenia widzenia, osłabienie, światłowstręt, niepamięć?",
        "hearing_vision_lbl": "Czy w ostatnich latach pogorszył się słuch lub wzrok?",
        "attacks_lbl": "Czy występują ataki lub nagłe epizody? Jeśli tak, opisz.",
        "sinus_lbl": "Czy występują problemy z zatokami?",
        "nose_lbl": "Czy są problemy z nosem, np. krwawienia, suchość, zapalenia, trudności w oddychaniu przez nos?",
        "allergies_lbl": "Czy występują alergie? Jeśli tak, na co, o jakiej porze roku i jak nasilone?",
        "herpes_lbl": "Czy pojawia się opryszczka? Jeśli tak, jak często?",
        "mouth_corners_lbl": "Czy występują zajady?",
        "fresh_food_lbl": "Czy po spożyciu świeżych warzyw i owoców pojawia się pieczenie lub zaczerwienienie wokół ust?",
        "epilepsy_lbl": "Czy kiedykolwiek rozpoznano padaczkę?",
        "smell_taste_lbl": "Czy są zaburzenia węchu lub smaku? Jeśli tak, od kiedy?",
        "colds_lbl": "Jak często zdarzają się przeziębienia w ciągu roku?",
        # sekcja 15
        "sec_15": "15. Układ oddechowy",
        "throat_lbl": "Czy rano występuje ból gardła?",
        "esophagus_lbl": "Czy pojawia się pieczenie w przełyku?",
        "asthma_lbl": "Czy kiedykolwiek rozpoznano astmę?",
        "pneumonia_lbl": "Czy kiedykolwiek było zapalenie płuc?",
        "pneumonia_details_lbl": "Jeśli tak, podaj daty i po której stronie płuc było zapalenie",
        "dyspnea_lbl": "Czy zdarza się duszność lub zadyszka? Jeśli tak, opisz w jakich sytuacjach.",
        "night_breath_lbl": "Czy dochodzi do wybudzania w nocy z powodu braku tchu?",
        "chest_heaviness_lbl": "Czy występuje ciężkość w klatce piersiowej? Jeśli tak, opisz nasilenie.",
        "breathing_type_lbl": "Czy są trudności z oddychaniem?",
        "wheezing_lbl": "Czy występuje świszczący oddech?",
        "wheezing_ph": "Wybierz okoliczności świszczącego oddechu",
        "cough_lbl": "Czy jest kaszel? Jeśli tak, od kiedy, czy jest suchy czy z wydzieliną, jakiego koloru?",
        # sekcja 16
        "sec_16": "16. Układ sercowo-naczyniowy",
        "chest_pain_lbl": "Czy występują bóle w klatce piersiowej? Czy są miejscowe czy rozległe? Czy promieniują?",
        "pressure_type_lbl": "Czy są problemy z ciśnieniem?",
        "current_bp_lbl": "Jakie jest aktualne ciśnienie tętnicze?",
        "current_hr_lbl": "Jakie jest aktualne tętno?",
        "pain_press_lbl": "Czy odczuwasz ból przy naciskaniu klatki piersiowej?",
        "pain_position_lbl": "Czy przy zmianie pozycji występują bóle w klatce piersiowej?",
        "palpitations_lbl": "Czy odczuwasz nierówne bicie serca? Jeśli tak, opisz porę dnia, okoliczności i częstość.",
        # sekcja 17
        "sec_17": "17. Przewód pokarmowy",
        "gi_problem_lbl": "Czy występują problemy z przewodem pokarmowym?",
        "gi_symptoms_lbl": "Zaznacz problemy",
        "gi_symptoms_ph": "Wybierz objawy przewodu pokarmowego",
        "worsening_foods_lbl": "Czy są potrawy, po których samopoczucie się pogarsza?",
        "gi_infections_lbl": "Czy kiedykolwiek było zakażenie bakteryjne lub wirusowe przewodu pokarmowego? Jeśli tak, kiedy i czy było badanie kontrolne z wynikiem ujemnym?",
        # sekcja 18
        "sec_18": "18. Układ moczowy",
        "urine_lbl": "Czy są problemy z oddawaniem moczu, np. pieczenie, trudności, inne?",
        "night_urination_lbl": "Ile razy w nocy wstajesz oddać mocz?",
        "fluids_lbl": "Ile litrów płynów wypijasz dziennie?",
        # sekcja 19
        "sec_19": "19. Stawy i mięśnie",
        "joints_lbl": "Czy występują bóle stawów? Jeśli tak, to których?",
        "stiffness_lbl": "Czy po wstaniu z łóżka występuje ból lub sztywność stawów?",
        # sekcja 20
        "sec_20": "20. Skóra",
        "skin_changes_lbl": "Czy są jakieś zmiany na skórze? Jeśli tak, opisz dokładnie. Kiedy pojawiły się pierwszy raz? Czy od tej pory jest poprawa lub pogorszenie?",
        "skin_itch_lbl": "Czy występuje swędzenie skóry? Jeśli tak, których partii ciała dotyczy?",
        "acne_lbl": "Czy występował lub występuje nasilony trądzik na twarzy lub plecach?",
        "acne_details_lbl": "Jeśli tak, możesz opisać dokładniej",
        "skin_sensation_lbl": "Czy są zaburzenia czucia skóry? Jeśli tak, opisz lokalizację i od kiedy.",
        "wound_healing_lbl": "Czy występują problemy z gojeniem się ran?",
        "wound_healing_details_lbl": "Jeśli tak, opisz problemy z gojeniem",
        # sekcja 21
        "sec_21": "21. Sen i psychika",
        "sleep_problem_lbl": "Czy są problemy ze snem?",
        "sleep_types_lbl": "Jakie problemy ze snem występują?",
        "sleep_types_ph": "Wybierz rodzaj problemów ze snem",
        "psych_contact_lbl": "Czy kiedykolwiek była porada psychologa lub psychiatry?",
        "psych_dx_lbl": "Czy kiedykolwiek rozpoznano chorobę psychiczną? Jeśli tak, napisz jaką.",
        # sekcja 22
        "sec_22": "22. Krążenie obwodowe",
        "edema_lbl": "Czy pojawiają się obrzęki na podudziach lub kostkach?",
        "edema_details_lbl": "Jeśli tak, napisz czy występują stale czy po staniu, siedzeniu lub w innych sytuacjach.",
        "calf_pain_lbl": "Czy występują bóle łydek podczas chodzenia? Jeśli tak, po jakim dystansie i po jakim czasie ustępują?",
        "cold_fingers_lbl": "Czy palce rąk lub nóg łatwo stają się zimne lub zmieniają kolor?",
        "tingling_lbl": "Czy występuje mrowienie lub drętwienie rąk lub nóg?",
        "varicose_lbl": "Czy są obecne żylaki?",
        # sekcja 23
        "sec_23": "23. Odbyt i okolice odbytu",
        "anal_problems_lbl": "Czy występują problemy ze śluzówką odbytu?",
        "anal_problems_ph": "Wybierz problemy w okolicy odbytu",
        "anal_other_lbl": "Inne problemy w okolicy odbytu — opisz jakie",
        # sekcja 24
        "sec_24": "24. Ginekologia lub andrologia",
        "gyn_problems_lbl": "Czy występują problemy ginekologiczne?",
        "menstruation_lbl": "Czy występuje nieregularna miesiączka, menopauza lub leczenie hormonalne? Jeśli tak, napisz od kiedy.",
        "first_menses_lbl": "Podaj miesiąc i rok pierwszej miesiączki",
        "last_menses_lbl": "Data ostatniej miesiączki",
        "last_menses_help": "Najlepiej w formacie DD.MM.RRRR",
        "potency_lbl": "Czy są problemy z potencją?",
        # sekcja 25
        "sec_25": "25. Wywiad rodzinny",
        "mother_lbl": "Na jakie choroby choruje lub chorowała mama?",
        "father_lbl": "Na jakie choroby choruje lub chorował ojciec?",
        "mat_grandmother_lbl": "Na jakie choroby choruje lub chorowała babcia ze strony mamy?",
        "pat_grandmother_lbl": "Na jakie choroby choruje lub chorowała babcia ze strony ojca?",
        "mat_grandfather_lbl": "Na jakie choroby choruje lub chorował dziadek ze strony mamy?",
        "pat_grandfather_lbl": "Na jakie choroby choruje lub chorował dziadek ze strony ojca?",
        # sekcja 26
        "sec_26": "26. Dotychczasowe rozpoznania, operacje i ważne informacje",
        "own_diagnoses_lbl": "Proszę wymienić wszystkie dotychczasowe rozpoznania oraz operacje",
        "important_info_lbl": "Czy są jakieś ważne informacje, które chcesz przekazać lekarzowi?",
        "current_reason_lbl": "Co jest powodem obecnych dolegliwości lub problemów zdrowotnych?",
        "key_question_lbl": "Jakie jest najważniejsze pytanie do lekarza lub najważniejszy problem do omówienia na wizycie?",
        # sekcja 27
        "sec_27": "27. Informacje organizacyjne i zgody",
        "org_info": (
            "**Proszę przesłać wszystkie posiadane wyniki badań na adres:**\n"
            "niedzialkowski@ocenazdrowia.pl\n\n"
            "**lub wgrać je po zalogowaniu się na stronie:**\n"
            "https://aplikacja.medyc.pl/NiedzialkowskiPortal/#/login\n\n"
            "Po założeniu konta możesz wgrać pliki bezpośrednio do swojej kartoteki zdrowotnej.\n"
            "Najlepiej przesłać lub wgrać jeden plik PDF z wynikami ułożonymi chronologicznie.\n\n"
            "Proszę również przynieść na wizytę posiadane wyniki badań w formie papierowej."
        ),
    },
    "en": {
        "header_title": "HEALTH ASSESSMENT",
        "header_subtitle": "Medical Interview",
        "header_contact": "Reception: +48 690 584 584 &nbsp;·&nbsp; English-speaking patients: +48 609 857 377",
        "welcome_text": (
            "Dear Patient,<br><br>"
            "each visit is prepared individually.<br>"
            "Please answer as honestly and thoroughly as possible about your health.<br>"
            "The more details you provide, the better the chances of early detection and accurate assessment.<br><br>"
            "For children, please fill in the appropriate fields.<br><br>"
            "Best regards and see you at the appointment."
        ),
        "welcome_privacy": (
            "This form is informational and serves to prepare the medical appointment. "
            "Data is not stored in the application database. "
            "After submission, it is sent exclusively to the doctor via email and PDF document."
        ),
        "send_btn": "✉ Submit form to the doctor",
        "sending": "Sending form…",
        "form_sent": "Form submitted successfully. Thank you.",
        "consent_true": "I declare that the information provided is true.",
        "consent_visit": "I consent to the use of this information exclusively by the doctor to prepare the appointment.",
        "consent_privacy": "I acknowledge that the form does not store data in the application database, and the document sent to the doctor contains limited identifying information.",
        "contact_consent": "I consent to phone or email contact for organizational matters related to the appointment.",
        "err_consent": "Please check all required consents.",
        # general
        "placeholder": "select",
        # section 1
        "sec_1": "1. Basic Information",
        "visit_type_lbl": "Type of visit",
        "first_name_lbl": "First name",
        "last_name_lbl": "Last name",
        "phone_lbl": "Contact phone",
        "phone_help": "With or without country code, e.g. 690584584 or +48690584584",
        "email_lbl": "Email address",
        "birth_date_lbl": "Date of birth",
        "nationality_lbl": "Nationality",
        "sex_lbl": "Sex",
        "sex_other_lbl": "Other sex — describe",
        "current_status_lbl": "Current status",
        "current_status_other_lbl": "Other status — describe",
        "profession_lbl": "Current occupation",
        # section 2
        "sec_2": "2. General Assessment",
        "physical_score_lbl": "How would you rate your physical health? 0 = very poor, 10 = excellent",
        "mental_score_lbl": "How would you rate your mental health? 0 = very poor, 10 = excellent",
        "weight_change_lbl": "Did your body weight change in the last year?",
        "weight_change_grew_lbl": "By how many kg did weight increase?",
        "weight_change_fell_lbl": "By how many kg did weight decrease?",
        "weight_kg_placeholder": "enter number of kg",
        # section 4
        "sec_4": "4. Main Symptoms",
        "symptom_lbl": "Symptom {n}",
        "symptom_since_lbl": "Since when has symptom {n} been present?",
        "additional_symptoms_lbl": "Other complaints, even milder ones",
        # validation errors
        "err_visit_type": "Please select the type of visit.",
        "err_first_name": "Please enter your first name.",
        "err_last_name": "Please enter your last name.",
        "err_phone": "Please enter a valid phone number. With or without +country code.",
        "err_email": "Please enter a valid email address.",
        "err_birth_date": "Please select your date of birth.",
        # section 3
        "sec_3": "3. Tests Performed in the Last 2 Years",
        "tests_lbl": "Select completed tests",
        "tests_ph": "Select tests",
        # section 5
        "sec_5": "5. Symptom Characteristics",
        "symptom_pattern_lbl": "Are symptoms constant or do they appear periodically?",
        "symptom_periodicity_lbl": "If periodic, describe when they appear and how often per year",
        "symptom_past_lbl": "Did similar symptoms occur before? If so, when?",
        "worsening_factors_lbl": "What causes worsening of symptoms?",
        "worsening_factors_ph": "Select worsening factors",
        "worsening_other_lbl": "Other worsening factors — describe",
        "improvement_factors_lbl": "What causes improvement or reduction of symptoms?",
        "improvement_factors_ph": "Select improvement factors",
        "improvement_other_lbl": "Other improvement factors — describe",
        # section 6
        "sec_6": "6. Health Timeline and Medications",
        "health_timeline_lbl": "Describe your health history from first health issues to today",
        "current_meds_lbl": "What medications are you currently taking? Provide name and dosage. Preferably enter each medication on a separate line.",
        # section 7
        "sec_7": "7. Lifestyle",
        "lifestyle_lbl": "Lifestyle",
        "lifestyle_other_lbl": "Other lifestyle — describe",
        "stimulants_lbl": "Stimulants and daily habits",
        "stimulants_ph": "Select stimulants and habits",
        "stimulants_other_lbl": "Other stimulants or habits — describe",
        "sleep_hours_lbl": "How many hours of sleep per night on average?",
        # section 8
        "sec_8": "8. Travel",
        "travel_abroad_lbl": "Was there a trip abroad in the last 3 months?",
        "travel_where_lbl": "If so, where?",
        # section 9
        "sec_9": "9. Animals",
        "animal_contact_lbl": "Was there a bite, scratch, or close contact with an animal in recent months?",
        "animal_details_lbl": "If so, describe when and what animal",
        # section 10
        "sec_10": "10. Injuries",
        "injuries_lbl": "Were there any major body injuries? Provide year and describe, e.g. fall from height, traffic accident, assault, drowning, surgery",
        # section 11
        "sec_11": "11. COVID-19",
        "covid_lbl": "Did you have COVID-19, and if so, when?",
        "covid_details_lbl": "If so, describe when and the course of illness",
        # section 12
        "sec_12": "12. Stress",
        "stress_lbl": "Were there any strong stress reactions or difficult life events? If so, describe and provide year",
        # section 13
        "sec_13": "13. Birth and Childhood",
        "birth_delivery_lbl": "Mode of delivery",
        "birth_delivery_other_lbl": "Other delivery mode — describe",
        "birth_timing_lbl": "Timing of delivery",
        "birth_timing_other_lbl": "Other delivery timing — describe",
        "green_water_lbl": "Was there meconium-stained amniotic fluid?",
        "birth_info_other_lbl": "Other birth information",
        "breastfeeding_lbl": "Was the baby breastfed?",
        "childhood_diseases_lbl": "Serious childhood illnesses",
        "childhood_diseases_ph": "Select childhood illnesses",
        "childhood_diseases_other_lbl": "Other childhood illnesses — describe",
        # section 14
        "sec_14": "14. General and Neurological Symptoms",
        "fever_lbl": "Is there currently a fever?",
        "if_yes_describe": "If so, describe in more detail",
        "headache_lbl": "Are there headaches or dizziness?",
        "headache_assoc_lbl": "Are headaches accompanied by vomiting, fainting, vision disturbances, weakness, light sensitivity, memory loss?",
        "hearing_vision_lbl": "Has hearing or vision worsened in recent years?",
        "attacks_lbl": "Are there attacks or sudden episodes? If so, describe.",
        "sinus_lbl": "Are there sinus problems?",
        "nose_lbl": "Are there nasal problems, e.g. bleeding, dryness, inflammation, difficulty breathing through the nose?",
        "allergies_lbl": "Are there allergies? If so, to what, at what time of year, and how severe?",
        "herpes_lbl": "Does herpes appear? If so, how often?",
        "mouth_corners_lbl": "Are there angular cheilitis (mouth sores at corners)?",
        "fresh_food_lbl": "After eating fresh vegetables or fruits, does burning or redness appear around the mouth?",
        "epilepsy_lbl": "Has epilepsy ever been diagnosed?",
        "smell_taste_lbl": "Are there disturbances in smell or taste? If so, since when?",
        "colds_lbl": "How often do colds occur per year?",
        # section 15
        "sec_15": "15. Respiratory System",
        "throat_lbl": "Is there sore throat in the morning?",
        "esophagus_lbl": "Does esophageal burning occur?",
        "asthma_lbl": "Has asthma ever been diagnosed?",
        "pneumonia_lbl": "Has pneumonia ever occurred?",
        "pneumonia_details_lbl": "If so, provide dates and which lung was affected",
        "dyspnea_lbl": "Does shortness of breath occur? If so, describe in which situations.",
        "night_breath_lbl": "Is there waking up at night due to breathlessness?",
        "chest_heaviness_lbl": "Is there chest tightness? If so, describe its severity.",
        "breathing_type_lbl": "Are there breathing difficulties?",
        "wheezing_lbl": "Is there wheezing?",
        "wheezing_ph": "Select wheezing circumstances",
        "cough_lbl": "Is there a cough? If so, since when, is it dry or with sputum, what color?",
        # section 16
        "sec_16": "16. Cardiovascular System",
        "chest_pain_lbl": "Is there chest pain? Is it localized or widespread? Does it radiate?",
        "pressure_type_lbl": "Are there blood pressure issues?",
        "current_bp_lbl": "What is the current blood pressure?",
        "current_hr_lbl": "What is the current heart rate?",
        "pain_press_lbl": "Do you feel pain when pressing on the chest?",
        "pain_position_lbl": "Does chest pain occur when changing position?",
        "palpitations_lbl": "Do you feel irregular heartbeat? If so, describe time of day, circumstances and frequency.",
        # section 17
        "sec_17": "17. Gastrointestinal Tract",
        "gi_problem_lbl": "Are there gastrointestinal problems?",
        "gi_symptoms_lbl": "Select problems",
        "gi_symptoms_ph": "Select GI symptoms",
        "worsening_foods_lbl": "Are there foods after which you feel worse?",
        "gi_infections_lbl": "Was there ever a bacterial or viral gastrointestinal infection? If so, when, and was there a follow-up test with a negative result?",
        # section 18
        "sec_18": "18. Urinary System",
        "urine_lbl": "Are there urination problems, e.g. burning, difficulty, other?",
        "night_urination_lbl": "How many times per night do you get up to urinate?",
        "fluids_lbl": "How many liters of fluid do you drink per day?",
        # section 19
        "sec_19": "19. Joints and Muscles",
        "joints_lbl": "Are there joint pains? If so, which joints?",
        "stiffness_lbl": "After getting out of bed, is there pain or joint stiffness?",
        # section 20
        "sec_20": "20. Skin",
        "skin_changes_lbl": "Are there any skin changes? If so, describe in detail. When did they first appear? Has there been improvement or worsening since?",
        "skin_itch_lbl": "Is there skin itching? If so, which body parts are affected?",
        "acne_lbl": "Is there or was there significant acne on the face or back?",
        "acne_details_lbl": "If so, you can describe in more detail",
        "skin_sensation_lbl": "Are there skin sensation disturbances? If so, describe location and since when.",
        "wound_healing_lbl": "Are there wound healing problems?",
        "wound_healing_details_lbl": "If so, describe the wound healing problems",
        # section 21
        "sec_21": "21. Sleep and Mental Health",
        "sleep_problem_lbl": "Are there sleep problems?",
        "sleep_types_lbl": "What types of sleep problems occur?",
        "sleep_types_ph": "Select type of sleep problems",
        "psych_contact_lbl": "Was there ever a psychological or psychiatric consultation?",
        "psych_dx_lbl": "Has a mental illness ever been diagnosed? If so, write which one.",
        # section 22
        "sec_22": "22. Peripheral Circulation",
        "edema_lbl": "Do swellings appear on the lower legs or ankles?",
        "edema_details_lbl": "If so, are they constant or after standing, sitting, or other situations?",
        "calf_pain_lbl": "Is there calf pain while walking? If so, after what distance and how long until it resolves?",
        "cold_fingers_lbl": "Do fingers or toes easily become cold or change color?",
        "tingling_lbl": "Is there tingling or numbness in hands or feet?",
        "varicose_lbl": "Are varicose veins present?",
        # section 23
        "sec_23": "23. Rectum and Anal Area",
        "anal_problems_lbl": "Are there rectal or anal area problems?",
        "anal_problems_ph": "Select anal area problems",
        "anal_other_lbl": "Other anal area problems — describe",
        # section 24
        "sec_24": "24. Gynecology or Andrology",
        "gyn_problems_lbl": "Are there gynecological problems?",
        "menstruation_lbl": "Is there irregular menstruation, menopause, or hormonal treatment? If so, since when.",
        "first_menses_lbl": "Provide month and year of first menstruation",
        "last_menses_lbl": "Date of last menstruation",
        "last_menses_help": "Preferably in DD.MM.YYYY format",
        "potency_lbl": "Are there erectile dysfunction problems?",
        # section 25
        "sec_25": "25. Family History",
        "mother_lbl": "What illnesses does/did your mother have?",
        "father_lbl": "What illnesses does/did your father have?",
        "mat_grandmother_lbl": "What illnesses does/did your maternal grandmother have?",
        "pat_grandmother_lbl": "What illnesses does/did your paternal grandmother have?",
        "mat_grandfather_lbl": "What illnesses does/did your maternal grandfather have?",
        "pat_grandfather_lbl": "What illnesses does/did your paternal grandfather have?",
        # section 26
        "sec_26": "26. Previous Diagnoses, Surgeries and Important Information",
        "own_diagnoses_lbl": "Please list all previous diagnoses and surgeries",
        "important_info_lbl": "Is there any important information you want to share with the doctor?",
        "current_reason_lbl": "What is the cause of current complaints or health problems?",
        "key_question_lbl": "What is the most important question for the doctor or the most important issue to discuss at the appointment?",
        # section 27
        "sec_27": "27. Organizational Information and Consents",
        "org_info": (
            "**Please send all available test results to:**\n"
            "niedzialkowski@ocenazdrowia.pl\n\n"
            "**or upload them after logging in at:**\n"
            "https://aplikacja.medyc.pl/NiedzialkowskiPortal/#/login\n\n"
            "After creating an account, you can upload files directly to your health record.\n"
            "It is best to send or upload a single PDF file with results arranged chronologically.\n\n"
            "Please also bring any paper test results to the appointment."
        ),
    },
}


def t(key: str) -> str:
    lang = st.session_state.get("lang", "pl")
    return TRANSLATIONS.get(lang, TRANSLATIONS["pl"]).get(key, key)


_OPT_EN: Dict[str, str] = {
    "Pierwsza": "First visit",
    "Kontrolna": "Follow-up visit",
    "kobieta": "Female",
    "mężczyzna": "Male",
    "inne": "Other",
    "pracujący": "Employed",
    "dziecko": "Child",
    "uczeń": "School student",
    "student": "University student",
    "emeryt": "Retired",
    "wzrosła": "Increased",
    "spadła": "Decreased",
    "bez zmian": "Unchanged",
    # sec 3 — badania
    "RTG klatki piersiowej": "Chest X-ray",
    "EKG": "ECG",
    "Echo serca": "Echocardiogram",
    "Holter EKG": "Holter ECG",
    "Holter ciśnieniowy": "Blood pressure Holter",
    "Gastroskopia": "Gastroscopy",
    "Kolonoskopia": "Colonoscopy",
    "USG jamy brzusznej": "Abdominal ultrasound",
    "USG miednicy": "Pelvic ultrasound",
    "USG ginekologiczne": "Gynecological ultrasound",
    "USG tarczycy": "Thyroid ultrasound",
    "USG jąder": "Testicular ultrasound",
    "USG prostaty": "Prostate ultrasound",
    "USG piersi": "Breast ultrasound",
    "Mammografia": "Mammography",
    "Tomografia komputerowa": "CT scan",
    "Tomografia głowy": "Head CT scan",
    "Rezonans magnetyczny": "MRI",
    "Rezonans głowy": "Head MRI",
    "Doppler tętnic szyjnych": "Carotid artery Doppler",
    "Przepływy w naczyniach kończyn dolnych": "Lower limb vessel flow study",
    "Densytometria": "Bone densitometry",
    "Scyntygrafia": "Scintigraphy",
    # sec 5 — charakter objawów
    "stałe": "constant",
    "okresowe": "periodic",
    "trudno powiedzieć": "hard to say",
    "wysiłek": "exercise",
    "głód": "hunger",
    "posiłek": "meal",
    "mówienie": "speaking",
    "śmiech": "laughing",
    "wypoczynek": "rest",
    # tak/nie/nie wiem
    "tak": "yes",
    "nie": "no",
    "nie wiem": "don't know",
    # sec 13 — poród i dzieciństwo
    "poród naturalny": "natural delivery",
    "poród przez cesarskie cięcie": "C-section",
    "poród przedwczesny": "premature birth",
    "poród o czasie": "term delivery",
    "poród po terminie": "post-term delivery",
    "tak, do 3 miesięcy": "yes, up to 3 months",
    "tak, do 6 miesięcy": "yes, up to 6 months",
    "tak, powyżej 6 miesięcy": "yes, over 6 months",
    "astma": "asthma",
    "atopowe zapalenie skóry": "atopic dermatitis",
    "skaza białkowa": "protein allergy",
    "częste przeziębienia": "frequent colds",
    "pobyty w szpitalu": "hospitalizations",
    "częste zapalenia płuc": "frequent pneumonia",
    "problemy jelitowe": "intestinal problems",
    "choroby psychiczne": "mental illness",
    "problemy ze śledzioną": "spleen problems",
    "problemy z trzustką": "pancreas problems",
    # sec 15 — oddechowy
    "nie mam takich trudności": "no such difficulties",
    "z nabieraniem powietrza": "with inhaling",
    "z wypuszczaniem powietrza": "with exhaling",
    "z oboma": "both",
    "podczas wysiłku": "during exercise",
    "podczas infekcji": "during infections",
    "w nocy": "at night",
    "rano": "in the morning",
    "podczas alergii": "during allergies",
    "w zimnej pogodzie": "in cold weather",
    # sec 16 — sercowo-naczyniowy
    "nie mam kłopotów z ciśnieniem": "no blood pressure issues",
    "mam skłonność do niskiego ciśnienia": "tend to have low blood pressure",
    "mam skłonność do wysokiego ciśnienia": "tend to have high blood pressure",
    # sec 17 — pokarmowy
    "zgaga": "heartburn",
    "wzdęcia": "bloating",
    "biegunki": "diarrhea",
    "zaparcia": "constipation",
    "hemoroidy": "hemorrhoids",
    "gazy": "gas",
    "skurcze": "cramps",
    "wymioty": "vomiting",
    "nudności": "nausea",
    # sec 18 — moczowy
    "7 lub więcej": "7 or more",
    "więcej niż 5": "more than 5",
    # sec 21 — sen i psychika
    "trudności z zasypianiem": "difficulty falling asleep",
    "wybudzanie w nocy": "waking during the night",
    "wstawanie zmęczony lub zmęczona": "waking up tired",
    "chrapanie": "snoring",
    "zbyt krótki sen": "too little sleep",
    "bardzo głęboki sen": "very deep sleep",
    "psycholog": "psychologist",
    "psychiatra": "psychiatrist",
    "oba": "both",
    # sec 23 — odbyt
    "stany zapalne błony śluzowej odbytu": "rectal inflammation",
    "pieczenie": "burning",
    "świąd": "itching",
    "grzybica": "fungal infection",
    # sec 24 — andrologia
    "czasami": "sometimes",
    "często": "often",
    # sec 7 — tryb życia
    "leżący": "bedridden",
    "siedzący": "sedentary",
    "nisko aktywny": "lightly active",
    "średnio aktywny": "moderately active",
    "bardzo aktywny": "very active",
    "kawa": "coffee",
    "herbata": "tea",
    "papierosy": "cigarettes",
    "alkohol": "alcohol",
    "narkotyki": "drugs",
    "słodycze": "sweets",
}


def _opt(x: str) -> str:
    if st.session_state.get("lang", "pl") == "en":
        return _OPT_EN.get(x, x)
    return x


# =========================================================
# SECRETS / ENV
# =========================================================
def get_secret(name: str) -> str:
    value = None
    try:
        value = st.secrets.get(name) if hasattr(st, "secrets") else None
    except Exception:
        pass
    if not value:
        value = os.getenv(name)
    if not value:
        st.error(f"Brakuje zmiennej środowiskowej lub wpisu w secrets.toml: {name}")
        st.stop()
    return value


EMAIL_NADAWCA = get_secret("EMAIL_NADAWCA")
HASLO_APLIKACJI = get_secret("HASLO_APLIKACJI")
EMAIL_ODBIORCA1 = get_secret("EMAIL_ODBIORCA1")
EMAIL_ODBIORCA2 = os.getenv("EMAIL_ODBIORCA2", "")


# =========================================================
# FUNKCJE POMOCNICZE
# =========================================================
def nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, bool):
        return value
    return True


def safe(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.strftime("%d.%m.%Y")
    return str(value).strip()


def list_text(values: List[str]) -> str:
    return ", ".join([v for v in values if v and v != "nie"])


def lines_from_text(text: str) -> List[str]:
    return [x.strip() for x in text.splitlines() if x.strip()]


def initials(full_name: str) -> str:
    parts = [p for p in full_name.strip().split() if p]
    if not parts:
        return ""
    return " ".join([p[0].upper() + "." for p in parts])


def bmi_calc(weight_kg: Optional[float], height_cm: Optional[float]):
    if not weight_kg or not height_cm or height_cm <= 0:
        return None
    return weight_kg / ((height_cm / 100.0) ** 2)


def bmi_label(bmi):
    if bmi is None:
        return "brak danych"
    if bmi < 18.5:
        return "niedowaga"
    if bmi < 25:
        return "masa ciała prawidłowa"
    if bmi < 30:
        return "nadwaga"
    if bmi < 35:
        return "otyłość I stopnia"
    if bmi < 40:
        return "otyłość II stopnia"
    return "otyłość III stopnia"


def validate_phone(raw: str) -> Optional[str]:
    text = (raw or "").strip()
    if not text:
        return None

    cleaned = (
        text.replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if cleaned.startswith("+"):
        digits = cleaned[1:]
    else:
        digits = cleaned

    if not digits.isdigit():
        return None

    if len(digits) < 7 or len(digits) > 15:
        return None

    return text


def validate_email(raw: str) -> Optional[str]:
    text = (raw or "").strip()
    if not text:
        return None
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(pattern, text):
        return None
    return text


def parse_polish_date(text: str) -> Optional[date]:
    raw = (text or "").strip()
    if not raw:
        return None

    formats = ["%d.%m.%Y", "%d-%m-%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(raw, fmt).date()
            if parsed < date(1900, 1, 1) or parsed > date.today():
                return None
            return parsed
        except ValueError:
            continue
    return None


def parse_optional_float(raw: str) -> Optional[float]:
    text = (raw or "").strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def select_with_placeholder(label: str, options: List[str], key: str) -> str:
    all_options = [""] + options
    return st.selectbox(
        label,
        all_options,
        format_func=lambda x: t("placeholder") if x == "" else _opt(x),
        key=key,
    )


def yes_no_unknown(label: str, key: str) -> str:
    return select_with_placeholder(label, ["tak", "nie", "nie wiem"], key)


def yes_no(label: str, key: str) -> str:
    return select_with_placeholder(label, ["tak", "nie"], key)


def error_box(message: str):
    st.markdown(
        f"<div class='field-error-box'>{message}</div>",
        unsafe_allow_html=True,
    )


def scroll_to_anchor(anchor_id: str):
    components.html(
        f"""
        <script>
        const target = window.parent.document.getElementById("{anchor_id}");
        if (target) {{
            target.scrollIntoView({{behavior: "smooth", block: "start"}});
        }}
        </script>
        """,
        height=0,
    )


def make_pdf(data: Dict[str, Any]) -> str:
    # Lazy import — reportlab ładuje się tylko przy wysyłaniu formularza
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    def register_fonts():
        regular_font = "Helvetica"
        bold_font = "Helvetica-Bold"
        if os.path.exists("DejaVuSans.ttf"):
            pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))
            regular_font = "DejaVuSans"
        if os.path.exists("DejaVuSans-Bold.ttf"):
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "DejaVuSans-Bold.ttf"))
            bold_font = "DejaVuSans-Bold"
        elif regular_font == "DejaVuSans":
            bold_font = "DejaVuSans"
        return regular_font, bold_font

    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            self._font_name = kwargs.pop("font_name", "Helvetica")
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            page_count = len(self._saved_page_states) + 1
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_number(page_count)
                super().showPage()
            self.draw_page_number(page_count)
            super().save()

        def draw_page_number(self, page_count: int):
            self.setFont(self._font_name, 9)
            self.drawCentredString(A4[0] / 2, 10 * mm, f"Strona {self._pageNumber} / {page_count}")

    def add_pdf_section(story, title: str, rows: List[str], styles_dict):
        clean_rows = [r for r in rows if nonempty(r)]
        story.append(Paragraph(title, styles_dict["section"]))
        story.append(Spacer(1, 2.2 * mm))
        if clean_rows:
            for row in clean_rows:
                story.append(Paragraph(row.replace("\n", "<br/>"), styles_dict["body"]))
                story.append(Spacer(1, 1.2 * mm))
        else:
            story.append(Paragraph("Brak danych.", styles_dict["body"]))
            story.append(Spacer(1, 1.2 * mm))
        story.append(Spacer(1, 2.5 * mm))

    regular_font, bold_font = register_fonts()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()

    doc = SimpleDocTemplate(
        tmp.name,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm,
    )

    base = getSampleStyleSheet()
    styles_dict = {
        "title_big": ParagraphStyle(
            "TitleBig",
            parent=base["Title"],
            alignment=TA_CENTER,
            fontName=bold_font,
            fontSize=16,
            leading=19,
            spaceAfter=1.5 * mm,
        ),
        "title_mid": ParagraphStyle(
            "TitleMid",
            parent=base["Title"],
            alignment=TA_CENTER,
            fontName=bold_font,
            fontSize=12,
            leading=15,
            spaceAfter=2 * mm,
        ),
        "doctor": ParagraphStyle(
            "Doctor",
            parent=base["Normal"],
            alignment=TA_CENTER,
            fontName=regular_font,
            fontSize=10.5,
            leading=13,
            spaceAfter=4 * mm,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            alignment=TA_LEFT,
            fontName=bold_font,
            fontSize=11,
            leading=14,
            spaceBefore=2 * mm,
            spaceAfter=1.5 * mm,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            alignment=TA_LEFT,
            fontName=regular_font,
            fontSize=9.5,
            leading=12,
        ),
    }

    story = []
    story.append(Paragraph("OCENA STANU ZDROWIA", styles_dict["title_big"]))
    story.append(Paragraph("Wywiad lekarski", styles_dict["title_mid"]))
    story.append(Paragraph("dr n. med. Piotr Niedziałkowski", styles_dict["doctor"]))
    story.append(Spacer(1, 1 * mm))

    add_pdf_section(
        story,
        "Dane identyfikacyjne",
        [
            f"Pacjent: {data.get('full_name') or data['initials']}",
            f"Telefon kontaktowy: {data['phone']}",
            f"Data urodzenia: {data['birth_date']}",
                f"Data i godzina wypełnienia formularza: {data['submitted_at']}",
        ],
        styles_dict,
    )

    add_pdf_section(story, "Dane podstawowe", data["sec_basic"], styles_dict)
    add_pdf_section(story, "Ocena ogólna", data["sec_overall"], styles_dict)
    add_pdf_section(story, "Badania wykonane w ciągu ostatnich 2 lat", data["sec_tests"], styles_dict)
    add_pdf_section(story, "Objawy główne", data["sec_main_symptoms"], styles_dict)
    add_pdf_section(story, "Pozostałe dolegliwości", data["sec_other_symptoms"], styles_dict)
    add_pdf_section(story, "Charakter objawów", data["sec_symptom_character"], styles_dict)
    add_pdf_section(story, "Chronologia zdrowia i leki", data["sec_timeline_meds"], styles_dict)
    add_pdf_section(story, "Tryb życia", data["sec_lifestyle"], styles_dict)
    add_pdf_section(story, "Podróże", data["sec_travel"], styles_dict)
    add_pdf_section(story, "Zwierzęta", data["sec_animals"], styles_dict)
    add_pdf_section(story, "Urazy", data["sec_injuries"], styles_dict)
    add_pdf_section(story, "COVID-19", data["sec_covid"], styles_dict)
    add_pdf_section(story, "Stres", data["sec_stress"], styles_dict)
    add_pdf_section(story, "Urodzenie i dzieciństwo", data["sec_birth_childhood"], styles_dict)
    add_pdf_section(story, "Objawy ogólne i neurologiczne", data["sec_general_neuro"], styles_dict)
    add_pdf_section(story, "Układ oddechowy", data["sec_respiratory"], styles_dict)
    add_pdf_section(story, "Układ sercowo-naczyniowy", data["sec_cardio"], styles_dict)
    add_pdf_section(story, "Przewód pokarmowy", data["sec_gi"], styles_dict)
    add_pdf_section(story, "Układ moczowy", data["sec_urinary"], styles_dict)
    add_pdf_section(story, "Stawy i mięśnie", data["sec_msk"], styles_dict)
    add_pdf_section(story, "Skóra", data["sec_skin"], styles_dict)
    add_pdf_section(story, "Sen i psychika", data["sec_sleep_psych"], styles_dict)
    add_pdf_section(story, "Krążenie obwodowe", data["sec_peripheral"], styles_dict)
    add_pdf_section(story, "Odbyt i okolice odbytu", data["sec_anal"], styles_dict)
    add_pdf_section(story, "Ginekologia lub andrologia", data["sec_sex_specific"], styles_dict)
    add_pdf_section(story, "Wywiad rodzinny", data["sec_family"], styles_dict)
    add_pdf_section(story, "Dotychczasowe rozpoznania, operacje i ważne informacje", data["sec_history_final"], styles_dict)
    add_pdf_section(story, "Najważniejsze pytanie do lekarza", data["sec_question"], styles_dict)

    doc.build(
        story,
        canvasmaker=lambda *args, **kwargs: NumberedCanvas(*args, font_name=regular_font, **kwargs),
    )
    return tmp.name


def send_confirmation_to_patient(patient_email: str, full_name: str, lang: str = "pl"):
    if not patient_email:
        return
    msg = EmailMessage()
    if lang == "pl":
        msg["Subject"] = "Potwierdzenie wysłania wywiadu lekarskiego"
        body = f"""Szanowna/Szanowny {full_name},

Dziękujemy za wypełnienie wywiadu lekarskiego. Formularz został pomyślnie przesłany do lekarza.

Prosimy o przesłanie posiadanych wyników badań na adres:
niedzialkowski@ocenazdrowia.pl

lub wgranie ich po zalogowaniu się na stronie:
https://aplikacja.medyc.pl/NiedzialkowskiPortal/#/login

Po założeniu konta można wgrać pliki bezpośrednio do swojej kartoteki zdrowotnej.
Najlepiej przesłać lub wgrać jeden plik PDF z wynikami ułożonymi chronologicznie.

Prosimy również przynieść na wizytę posiadane wyniki badań w formie papierowej.

W razie pytań prosimy o kontakt z recepcją: +48 690 584 584

Z poważaniem,
dr n. med. Piotr Niedziałkowski
www.ocenazdrowia.pl
"""
    else:
        msg["Subject"] = "Confirmation of submitted medical interview"
        body = f"""Dear {full_name},

Thank you for completing the medical interview. Your form has been successfully sent to the doctor.

Please send your test results to:
niedzialkowski@ocenazdrowia.pl

or upload them after logging in at:
https://aplikacja.medyc.pl/NiedzialkowskiPortal/#/login

After creating an account you can upload files directly to your health record.
Ideally, send or upload a single PDF with results arranged chronologically.

Please also bring any paper test results to your appointment.

For questions, please contact reception: +48 690 584 584

Best regards,
Dr. Piotr Niedziałkowski, MD
www.ocenazdrowia.pl
"""
    msg["From"] = EMAIL_NADAWCA
    msg["To"] = patient_email
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_NADAWCA, HASLO_APLIKACJI)
        smtp.send_message(msg)


def send_email_with_pdf(subject: str, body_text: str, pdf_path: str, filename: str = "wywiad_lekarski.pdf"):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_NADAWCA
    msg["To"] = EMAIL_NADAWCA
    bcc_list = [EMAIL_ODBIORCA1]
    if EMAIL_ODBIORCA2:
        bcc_list.append(EMAIL_ODBIORCA2)
    msg["Bcc"] = ", ".join(bcc_list)
    msg.set_content(body_text)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=filename,
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_NADAWCA, HASLO_APLIKACJI)
        smtp.send_message(msg)


def calc_progress(values: List[Any]) -> int:
    if not values:
        return 0
    filled = sum(1 for v in values if nonempty(v))
    return int(round((filled / len(values)) * 100))


# =========================================================
# KLUCZE FORMULARZA I PERSYSTENCJA DRAFTU
# =========================================================
_FORM_KEYS = [
    "visit_type", "first_name", "last_name", "phone", "email", "birth_date_input",
    "nationality", "sex", "sex_other", "current_status", "current_status_other",
    "profession", "height_cm_text", "weight_kg_text",
    "physical_score", "mental_score", "weight_change", "weight_change_amount_num",
    "performed_tests",
    *[f"symptom_{_i}" for _i in range(1, 11)],
    *[f"symptom_{_i}_since" for _i in range(1, 11)],
    "symptom_count", "additional_symptoms",
    "symptom_pattern", "symptom_periodicity", "symptom_past",
    "worsening_factors", "worsening_other", "improvement_factors", "improvement_other",
    "health_timeline", "current_meds",
    "lifestyle", "lifestyle_other", "stimulants", "stimulants_other", "sleep_hours",
    "travel_abroad", "travel_where",
    "animal_contact", "animal_contact_details",
    "major_injuries", "covid", "covid_details", "strong_stress",
    "birth_delivery", "birth_delivery_other", "birth_timing", "birth_timing_other",
    "green_water", "birth_info_other", "breastfeeding",
    "childhood_diseases", "childhood_diseases_other",
    "fever_now", "fever_details", "headache_dizziness", "headache_dizziness_details",
    "headache_assoc", "hearing_vision", "attacks", "sinus_problems", "nose_problems",
    "allergies", "herpes", "mouth_corners", "fresh_food_reaction", "epilepsy",
    "smell_taste", "colds",
    "throat_morning", "esophagus_burning", "asthma_dx", "pneumonia", "pneumonia_details",
    "dyspnea", "night_breath", "chest_heaviness", "breathing_type", "wheezing", "cough",
    "chest_pain", "pressure_type", "current_bp", "current_hr",
    "pain_press", "pain_position", "palpitations",
    "gi_problem", "gi_symptoms", "worsening_foods", "gi_infections",
    "urine_problems", "night_urination", "fluids",
    "joints", "stiffness",
    "skin_changes", "skin_itch", "acne", "acne_details", "skin_sensation",
    "wound_healing", "wound_healing_details",
    "sleep_problem", "sleep_problem_types", "psych_contact", "psych_dx",
    "edema", "edema_details", "calf_pain", "cold_fingers", "tingling", "varicose",
    "anal_problems", "anal_other",
    "gyn_problems", "menstruation", "first_menses", "last_menses_text", "potency",
    "mother_history", "father_history", "maternal_grandmother", "paternal_grandmother",
    "maternal_grandfather", "paternal_grandfather",
    "own_diagnoses", "important_info", "current_reason", "key_question",
    "consent_true", "consent_visit", "consent_privacy", "contact_consent",
]

_DRAFT_DIR = "/tmp"


def _draft_path(sid: str) -> str:
    return os.path.join(_DRAFT_DIR, f"form_draft_{sid}.json")


def _save_draft(sid: str):
    try:
        data: Dict[str, Any] = {"_step": st.session_state.get("step", 1)}
        for k in _FORM_KEYS:
            v = st.session_state.get(k)
            if v is None:
                continue
            if isinstance(v, (date, datetime)):
                data[k] = v.isoformat()
            else:
                data[k] = v
        with open(_draft_path(sid), "w", encoding="utf-8") as _f:
            json.dump(data, _f, ensure_ascii=False, default=str)
    except Exception:
        pass


def _load_draft(sid: str):
    path = _draft_path(sid)
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as _f:
            data = json.load(_f)
        for k, v in data.items():
            if k == "_step":
                st.session_state["step"] = int(v)
            elif k == "birth_date_input" and v:
                try:
                    st.session_state[k] = date.fromisoformat(v)
                except Exception:
                    pass
            elif k not in st.session_state:
                st.session_state[k] = v
    except Exception:
        pass


def _delete_draft(sid: str):
    try:
        path = _draft_path(sid)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


# =========================================================
# STAN SESJI
# =========================================================
# Session ID — persystuje w URL, pozwala odtworzyć draft po restarcie serwera
if "sid" not in st.session_state:
    _url_sid = st.query_params.get("sid", "")
    if _url_sid:
        st.session_state["sid"] = _url_sid
        _load_draft(_url_sid)   # przywróć dane jeśli sesja świeża
    else:
        st.session_state["sid"] = str(uuid.uuid4())[:12]
_sid: str = st.session_state["sid"]
if st.query_params.get("sid") != _sid:
    st.query_params["sid"] = _sid

if "field_errors" not in st.session_state:
    st.session_state.field_errors = {}
if "scroll_target" not in st.session_state:
    st.session_state.scroll_target = None
if "lang" not in st.session_state:
    st.session_state["lang"] = "pl"
if "step" not in st.session_state:
    st.session_state["step"] = 1
if "_nav_open" not in st.session_state:
    st.session_state["_nav_open"] = False

# ── Trwały magazyn wartości formularza ──────────────────────
# Streamlit czyści widget-keys gdy widget przestaje być renderowany
# (np. przy zmianie kroku). _form_data to zwykły dict w session_state
# — nie jest traktowany jako widget, więc nigdy nie jest czyszczony.
# Dzięki temu cofnięcie do poprzedniego kroku przywraca wpisane dane.
if "_form_data" not in st.session_state:
    st.session_state["_form_data"] = {}

# Zapisz aktualne wartości widgetów do trwałego magazynu
for _fk in _FORM_KEYS:
    _fv = st.session_state.get(_fk)
    if _fv is not None:
        st.session_state["_form_data"][_fk] = _fv

# Przywróć wartości które Streamlit wyczyścił (widget był niewidoczny)
for _fk in _FORM_KEYS:
    if _fk not in st.session_state and _fk in st.session_state["_form_data"]:
        st.session_state[_fk] = st.session_state["_form_data"][_fk]

TOTAL_STEPS = 32
step = st.session_state["step"]
field_errors: Dict[str, str] = st.session_state.field_errors
_lang = st.session_state.get("lang", "pl")
_has_form_nav = False

if "form_success" not in st.session_state:
    st.session_state["form_success"] = False
if "symptom_count" not in st.session_state:
    st.session_state["symptom_count"] = 1

# =========================================================
# GÓRA APLIKACJI
# =========================================================
_cur_lang = st.session_state.get("lang", "pl")
_lc_gap, _lc_pl, _lc_en = st.columns([5, 1, 1])
with _lc_pl:
    if st.button("PL", key="_btn_lang_pl",
                 type="primary" if _cur_lang == "pl" else "secondary",
                 use_container_width=True):
        st.session_state["lang"] = "pl"
        st.rerun()
with _lc_en:
    if st.button("EN", key="_btn_lang_en",
                 type="primary" if _cur_lang == "en" else "secondary",
                 use_container_width=True):
        st.session_state["lang"] = "en"
        st.rerun()

if os.path.exists("logo.PNG"):
    st.image("logo.PNG", use_container_width=True)
elif os.path.exists("logo.png"):
    st.image("logo.png", use_container_width=True)
elif os.path.exists("Logo OCENA ZDROWIA.PNG"):
    st.image("Logo OCENA ZDROWIA.PNG", use_container_width=True)

st.markdown(
    f"""
    <div class="header-card">
        <div class="header-title">{t("header_title")}</div>
        <div class="header-subtitle">{t("header_subtitle")}</div>
        <hr class="header-divider">
        <div class="header-doctor">dr&nbsp;n.&nbsp;med.&nbsp;Piotr&nbsp;Niedziałkowski</div>
        <div class="header-site">www.ocenazdrowia.pl</div>
        <div class="header-contact">{t("header_contact")}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# STRONA SUKCESU
# =========================================================
if st.session_state["form_success"]:
    _success_title = "Formularz wysłany pomyślnie!" if _lang == "pl" else "Form submitted successfully!"
    _success_body = (
        "Dziękujemy za wypełnienie wywiadu lekarskiego.<br>"
        "Formularz został przesłany do lekarza.<br><br>"
        "Na podany adres e-mail wysłaliśmy potwierdzenie<br>"
        "z instrukcją jak przesłać wyniki badań.<br>"
        "<small style='color:#6b7280;'>Jeśli nie widzisz wiadomości, sprawdź folder <strong>Spam</strong>.</small>"
        if _lang == "pl"
        else "Thank you for completing the medical interview.<br>"
        "Your form has been sent to the doctor.<br><br>"
        "We sent a confirmation email with instructions<br>"
        "on how to submit your test results.<br>"
        "<small style='color:#6b7280;'>If you don't see the message, please check your <strong>Spam</strong> folder.</small>"
    )
    st.markdown(
        f"""
        <div class="success-card">
            <span class="success-icon">✅</span>
            <div class="success-title">{_success_title}</div>
            <div class="success-body">{_success_body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(t("org_info"))
    _delete_draft(_sid)
    st.stop()

# =========================================================
# PASEK POSTĘPU
# =========================================================
_STEP_NAMES_PL = [
    "Dane osobowe", "Dane szczegółowe", "Wzrost i masa ciała",
    "Objawy główne", "Charakter objawów", "Badania i historia zdrowia",
    "Urodzenie i dzieciństwo", "Tryb życia", "Stres", "Podróże",
    "Kontakt ze zwierzętami", "Urazy", "COVID-19", "Objawy ogólne",
    "Objawy neurologiczne", "Górne drogi oddechowe", "Alergie",
    "Opryszczka i reakcje pokarmowe", "Układ oddechowy", "Serce i naczynia",
    "Przewód pokarmowy", "Układ moczowy", "Stawy i mięśnie", "Skóra",
    "Sen i psychika", "Krążenie obwodowe", "Odbyt i okolica odbytu",
    "Ginekologia / andrologia", "Wywiad rodzinny",
    "Dotychczasowe rozpoznania", "Informacje organizacyjne",
    "Podsumowanie i wysyłka",
]
_STEP_NAMES_EN = [
    "Personal data", "Additional details", "Height & Weight",
    "Main symptoms", "Symptom characteristics", "Diagnostics & History",
    "Birth & Childhood", "Lifestyle", "Stress", "Travel",
    "Animal contact", "Injuries", "COVID-19", "General symptoms",
    "Neurological symptoms", "Upper respiratory tract", "Allergies",
    "Herpes & Food reactions", "Respiratory system", "Cardiovascular",
    "Digestive system", "Urinary system", "Joints & Muscles", "Skin",
    "Sleep & Mental health", "Peripheral circulation", "Anal area",
    "Gynecology / Andrology", "Family history",
    "Current diagnoses", "Organizational info",
    "Summary & Submit",
]
_step_names = _STEP_NAMES_PL if _lang == "pl" else _STEP_NAMES_EN
_current_step_name = _step_names[min(step - 1, len(_step_names) - 1)]
_step_of = f"Krok {step} / {TOTAL_STEPS}" if _lang == "pl" else f"Step {step} / {TOTAL_STEPS}"
_pct_val = int(round((step / TOTAL_STEPS) * 100))
st.markdown(
    f"""
    <div class="progress-box">
        <div>
            <div class="progress-label">{_step_of}</div>
            <div class="progress-step-name">{_current_step_name}</div>
        </div>
        <div class="progress-pct">{_pct_val}%</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.progress(step / TOTAL_STEPS)

# =========================================================
# NAWIGACJA — szybki powrót do dowolnego poprzedniego kroku
# =========================================================
def _nav_toggle_cb():
    st.session_state["_nav_open"] = not st.session_state.get("_nav_open", False)

def _nav_go_cb(target_step: int):
    st.session_state["step"] = target_step
    st.session_state["_nav_open"] = False
    st.session_state["_nav_needs_rerun"] = True

@st.fragment
def _render_nav():
    _lg = st.session_state.get("lang", "pl")
    _stp = st.session_state.get("step", 1)
    _snames = _STEP_NAMES_PL if _lg == "pl" else _STEP_NAMES_EN
    _is_open = st.session_state.get("_nav_open", False)

    _lbl = (
        ("Zwiń nawigację ▲" if _is_open else "Rozwiń nawigację ▼")
        if _lg == "pl"
        else ("Close navigation ▲" if _is_open else "Open navigation ▼")
    )
    st.button(_lbl, key="_nav_toggle", on_click=_nav_toggle_cb, use_container_width=True)

    if _is_open:
        if _stp > 1:
            for _ni in range(1, _stp):
                st.button(
                    f"✓  {_ni}. {_snames[_ni - 1]}",
                    key=f"_nav_s{_ni}",
                    on_click=_nav_go_cb,
                    args=(_ni,),
                    use_container_width=True,
                    type="primary",
                )
        st.markdown(
            f"<div style='background:#c9a84c;color:#132743;font-weight:700;"
            f"border-radius:8px;padding:8px 14px;font-size:0.9rem;margin-bottom:4px;'>"
            f"▶  {_stp}. {_snames[_stp - 1]}</div>",
            unsafe_allow_html=True,
        )
        if _stp < TOTAL_STEPS:
            _rem = TOTAL_STEPS - _stp
            st.caption(
                f"+ {_rem} kolejnych kroków" if _lg == "pl" else f"+ {_rem} more steps"
            )

    if st.session_state.get("_nav_needs_rerun"):
        del st.session_state["_nav_needs_rerun"]
        st.rerun()

if not st.session_state.get("form_success"):
    _render_nav()

# =========================================================
# KROKI
# =========================================================
if step == 1:
    _has_form_nav = True
    st.markdown(
        f"""
        <div class="welcome-card">
            {t("welcome_text")}
            <div class="welcome-privacy">{t("welcome_privacy")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="video-wrapper">'
        '<iframe src="https://www.youtube.com/embed/qdwtGE9k4GY" allowfullscreen></iframe>'
        '</div>',
        unsafe_allow_html=True,
    )
    for _fk in ["first_name", "phone", "email", "birth_date"]:
        if _fk in field_errors:
            error_box(field_errors[_fk])
    with st.form("step_form_1"):
        st.subheader(t("sec_1"))
        st.text_input(t("first_name_lbl"), key="first_name")
        st.text_input(t("last_name_lbl"), key="last_name")
        st.text_input(t("phone_lbl"), key="phone", help=t("phone_help"))
        st.text_input(t("email_lbl"), key="email")
        st.date_input(
            t("birth_date_lbl"),
            value=None,
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            format="DD.MM.YYYY",
            key="birth_date_input",
        )
        st.markdown("---")
        _f1_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
    if _f1_next:
        _errs1 = {}
        if not st.session_state.get("first_name", "").strip():
            _errs1["first_name"] = t("err_first_name")
        _ph1 = st.session_state.get("phone", "")
        if not validate_phone(_ph1):
            _errs1["phone"] = t("err_phone")
        _em1 = st.session_state.get("email", "")
        if not validate_email(_em1):
            _errs1["email"] = t("err_email")
        if st.session_state.get("birth_date_input") is None:
            _errs1["birth_date"] = t("err_birth_date")
        if _errs1:
            st.session_state.field_errors = _errs1
        else:
            st.session_state.field_errors = {}
            st.session_state["step"] += 1
        st.rerun()

# =========================================================
# KROK 2 — Dane podstawowe cz. 2
# =========================================================
elif step == 2:
    _has_form_nav = True
    @st.fragment
    def _step2():
        _lg = st.session_state.get("lang", "pl")
        _h2 = "Dane podstawowe — część dalsza" if _lg == "pl" else "Basic Information — continued"
        st.subheader(_h2)
        st.text_input(t("nationality_lbl"), key="nationality")
        _sex2 = select_with_placeholder(t("sex_lbl"), ["kobieta", "mężczyzna", "inne"], key="sex")
        if _sex2 == "inne":
            st.text_input(t("sex_other_lbl"), key="sex_other")
        _cst2 = select_with_placeholder(
            t("current_status_lbl"),
            ["pracujący", "dziecko", "uczeń", "student", "emeryt", "inne"],
            key="current_status",
        )
        if _cst2 == "inne":
            st.text_input(t("current_status_other_lbl"), key="current_status_other")
        st.text_input(t("profession_lbl"), key="profession")
        st.write("")
        st.markdown("---")
        if st.button("Dalej →" if _lg == "pl" else "Next →", key="s2_next", use_container_width=True, type="primary"):
            st.session_state["step"] += 1
            st.rerun()
        if st.button("← Wstecz" if _lg == "pl" else "← Back", key="s2_back", use_container_width=True, type="primary"):
            st.session_state["step"] -= 1
            st.rerun()
    _step2()

# =========================================================
# KROK 3 — Ocena ogólna i BMI
# =========================================================
elif step == 3:
    _has_form_nav = True
    @st.fragment
    def _step3():
        _lg = st.session_state.get("lang", "pl")
        _bmi_title = "Wzrost, masa ciała i BMI" if _lg == "pl" else "Height, Weight and BMI"
        st.subheader(_bmi_title)
        _col1, _col2 = st.columns(2)
        with _col1:
            st.text_input("Wzrost (cm)" if _lg == "pl" else "Height (cm)", key="height_cm_text")
        with _col2:
            st.text_input("Masa ciała (kg)" if _lg == "pl" else "Weight (kg)", key="weight_kg_text")
        _h3 = parse_optional_float(st.session_state.get("height_cm_text", ""))
        _w3 = parse_optional_float(st.session_state.get("weight_kg_text", ""))
        _bmi3 = bmi_calc(_w3, _h3)
        if _bmi3 is not None:
            if _bmi3 < 18.5:
                _bc3, _bb3 = "#1565C0", "rgba(21,101,192,0.12)"
            elif _bmi3 < 25:
                _bc3, _bb3 = "#2E7D32", "rgba(46,125,50,0.12)"
            elif _bmi3 < 30:
                _bc3, _bb3 = "#E65100", "rgba(230,81,0,0.12)"
            elif _bmi3 < 35:
                _bc3, _bb3 = "#BF360C", "rgba(191,54,12,0.12)"
            else:
                _bc3, _bb3 = "#B71C1C", "rgba(183,28,28,0.14)"
            st.markdown(
                f"<div style='padding:10px 14px;border-radius:10px;border:1px solid {_bc3};"
                f"background:{_bb3};color:{_bc3};font-weight:700;font-size:1rem;'>"
                f"BMI: {_bmi3:.1f} — {bmi_label(_bmi3)}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.caption("BMI zostanie obliczone po wpisaniu wzrostu i masy ciała." if _lg == "pl" else "BMI will be calculated after entering height and weight.")
        st.subheader(t("sec_2"))
        st.slider(t("physical_score_lbl"), min_value=0, max_value=10, value=5, key="physical_score")
        st.slider(t("mental_score_lbl"), min_value=0, max_value=10, value=5, key="mental_score")
        _wch3 = select_with_placeholder(
            t("weight_change_lbl"), ["wzrosła", "spadła", "bez zmian"], key="weight_change"
        )
        if _wch3 in ["wzrosła", "spadła"]:
            _wc_lbl = t("weight_change_grew_lbl") if _wch3 == "wzrosła" else t("weight_change_fell_lbl")
            st.number_input(
                _wc_lbl,
                min_value=0.0, max_value=200.0, value=None,
                step=0.5, format="%.1f",
                placeholder=t("weight_kg_placeholder"),
                key="weight_change_amount_num",
            )
        st.markdown("---")
        if st.button("Dalej →" if _lg == "pl" else "Next →", key="s3_next", use_container_width=True, type="primary"):
            st.session_state["step"] += 1
            st.rerun()
        if st.button("← Wstecz" if _lg == "pl" else "← Back", key="s3_back", use_container_width=True, type="primary"):
            st.session_state["step"] -= 1
            st.rerun()
    _step3()

# =========================================================
# KROK 4 — Objawy główne (dynamiczne)
# =========================================================
elif step == 4:
    _has_form_nav = True
    @st.fragment
    def _step4():
        _lg = st.session_state.get("lang", "pl")
        st.subheader(t("sec_4"))
        _sc = st.session_state.get("symptom_count", 1)
        for _si in range(1, _sc + 1):
            if _si > 1:
                st.markdown("---")
            st.text_input(t("symptom_lbl").format(n=_si), key=f"symptom_{_si}")
            st.text_input(t("symptom_since_lbl").format(n=_si), key=f"symptom_{_si}_since")
        _add_lbl = "➕ Dodaj objaw" if _lg == "pl" else "➕ Add symptom"
        if _sc < 10:
            if st.button(_add_lbl, key="add_symptom"):
                st.session_state["symptom_count"] = _sc + 1
                st.rerun()
        st.markdown("---")
        st.text_area(t("additional_symptoms_lbl"), key="additional_symptoms")
        st.markdown("---")
        if st.button("Dalej →" if _lg == "pl" else "Next →", key="s4_next", use_container_width=True, type="primary"):
            st.session_state["step"] += 1
            st.rerun()
        if st.button("← Wstecz" if _lg == "pl" else "← Back", key="s4_back", use_container_width=True, type="primary"):
            st.session_state["step"] -= 1
            st.rerun()
    _step4()

# =========================================================
# KROK 5 — Charakter objawów
# =========================================================
elif step == 5:
    _has_form_nav = True
    @st.fragment
    def _step5():
        _lg = st.session_state.get("lang", "pl")
        st.subheader(t("sec_5"))
        _sp5 = select_with_placeholder(
            t("symptom_pattern_lbl"),
            ["stałe", "okresowe", "trudno powiedzieć"],
            key="symptom_pattern",
        )
        if _sp5 == "okresowe":
            st.text_area(t("symptom_periodicity_lbl"), key="symptom_periodicity")
        st.text_area(t("symptom_past_lbl"), key="symptom_past")
        _wf5 = st.multiselect(
            t("worsening_factors_lbl"),
            ["wysiłek", "głód", "posiłek", "mówienie", "śmiech", "inne"],
            format_func=_opt,
            placeholder=t("worsening_factors_ph"),
            key="worsening_factors",
        )
        if "inne" in _wf5:
            st.text_input(t("worsening_other_lbl"), key="worsening_other")
        _if5 = st.multiselect(
            t("improvement_factors_lbl"),
            ["wypoczynek", "wysiłek", "głód", "posiłek", "inne"],
            format_func=_opt,
            placeholder=t("improvement_factors_ph"),
            key="improvement_factors",
        )
        if "inne" in _if5:
            st.text_input(t("improvement_other_lbl"), key="improvement_other")
        st.markdown("---")
        if st.button("Dalej →" if _lg == "pl" else "Next →", key="s5_next", use_container_width=True, type="primary"):
            st.session_state["step"] += 1
            st.rerun()
        if st.button("← Wstecz" if _lg == "pl" else "← Back", key="s5_back", use_container_width=True, type="primary"):
            st.session_state["step"] -= 1
            st.rerun()
    _step5()

# =========================================================
# KROK 6 — Badania i chronologia zdrowia
# =========================================================
elif step == 6:
    _has_form_nav = True
    _f6_back = False
    with st.form("step_form_6"):
        st.subheader(t("sec_3"))
        st.multiselect(
            t("tests_lbl"),
            [
                "RTG klatki piersiowej", "EKG", "Echo serca", "Holter EKG", "Holter ciśnieniowy",
                "Gastroskopia", "Kolonoskopia", "USG jamy brzusznej", "USG miednicy",
                "USG ginekologiczne", "USG tarczycy", "USG jąder", "USG prostaty", "USG piersi",
                "Mammografia", "Tomografia komputerowa", "Tomografia głowy",
                "Rezonans magnetyczny", "Rezonans głowy", "Doppler tętnic szyjnych",
                "Przepływy w naczyniach kończyn dolnych", "Densytometria", "Scyntygrafia",
            ],
            format_func=_opt,
            placeholder=t("tests_ph"),
            key="performed_tests",
        )
        st.subheader(t("sec_6"))
        st.text_area(t("health_timeline_lbl"), key="health_timeline")
        st.text_area(t("current_meds_lbl"), key="current_meds")
        st.markdown("---")
        _f6_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f6_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f6_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f6_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 7 — Urodzenie i dzieciństwo
# =========================================================
elif step == 7:
    _has_form_nav = True
    @st.fragment
    def _step7():
        _lg = st.session_state.get("lang", "pl")
        st.subheader(t("sec_13"))
        _bd7 = select_with_placeholder(
            t("birth_delivery_lbl"),
            ["poród naturalny", "poród przez cesarskie cięcie", "nie wiem", "inne"],
            key="birth_delivery",
        )
        if _bd7 == "inne":
            st.text_input(t("birth_delivery_other_lbl"), key="birth_delivery_other")
        _bt7 = select_with_placeholder(
            t("birth_timing_lbl"),
            ["poród przedwczesny", "poród o czasie", "poród po terminie", "nie wiem", "inne"],
            key="birth_timing",
        )
        if _bt7 == "inne":
            st.text_input(t("birth_timing_other_lbl"), key="birth_timing_other")
        yes_no_unknown(t("green_water_lbl"), key="green_water")
        st.text_input(t("birth_info_other_lbl"), key="birth_info_other")
        select_with_placeholder(
            t("breastfeeding_lbl"),
            ["tak, do 3 miesięcy", "tak, do 6 miesięcy", "tak, powyżej 6 miesięcy", "nie", "nie wiem"],
            key="breastfeeding",
        )
        _cd7 = st.multiselect(
            t("childhood_diseases_lbl"),
            ["astma", "atopowe zapalenie skóry", "skaza białkowa", "częste przeziębienia",
             "pobyty w szpitalu", "częste zapalenia płuc", "problemy jelitowe",
             "choroby psychiczne", "problemy ze śledzioną", "problemy z trzustką", "inne"],
            format_func=_opt,
            placeholder=t("childhood_diseases_ph"),
            key="childhood_diseases",
        )
        if "inne" in _cd7:
            st.text_input(t("childhood_diseases_other_lbl"), key="childhood_diseases_other")
        st.markdown("---")
        if st.button("Dalej →" if _lg == "pl" else "Next →", key="s7_next", use_container_width=True, type="primary"):
            st.session_state["step"] += 1
            st.rerun()
        if st.button("← Wstecz" if _lg == "pl" else "← Back", key="s7_back", use_container_width=True, type="primary"):
            st.session_state["step"] -= 1
            st.rerun()
    _step7()

# =========================================================
# KROK 8 — Tryb życia
# =========================================================
elif step == 8:
    _has_form_nav = True
    @st.fragment
    def _step8():
        _lg = st.session_state.get("lang", "pl")
        st.subheader(t("sec_7"))
        _ls8 = select_with_placeholder(
            t("lifestyle_lbl"),
            ["leżący", "siedzący", "nisko aktywny", "średnio aktywny", "bardzo aktywny", "inne"],
            key="lifestyle",
        )
        if _ls8 == "inne":
            st.text_input(t("lifestyle_other_lbl"), key="lifestyle_other")
        _st8 = st.multiselect(
            t("stimulants_lbl"),
            ["kawa", "herbata", "papierosy", "alkohol", "narkotyki", "słodycze", "inne"],
            format_func=_opt,
            placeholder=t("stimulants_ph"),
            key="stimulants",
        )
        if "inne" in _st8:
            st.text_input(t("stimulants_other_lbl"), key="stimulants_other")
        select_with_placeholder(
            t("sleep_hours_lbl"),
            ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12"],
            key="sleep_hours",
        )
        st.markdown("---")
        if st.button("Dalej →" if _lg == "pl" else "Next →", key="s8_next", use_container_width=True, type="primary"):
            st.session_state["step"] += 1
            st.rerun()
        if st.button("← Wstecz" if _lg == "pl" else "← Back", key="s8_back", use_container_width=True, type="primary"):
            st.session_state["step"] -= 1
            st.rerun()
    _step8()

# =========================================================
# KROK 9 — Stres
# =========================================================
elif step == 9:
    _has_form_nav = True
    _f9_back = False
    with st.form("step_form_9"):
        st.subheader(t("sec_12"))
        st.text_area(t("stress_lbl"), key="strong_stress")
        st.markdown("---")
        _f9_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f9_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f9_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f9_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 10 — Podróże
# =========================================================
elif step == 10:
    _has_form_nav = True
    _f10_back = False
    with st.form("step_form_10"):
        st.subheader(t("sec_8"))
        yes_no(t("travel_abroad_lbl"), key="travel_abroad")
        st.text_input(t("travel_where_lbl"), key="travel_where")
        st.markdown("---")
        _f10_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f10_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f10_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f10_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 11 — Zwierzęta
# =========================================================
elif step == 11:
    _has_form_nav = True
    _f11_back = False
    with st.form("step_form_11"):
        st.subheader(t("sec_9"))
        yes_no(t("animal_contact_lbl"), key="animal_contact")
        st.text_area(t("animal_details_lbl"), key="animal_contact_details")
        st.markdown("---")
        _f11_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f11_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f11_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f11_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 12 — Urazy
# =========================================================
elif step == 12:
    _has_form_nav = True
    _f12_back = False
    with st.form("step_form_12"):
        st.subheader(t("sec_10"))
        st.text_area(t("injuries_lbl"), key="major_injuries")
        st.markdown("---")
        _f12_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f12_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f12_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f12_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 13 — COVID-19
# =========================================================
elif step == 13:
    _has_form_nav = True
    _f13_back = False
    with st.form("step_form_13"):
        st.subheader(t("sec_11"))
        yes_no_unknown(t("covid_lbl"), key="covid")
        st.text_area(t("covid_details_lbl"), key="covid_details")
        st.markdown("---")
        _f13_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f13_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f13_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f13_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 14 — Objawy ogólne
# =========================================================
elif step == 14:
    _has_form_nav = True
    _f14_back = False
    with st.form("step_form_14"):
        _h14 = "Objawy ogólne" if _lang == "pl" else "General Symptoms"
        st.subheader(_h14)
        yes_no(t("fever_lbl"), key="fever_now")
        st.text_area(t("if_yes_describe"), key="fever_details")
        yes_no(t("headache_lbl"), key="headache_dizziness")
        st.text_area(t("if_yes_describe"), key="headache_dizziness_details")
        st.text_area(t("hearing_vision_lbl"), key="hearing_vision")
        st.text_area(t("attacks_lbl"), key="attacks")
        st.markdown("---")
        _f14_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f14_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f14_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f14_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 15 — Objawy neurologiczne
# =========================================================
elif step == 15:
    _has_form_nav = True
    _f15_back = False
    with st.form("step_form_15"):
        _h15 = "Objawy neurologiczne" if _lang == "pl" else "Neurological Symptoms"
        st.subheader(_h15)
        st.text_area(t("headache_assoc_lbl"), key="headache_assoc")
        yes_no(t("epilepsy_lbl"), key="epilepsy")
        st.text_area(t("smell_taste_lbl"), key="smell_taste")
        st.markdown("---")
        _f15_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f15_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f15_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f15_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 16 — Górne drogi oddechowe
# =========================================================
elif step == 16:
    _has_form_nav = True
    _f16_back = False
    with st.form("step_form_16"):
        _h16 = "Górne drogi oddechowe" if _lang == "pl" else "Upper Respiratory Tract"
        st.subheader(_h16)
        st.text_area(t("sinus_lbl"), key="sinus_problems")
        st.text_area(t("nose_lbl"), key="nose_problems")
        st.markdown("---")
        _f16_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f16_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f16_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f16_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 17 — Alergie
# =========================================================
elif step == 17:
    _has_form_nav = True
    _f17_back = False
    with st.form("step_form_17"):
        _h17 = "Alergie" if _lang == "pl" else "Allergies"
        st.subheader(_h17)
        st.text_area(t("allergies_lbl"), key="allergies")
        st.markdown("---")
        _f17_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f17_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f17_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f17_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 18 — Opryszczka, zajady i reakcje pokarmowe
# =========================================================
elif step == 18:
    _has_form_nav = True
    _f18_back = False
    with st.form("step_form_18"):
        _h18 = "Opryszczka, zajady i reakcje pokarmowe" if _lang == "pl" else "Herpes, Angular Cheilitis and Food Reactions"
        st.subheader(_h18)
        st.text_area(t("herpes_lbl"), key="herpes")
        st.text_area(t("mouth_corners_lbl"), key="mouth_corners")
        st.text_area(t("fresh_food_lbl"), key="fresh_food_reaction")
        st.markdown("---")
        _f18_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f18_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f18_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f18_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 19 — Układ oddechowy
# =========================================================
elif step == 19:
    _has_form_nav = True
    _f19_back = False
    with st.form("step_form_19"):
        st.subheader(t("sec_15"))
        yes_no(t("throat_lbl"), key="throat_morning")
        yes_no(t("esophagus_lbl"), key="esophagus_burning")
        yes_no(t("asthma_lbl"), key="asthma_dx")
        yes_no(t("pneumonia_lbl"), key="pneumonia")
        st.text_area(t("pneumonia_details_lbl"), key="pneumonia_details")
        st.text_area(t("dyspnea_lbl"), key="dyspnea")
        st.text_area(t("night_breath_lbl"), key="night_breath")
        st.text_area(t("chest_heaviness_lbl"), key="chest_heaviness")
        select_with_placeholder(
            t("breathing_type_lbl"),
            ["nie mam takich trudności", "z nabieraniem powietrza", "z wypuszczaniem powietrza", "z oboma"],
            key="breathing_type",
        )
        st.multiselect(
            t("wheezing_lbl"),
            ["podczas wysiłku", "podczas infekcji", "w nocy", "rano", "podczas alergii", "w zimnej pogodzie"],
            format_func=_opt,
            placeholder=t("wheezing_ph"),
            key="wheezing",
        )
        st.text_area(t("cough_lbl"), key="cough")
        st.text_input(t("colds_lbl"), key="colds")
        st.markdown("---")
        _f19_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f19_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f19_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f19_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 20 — Układ sercowo-naczyniowy
# =========================================================
elif step == 20:
    _has_form_nav = True
    _f20_back = False
    with st.form("step_form_20"):
        st.subheader(t("sec_16"))
        st.text_area(t("chest_pain_lbl"), key="chest_pain")
        select_with_placeholder(
            t("pressure_type_lbl"),
            ["nie mam kłopotów z ciśnieniem", "mam skłonność do niskiego ciśnienia", "mam skłonność do wysokiego ciśnienia"],
            key="pressure_type",
        )
        st.text_input(t("current_bp_lbl"), key="current_bp")
        st.text_input(t("current_hr_lbl"), key="current_hr")
        yes_no(t("pain_press_lbl"), key="pain_press")
        yes_no(t("pain_position_lbl"), key="pain_position")
        st.text_area(t("palpitations_lbl"), key="palpitations")
        st.markdown("---")
        _f20_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f20_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f20_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f20_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 21 — Przewód pokarmowy
# =========================================================
elif step == 21:
    _has_form_nav = True
    _f21_back = False
    with st.form("step_form_21"):
        st.subheader(t("sec_17"))
        yes_no(t("gi_problem_lbl"), key="gi_problem")
        st.multiselect(
            t("gi_symptoms_lbl"),
            ["zgaga", "wzdęcia", "biegunki", "zaparcia", "hemoroidy", "gazy", "skurcze", "wymioty", "nudności"],
            format_func=_opt,
            placeholder=t("gi_symptoms_ph"),
            key="gi_symptoms",
        )
        st.text_area(t("worsening_foods_lbl"), key="worsening_foods")
        st.text_area(t("gi_infections_lbl"), key="gi_infections")
        st.markdown("---")
        _f21_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f21_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f21_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f21_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 22 — Układ moczowy
# =========================================================
elif step == 22:
    _has_form_nav = True
    _f22_back = False
    with st.form("step_form_22"):
        st.subheader(t("sec_18"))
        st.text_area(t("urine_lbl"), key="urine_problems")
        select_with_placeholder(
            t("night_urination_lbl"),
            ["0", "1", "2", "3", "4", "5", "6", "7 lub więcej"],
            key="night_urination",
        )
        select_with_placeholder(
            t("fluids_lbl"),
            ["1", "2", "3", "4", "5", "więcej niż 5"],
            key="fluids",
        )
        st.markdown("---")
        _f22_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f22_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f22_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f22_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 23 — Stawy i mięśnie
# =========================================================
elif step == 23:
    _has_form_nav = True
    _f23_back = False
    with st.form("step_form_23"):
        st.subheader(t("sec_19"))
        st.text_area(t("joints_lbl"), key="joints")
        st.text_area(t("stiffness_lbl"), key="stiffness")
        st.markdown("---")
        _f23_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f23_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f23_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f23_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 24 — Skóra
# =========================================================
elif step == 24:
    _has_form_nav = True
    _f24_back = False
    with st.form("step_form_24"):
        st.subheader(t("sec_20"))
        st.text_area(t("skin_changes_lbl"), key="skin_changes")
        st.text_area(t("skin_itch_lbl"), key="skin_itch")
        yes_no(t("acne_lbl"), key="acne")
        st.text_area(t("acne_details_lbl"), key="acne_details")
        st.text_area(t("skin_sensation_lbl"), key="skin_sensation")
        yes_no(t("wound_healing_lbl"), key="wound_healing")
        st.text_area(t("wound_healing_details_lbl"), key="wound_healing_details")
        st.markdown("---")
        _f24_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f24_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f24_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f24_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 25 — Sen i psychika
# =========================================================
elif step == 25:
    _has_form_nav = True
    _f25_back = False
    with st.form("step_form_25"):
        st.subheader(t("sec_21"))
        yes_no(t("sleep_problem_lbl"), key="sleep_problem")
        st.multiselect(
            t("sleep_types_lbl"),
            ["trudności z zasypianiem", "wybudzanie w nocy", "wstawanie zmęczony lub zmęczona",
             "chrapanie", "zbyt krótki sen", "bardzo głęboki sen"],
            format_func=_opt,
            placeholder=t("sleep_types_ph"),
            key="sleep_problem_types",
        )
        select_with_placeholder(t("psych_contact_lbl"), ["nie", "psycholog", "psychiatra", "oba"], key="psych_contact")
        st.text_area(t("psych_dx_lbl"), key="psych_dx")
        st.markdown("---")
        _f25_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f25_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f25_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f25_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 26 — Krążenie obwodowe
# =========================================================
elif step == 26:
    _has_form_nav = True
    _f26_back = False
    with st.form("step_form_26"):
        st.subheader(t("sec_22"))
        yes_no(t("edema_lbl"), key="edema")
        st.text_area(t("edema_details_lbl"), key="edema_details")
        st.text_area(t("calf_pain_lbl"), key="calf_pain")
        st.text_area(t("cold_fingers_lbl"), key="cold_fingers")
        st.text_area(t("tingling_lbl"), key="tingling")
        st.text_area(t("varicose_lbl"), key="varicose")
        st.markdown("---")
        _f26_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f26_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f26_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f26_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 27 — Odbyt i okolica odbytu
# =========================================================
elif step == 27:
    _has_form_nav = True
    _f27_back = False
    with st.form("step_form_27"):
        st.subheader(t("sec_23"))
        _ap27 = st.multiselect(
            t("anal_problems_lbl"),
            ["hemoroidy", "stany zapalne błony śluzowej odbytu", "pieczenie", "świąd", "grzybica", "inne"],
            format_func=_opt,
            placeholder=t("anal_problems_ph"),
            key="anal_problems",
        )
        st.text_input(t("anal_other_lbl"), key="anal_other")
        st.markdown("---")
        _f27_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f27_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f27_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f27_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 28 — Ginekologia / andrologia
# =========================================================
elif step == 28:
    _has_form_nav = True
    @st.fragment
    def _step28():
        _lg = st.session_state.get("lang", "pl")
        st.subheader(t("sec_24"))
        _sex28 = st.session_state.get("sex", "")
        if _sex28 == "kobieta":
            st.text_area(t("gyn_problems_lbl"), key="gyn_problems")
            st.text_area(t("menstruation_lbl"), key="menstruation")
            st.text_input(t("first_menses_lbl"), key="first_menses")
            st.text_input(t("last_menses_lbl"), key="last_menses_text", help=t("last_menses_help"))
        elif _sex28 == "mężczyzna":
            select_with_placeholder(t("potency_lbl"), ["nie", "czasami", "często"], key="potency")
            st.text_area(
                "Inne dolegliwości andrologiczne lub urogenitalne" if _lg == "pl" else "Other andrological or urogenital complaints",
                key="gyn_problems",
            )
        else:
            st.text_area(
                "Dolegliwości ginekologiczne lub andrologiczne — opisz" if _lg == "pl" else "Gynecological or andrological complaints — describe",
                key="gyn_problems",
            )
            select_with_placeholder(t("potency_lbl"), ["nie", "czasami", "często"], key="potency")
        st.markdown("---")
        if st.button("Dalej →" if _lg == "pl" else "Next →", key="s28_next", use_container_width=True, type="primary"):
            st.session_state["step"] += 1
            st.rerun()
        if st.button("← Wstecz" if _lg == "pl" else "← Back", key="s28_back", use_container_width=True, type="primary"):
            st.session_state["step"] -= 1
            st.rerun()
    _step28()

# =========================================================
# KROK 29 — Wywiad rodzinny
# =========================================================
elif step == 29:
    _has_form_nav = True
    _f29_back = False
    with st.form("step_form_29"):
        st.subheader(t("sec_25"))
        st.text_area(t("mother_lbl"), key="mother_history")
        st.text_area(t("father_lbl"), key="father_history")
        st.text_area(t("mat_grandmother_lbl"), key="maternal_grandmother")
        st.text_area(t("pat_grandmother_lbl"), key="paternal_grandmother")
        st.text_area(t("mat_grandfather_lbl"), key="maternal_grandfather")
        st.text_area(t("pat_grandfather_lbl"), key="paternal_grandfather")
        st.markdown("---")
        _f29_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f29_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f29_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f29_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 30 — Dotychczasowe rozpoznania i ważne informacje
# =========================================================
elif step == 30:
    _has_form_nav = True
    _f30_back = False
    with st.form("step_form_30"):
        st.subheader(t("sec_26"))
        st.text_area(t("own_diagnoses_lbl"), key="own_diagnoses")
        st.text_area(t("important_info_lbl"), key="important_info")
        st.text_area(t("current_reason_lbl"), key="current_reason")
        st.text_area(t("key_question_lbl"), key="key_question")
        st.markdown("---")
        _f30_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f30_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f30_next:
        st.session_state["step"] += 1
        st.rerun()
    elif _f30_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 31 — Informacje organizacyjne i zgody
# =========================================================
elif step == 31:
    _has_form_nav = True
    _f31_back = False
    with st.form("step_form_31"):
        st.subheader(t("sec_27"))
        st.markdown(t("org_info"))
        st.checkbox(t("consent_true"), key="consent_true")
        st.checkbox(t("consent_visit"), key="consent_visit")
        st.checkbox(t("consent_privacy"), key="consent_privacy")
        st.checkbox(t("contact_consent"), key="contact_consent")
        st.markdown("---")
        _f31_next = st.form_submit_button("Dalej →" if _lang == "pl" else "Next →", use_container_width=True, type="primary")
        _f31_back = st.form_submit_button("← Wstecz" if _lang == "pl" else "← Back", use_container_width=True, type="primary")
    if _f31_next:
        _all_consents = (
            st.session_state.get("consent_true", False)
            and st.session_state.get("consent_visit", False)
            and st.session_state.get("consent_privacy", False)
            and st.session_state.get("contact_consent", False)
        )
        if _all_consents:
            st.session_state["step"] += 1
            st.rerun()
        else:
            st.error(
                "Proszę zaznaczyć wszystkie zgody przed przejściem dalej."
                if _lang == "pl"
                else "Please check all consents before proceeding."
            )
    elif _f31_back:
        st.session_state["step"] -= 1
        st.rerun()

# =========================================================
# KROK 32 — Podsumowanie i wysyłka
# =========================================================
elif step == 32:
    _has_form_nav = True
    _sum_h = "Podsumowanie" if _lang == "pl" else "Summary"
    st.subheader(_sum_h)
    _s_fn = st.session_state.get("first_name", "").strip()
    _s_ln = st.session_state.get("last_name", "").strip()
    _s_ph = st.session_state.get("phone", "")
    _s_bd = st.session_state.get("birth_date_input")
    _sum_rows = []
    if _s_fn or _s_ln:
        _sum_rows.append(("Pacjent" if _lang == "pl" else "Patient", f"{_s_fn} {_s_ln}".strip()))
    if _s_ph:
        _sum_rows.append(("Telefon" if _lang == "pl" else "Phone", _s_ph))
    if _s_bd:
        _sum_rows.append(("Data urodzenia" if _lang == "pl" else "Date of birth", _s_bd.strftime("%d.%m.%Y")))
    _sc_disp = st.session_state.get("symptom_count", 1)
    for _si in range(1, _sc_disp + 1):
        _sv = st.session_state.get(f"symptom_{_si}", "")
        if _sv:
            _lbl = f"Objaw {_si}" if _lang == "pl" else f"Symptom {_si}"
            _sum_rows.append((_lbl, _sv))
    for _slbl, _sval in _sum_rows:
        st.markdown(f"**{_slbl}:** {_sval}")
    st.markdown("---")

    if st.button("← Wstecz" if _lang == "pl" else "← Back", key="s32_back", use_container_width=True, type="primary"):
        st.session_state["step"] -= 1
        st.rerun()
    send_clicked = st.button(t("send_btn"), key="send_button", use_container_width=True, type="primary")

    if send_clicked:
        _fd = st.session_state.get("_form_data", {})

        def _g(key, default=None):
            """Czyta z session_state; jeśli brak — z _form_data (trwały magazyn)."""
            v = st.session_state.get(key)
            if v is None:
                v = _fd.get(key)
            return v if v is not None else (default if default is not None else "")

        def _gl(key):
            """Jak _g ale domyślnie zwraca []."""
            v = _g(key, None)
            return v if isinstance(v, list) else ([] if v is None or v == "" else [v])

        _sex_s = _g("sex")
        first_name_clean = _g("first_name", "").strip()
        last_name_clean = _g("last_name", "").strip()
        phone_raw = _g("phone", "")
        email_raw = _g("email", "")
        birth_date = _g("birth_date_input")
        validated_phone = validate_phone(phone_raw)
        validated_email = validate_email(email_raw) if email_raw else None
        consent_true_v = st.session_state.get("consent_true", False)
        consent_visit_v = st.session_state.get("consent_visit", False)
        consent_privacy_v = st.session_state.get("consent_privacy", False)
        contact_consent_v = st.session_state.get("contact_consent", False)

        if email_raw and not validated_email:
            st.session_state.field_errors = {"email": t("err_email")}
            st.session_state["step"] = 1
            st.session_state.scroll_target = "anchor_email"
            st.rerun()

        full_name = f"{first_name_clean} {last_name_clean}".strip()
        patient_initials = initials(full_name)
        submitted_at = datetime.now().strftime("%d.%m.%Y, %H:%M")

        nationality = _g("nationality")
        sex = _sex_s
        sex_other = _g("sex_other") if sex == "inne" else ""
        current_status = _g("current_status")
        current_status_other = _g("current_status_other") if current_status == "inne" else ""
        profession = _g("profession")
        height_cm = parse_optional_float(_g("height_cm_text"))
        weight_kg = parse_optional_float(_g("weight_kg_text"))
        bmi = bmi_calc(weight_kg, height_cm)
        physical_score = _g("physical_score", 5)
        mental_score = _g("mental_score", 5)
        weight_change = _g("weight_change")
        _wca = _g("weight_change_amount_num")
        weight_change_amount = str(_wca) if _wca not in (None, "") else ""
        performed_tests = _gl("performed_tests")
        _scount = _g("symptom_count", 1)
        additional_symptoms = _g("additional_symptoms")
        symptom_pattern = _g("symptom_pattern")
        symptom_periodicity = _g("symptom_periodicity")
        symptom_past = _g("symptom_past")
        worsening_factors = _gl("worsening_factors")
        worsening_other = _g("worsening_other") if "inne" in worsening_factors else ""
        improvement_factors = _gl("improvement_factors")
        improvement_other = _g("improvement_other") if "inne" in improvement_factors else ""
        health_timeline = _g("health_timeline")
        current_meds = _g("current_meds")
        lifestyle = _g("lifestyle")
        lifestyle_other = _g("lifestyle_other") if lifestyle == "inne" else ""
        stimulants = _gl("stimulants")
        stimulants_other = _g("stimulants_other") if "inne" in stimulants else ""
        sleep_hours = _g("sleep_hours")
        travel_abroad = _g("travel_abroad")
        travel_where = _g("travel_where") if travel_abroad == "tak" else ""
        animal_contact = _g("animal_contact")
        animal_contact_details = _g("animal_contact_details") if animal_contact == "tak" else ""
        major_injuries = _g("major_injuries")
        covid = _g("covid")
        covid_details = _g("covid_details") if covid == "tak" else ""
        strong_stress = _g("strong_stress")
        birth_delivery = _g("birth_delivery")
        birth_delivery_other = _g("birth_delivery_other") if birth_delivery == "inne" else ""
        birth_timing = _g("birth_timing")
        birth_timing_other = _g("birth_timing_other") if birth_timing == "inne" else ""
        green_water = _g("green_water")
        birth_info_other = _g("birth_info_other")
        breastfeeding = _g("breastfeeding")
        childhood_diseases = _gl("childhood_diseases")
        childhood_diseases_other = _g("childhood_diseases_other") if "inne" in childhood_diseases else ""
        fever_now = _g("fever_now")
        fever_details = _g("fever_details") if fever_now == "tak" else ""
        headache_dizziness = _g("headache_dizziness")
        headache_dizziness_details = _g("headache_dizziness_details") if headache_dizziness == "tak" else ""
        headache_assoc = _g("headache_assoc")
        hearing_vision = _g("hearing_vision")
        attacks = _g("attacks")
        sinus_problems = _g("sinus_problems")
        nose_problems = _g("nose_problems")
        allergies = _g("allergies")
        herpes = _g("herpes")
        mouth_corners = _g("mouth_corners")
        fresh_food_reaction = _g("fresh_food_reaction")
        epilepsy = _g("epilepsy")
        smell_taste = _g("smell_taste")
        colds = _g("colds")
        throat_morning = _g("throat_morning")
        esophagus_burning = _g("esophagus_burning")
        asthma_dx = _g("asthma_dx")
        pneumonia = _g("pneumonia")
        pneumonia_details = _g("pneumonia_details") if pneumonia == "tak" else ""
        dyspnea = _g("dyspnea")
        night_breath = _g("night_breath")
        chest_heaviness = _g("chest_heaviness")
        breathing_type = _g("breathing_type")
        wheezing = _gl("wheezing")
        cough = _g("cough")
        chest_pain = _g("chest_pain")
        pressure_type = _g("pressure_type")
        current_bp = _g("current_bp")
        current_hr = _g("current_hr")
        pain_press = _g("pain_press")
        pain_position = _g("pain_position")
        palpitations = _g("palpitations")
        gi_problem = _g("gi_problem")
        gi_symptoms = _gl("gi_symptoms") if gi_problem == "tak" else []
        worsening_foods = _g("worsening_foods")
        gi_infections = _g("gi_infections")
        urine_problems = _g("urine_problems")
        night_urination = _g("night_urination")
        fluids = _g("fluids")
        joints = _g("joints")
        stiffness = _g("stiffness")
        skin_changes = _g("skin_changes")
        skin_itch = _g("skin_itch")
        acne = _g("acne")
        acne_details = _g("acne_details") if acne == "tak" else ""
        skin_sensation = _g("skin_sensation")
        wound_healing = _g("wound_healing")
        wound_healing_details = _g("wound_healing_details") if wound_healing == "tak" else ""
        sleep_problem = _g("sleep_problem")
        sleep_problem_types = _gl("sleep_problem_types") if sleep_problem == "tak" else []
        psych_contact = _g("psych_contact")
        psych_dx = _g("psych_dx")
        edema = _g("edema")
        edema_details = _g("edema_details") if edema == "tak" else ""
        calf_pain = _g("calf_pain")
        cold_fingers = _g("cold_fingers")
        tingling = _g("tingling")
        varicose = _g("varicose")
        anal_problems = _gl("anal_problems")
        anal_other = _g("anal_other") if "inne" in anal_problems else ""
        gyn_problems = _g("gyn_problems") if sex in ("kobieta", "inne", "") else ""
        menstruation = _g("menstruation") if sex == "kobieta" else ""
        first_menses = _g("first_menses") if sex == "kobieta" else ""
        last_menses_text = _g("last_menses_text") if sex == "kobieta" else ""
        potency = _g("potency") if sex in ("mężczyzna", "inne", "") else ""
        mother_history = _g("mother_history")
        father_history = _g("father_history")
        maternal_grandmother = _g("maternal_grandmother")
        paternal_grandmother = _g("paternal_grandmother")
        maternal_grandfather = _g("maternal_grandfather")
        paternal_grandfather = _g("paternal_grandfather")
        own_diagnoses = _g("own_diagnoses")
        important_info = _g("important_info")
        current_reason = _g("current_reason")
        key_question = _g("key_question")
        last_menses = parse_polish_date(last_menses_text) if last_menses_text else None

        main_symptom_rows = []
        for _si in range(1, _scount + 1):
            _sym = _g(f"symptom_{_si}")
            _sym_since = _g(f"symptom_{_si}_since")
            if nonempty(_sym):
                main_symptom_rows.append(f"{_si}. {_sym}" + (f" - od {_sym_since}" if nonempty(_sym_since) else ""))

        pdf_data = {
            "full_name": full_name,
            "initials": patient_initials,
            "phone": validated_phone,
            "birth_date": birth_date.strftime("%d.%m.%Y") if birth_date else "",
            "submitted_at": submitted_at,
            "sec_basic": [
                f"Płeć: {sex_other if nonempty(sex_other) else sex}" if nonempty(sex) else "",
                f"Narodowość: {nationality}" if nonempty(nationality) else "",
                f"Aktualny status: {current_status_other if nonempty(current_status_other) else current_status}" if nonempty(current_status) else "",
                f"Zawód: {profession}" if nonempty(profession) else "",
                f"Wzrost: {height_cm:.0f} cm" if height_cm is not None else "",
                f"Masa ciała: {weight_kg:.1f} kg" if weight_kg is not None else "",
                f"BMI: {bmi:.1f} ({bmi_label(bmi)})" if bmi is not None else "",
            ],
            "sec_overall": [
                f"Ocena stanu fizycznego: {physical_score}/10",
                f"Ocena stanu psychicznego: {mental_score}/10",
                f"Zmiana masy ciała: {weight_change}" + (f", {weight_change_amount}" if nonempty(weight_change_amount) else "") if nonempty(weight_change) else "",
            ],
            "sec_tests": [f"• {x}" for x in performed_tests],
            "sec_main_symptoms": main_symptom_rows,
            "sec_other_symptoms": [additional_symptoms],
            "sec_symptom_character": [
                f"Objawy: {symptom_pattern}" if nonempty(symptom_pattern) else "",
                f"Okresowość: {symptom_periodicity}" if nonempty(symptom_periodicity) else "",
                f"Czy występowały wcześniej: {symptom_past}" if nonempty(symptom_past) else "",
                f"Co powoduje pogorszenie objawów: {list_text(worsening_factors)}" if worsening_factors else "",
                f"Inne przyczyny pogorszenia objawów: {worsening_other}" if nonempty(worsening_other) else "",
                f"Co powoduje poprawę lub zmniejszenie objawów: {list_text(improvement_factors)}" if improvement_factors else "",
                f"Inne przyczyny poprawy objawów: {improvement_other}" if nonempty(improvement_other) else "",
            ],
            "sec_timeline_meds": [
                f"Chronologia zdrowia: {health_timeline}" if nonempty(health_timeline) else "",
                "Aktualnie przyjmowane leki:" if nonempty(current_meds) else "",
                *lines_from_text(current_meds),
            ],
            "sec_lifestyle": [
                f"Tryb życia: {lifestyle_other if nonempty(lifestyle_other) else lifestyle}" if nonempty(lifestyle) else "",
                f"Używki i nawyki: {list_text(stimulants)}" if stimulants else "",
                f"Inne używki lub nawyki: {stimulants_other}" if nonempty(stimulants_other) else "",
                f"Sen: {sleep_hours} godzin na dobę" if nonempty(sleep_hours) else "",
            ],
            "sec_travel": [
                f"Wyjazd za granicę w ostatnich 3 miesiącach: {travel_abroad}" + (f", {travel_where}" if nonempty(travel_where) else "") if nonempty(travel_abroad) else ""
            ],
            "sec_animals": [
                f"Pogryzienie, zadrapanie lub bliski kontakt ze zwierzęciem: {animal_contact}" + (f", {animal_contact_details}" if nonempty(animal_contact_details) else "") if nonempty(animal_contact) else ""
            ],
            "sec_injuries": [f"Duże urazy: {major_injuries}" if nonempty(major_injuries) else ""],
            "sec_covid": [
                f"Zachorowanie na COVID-19: {covid}" + (f", {covid_details}" if nonempty(covid_details) else "") if nonempty(covid) else ""
            ],
            "sec_stress": [f"Silne reakcje stresowe: {strong_stress}" if nonempty(strong_stress) else ""],
            "sec_birth_childhood": [
                f"Sposób porodu: {birth_delivery_other if nonempty(birth_delivery_other) else birth_delivery}" if nonempty(birth_delivery) else "",
                f"Czas porodu: {birth_timing_other if nonempty(birth_timing_other) else birth_timing}" if nonempty(birth_timing) else "",
                f"Zielone wody płodowe: {green_water}" if nonempty(green_water) else "",
                f"Inne informacje o urodzeniu: {birth_info_other}" if nonempty(birth_info_other) else "",
                f"Karmienie mlekiem matki: {breastfeeding}" if nonempty(breastfeeding) else "",
                f"Choroby dzieciństwa: {list_text(childhood_diseases)}" if childhood_diseases else "",
                f"Inne choroby dzieciństwa: {childhood_diseases_other}" if nonempty(childhood_diseases_other) else "",
            ],
            "sec_general_neuro": [
                f"Gorączka: {fever_now}" + (f", {fever_details}" if nonempty(fever_details) else "") if nonempty(fever_now) else "",
                f"Bóle lub zawroty głowy: {headache_dizziness}" + (f", {headache_dizziness_details}" if nonempty(headache_dizziness_details) else "") if nonempty(headache_dizziness) else "",
                f"Objawy towarzyszące bólom głowy: {headache_assoc}" if nonempty(headache_assoc) else "",
                f"Słuch lub wzrok: {hearing_vision}" if nonempty(hearing_vision) else "",
                f"Ataki lub nagłe epizody: {attacks}" if nonempty(attacks) else "",
                f"Problemy z zatokami: {sinus_problems}" if nonempty(sinus_problems) else "",
                f"Problemy z nosem: {nose_problems}" if nonempty(nose_problems) else "",
                f"Alergie: {allergies}" if nonempty(allergies) else "",
                f"Opryszczka: {herpes}" if nonempty(herpes) else "",
                f"Zajady: {mouth_corners}" if nonempty(mouth_corners) else "",
                f"Reakcja po świeżych warzywach i owocach: {fresh_food_reaction}" if nonempty(fresh_food_reaction) else "",
                f"Padaczka: {epilepsy}" if nonempty(epilepsy) else "",
                f"Zaburzenia węchu lub smaku: {smell_taste}" if nonempty(smell_taste) else "",
                f"Częstość przeziębień: {colds}" if nonempty(colds) else "",
            ],
            "sec_respiratory": [
                f"Ból gardła rano: {throat_morning}" if nonempty(throat_morning) else "",
                f"Pieczenie w przełyku: {esophagus_burning}" if nonempty(esophagus_burning) else "",
                f"Rozpoznana astma: {asthma_dx}" if nonempty(asthma_dx) else "",
                f"Zapalenie płuc: {pneumonia}" + (f", {pneumonia_details}" if nonempty(pneumonia_details) else "") if nonempty(pneumonia) else "",
                f"Duszność lub zadyszka: {dyspnea}" if nonempty(dyspnea) else "",
                f"Wybudzanie w nocy z powodu braku tchu: {night_breath}" if nonempty(night_breath) else "",
                f"Ciężkość w klatce piersiowej: {chest_heaviness}" if nonempty(chest_heaviness) else "",
                f"Trudności z oddychaniem: {breathing_type}" if nonempty(breathing_type) else "",
                f"Świszczący oddech: {list_text(wheezing)}" if wheezing else "",
                f"Kaszel: {cough}" if nonempty(cough) else "",
            ],
            "sec_cardio": [
                f"Bóle w klatce piersiowej: {chest_pain}" if nonempty(chest_pain) else "",
                f"Problemy z ciśnieniem: {pressure_type}" if nonempty(pressure_type) else "",
                f"Aktualne ciśnienie: {current_bp}" if nonempty(current_bp) else "",
                f"Aktualne tętno: {current_hr}" if nonempty(current_hr) else "",
                f"Ból przy nacisku na klatkę piersiową: {pain_press}" if nonempty(pain_press) else "",
                f"Ból przy zmianie pozycji: {pain_position}" if nonempty(pain_position) else "",
                f"Nierówne bicie serca: {palpitations}" if nonempty(palpitations) else "",
            ],
            "sec_gi": [
                f"Problemy z przewodem pokarmowym: {gi_problem}" if nonempty(gi_problem) else "",
                f"Objawy: {list_text(gi_symptoms)}" if gi_symptoms else "",
                f"Potrawy pogarszające stan: {worsening_foods}" if nonempty(worsening_foods) else "",
                f"Przebyte infekcje przewodu pokarmowego: {gi_infections}" if nonempty(gi_infections) else "",
            ],
            "sec_urinary": [
                f"Problemy z oddawaniem moczu: {urine_problems}" if nonempty(urine_problems) else "",
                f"Liczba mikcji nocnych: {night_urination}" if nonempty(night_urination) else "",
                f"Ilość wypijanych płynów dziennie: {fluids} l" if nonempty(fluids) else "",
            ],
            "sec_msk": [
                f"Bóle stawów: {joints}" if nonempty(joints) else "",
                f"Sztywność po wstaniu z łóżka: {stiffness}" if nonempty(stiffness) else "",
            ],
            "sec_skin": [
                f"Zmiany skórne: {skin_changes}" if nonempty(skin_changes) else "",
                f"Świąd skóry: {skin_itch}" if nonempty(skin_itch) else "",
                f"Trądzik: {acne}" + (f", {acne_details}" if nonempty(acne_details) else "") if nonempty(acne) else "",
                f"Zaburzenia czucia skóry: {skin_sensation}" if nonempty(skin_sensation) else "",
                f"Problemy z gojeniem ran: {wound_healing}" + (f", {wound_healing_details}" if nonempty(wound_healing_details) else "") if nonempty(wound_healing) else "",
            ],
            "sec_sleep_psych": [
                f"Problemy ze snem: {sleep_problem}" if nonempty(sleep_problem) else "",
                f"Rodzaj problemów ze snem: {list_text(sleep_problem_types)}" if sleep_problem_types else "",
                f"Kontakt z psychologiem lub psychiatrą: {psych_contact}" if nonempty(psych_contact) else "",
                f"Rozpoznana choroba psychiczna: {psych_dx}" if nonempty(psych_dx) else "",
            ],
            "sec_peripheral": [
                f"Obrzęki: {edema}" + (f", {edema_details}" if nonempty(edema_details) else "") if nonempty(edema) else "",
                f"Bóle łydek podczas chodzenia: {calf_pain}" if nonempty(calf_pain) else "",
                f"Zimne palce lub zmiana koloru: {cold_fingers}" if nonempty(cold_fingers) else "",
                f"Mrowienie lub drętwienie: {tingling}" if nonempty(tingling) else "",
                f"Żylaki: {varicose}" if nonempty(varicose) else "",
            ],
            "sec_anal": [
                f"Problemy w okolicy odbytu: {list_text(anal_problems)}" if anal_problems else "",
                f"Inne problemy w okolicy odbytu: {anal_other}" if nonempty(anal_other) else "",
            ],
            "sec_sex_specific": [
                f"Problemy ginekologiczne: {gyn_problems}" if nonempty(gyn_problems) else "",
                f"Miesiączka, menopauza, leczenie hormonalne: {menstruation}" if nonempty(menstruation) else "",
                f"Pierwsza miesiączka: {first_menses}" if nonempty(first_menses) else "",
                f"Ostatnia miesiączka: {safe(last_menses)}" if last_menses else "",
                f"Problemy z potencją: {potency}" if nonempty(potency) else "",
            ],
            "sec_family": [
                f"Mama: {mother_history}" if nonempty(mother_history) else "",
                f"Ojciec: {father_history}" if nonempty(father_history) else "",
                f"Babcia ze strony mamy: {maternal_grandmother}" if nonempty(maternal_grandmother) else "",
                f"Babcia ze strony ojca: {paternal_grandmother}" if nonempty(paternal_grandmother) else "",
                f"Dziadek ze strony mamy: {maternal_grandfather}" if nonempty(maternal_grandfather) else "",
                f"Dziadek ze strony ojca: {paternal_grandfather}" if nonempty(paternal_grandfather) else "",
            ],
            "sec_history_final": [
                f"Dotychczasowe rozpoznania i operacje: {own_diagnoses}" if nonempty(own_diagnoses) else "",
                f"Ważne informacje dla lekarza: {important_info}" if nonempty(important_info) else "",
                f"Powód obecnych dolegliwości: {current_reason}" if nonempty(current_reason) else "",
            ],
            "sec_question": [key_question],
        }

        email_body = f"""Nowy formularz pacjenta został wysłany.

Imię i nazwisko: {full_name}
Telefon kontaktowy: {validated_phone}
Adres e-mail: {validated_email or ""}
Data urodzenia: {birth_date.strftime("%d.%m.%Y") if birth_date else ""}
Data i godzina wypełnienia formularza: {submitted_at}
Zgoda na kontakt organizacyjny: {"tak" if contact_consent_v else "nie"}
"""

        _status = st.empty()
        _status.info(t("sending"))
        pdf_path = None
        try:
            pdf_path = make_pdf(pdf_data)
            date_slug = datetime.now().strftime("%Y-%m-%d")
            safe_initials = patient_initials.replace(" ", "_").replace(".", "")
            pdf_filename = f"wywiad_{safe_initials}_{date_slug}.pdf"
            send_email_with_pdf(
                subject=f"Nowy formularz pacjenta - {full_name}",
                body_text=email_body,
                pdf_path=pdf_path,
                filename=pdf_filename,
            )
            _status.empty()
            st.session_state.field_errors = {}
            st.session_state.scroll_target = None
            st.session_state["form_success"] = True
            _delete_draft(_sid)
            for _k in _FORM_KEYS:
                st.session_state.pop(_k, None)
            st.session_state["_form_data"] = {}
            st.session_state["step"] = 1
            if validated_email:
                try:
                    send_confirmation_to_patient(validated_email, full_name, _lang)
                except Exception as _mail_err:
                    st.warning(f"Formularz wysłany, ale nie udało się wysłać potwierdzenia na e-mail pacjenta: {_mail_err}")
            st.rerun()
        except Exception as e:
            _status.empty()
            st.error(f"Nie udało się wysłać formularza. Szczegóły: {e}")
        finally:
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except Exception:
                    pass

# =========================================================
# NAWIGACJA
# =========================================================
if not _has_form_nav:
    st.markdown("---")
    _nav_l, _nav_r = st.columns(2)
    with _nav_l:
        if step > 1:
            if st.button("← Wstecz" if _lang == "pl" else "← Back", key="btn_back", type="primary"):
                st.session_state.field_errors = {}
                st.session_state.scroll_target = None
                st.session_state["step"] -= 1
                st.rerun()
    with _nav_r:
        if step < TOTAL_STEPS:
            if st.button("Dalej →" if _lang == "pl" else "Next →", key="btn_next"):
                if step == 1:
                    _errs1 = {}
                    _em1 = st.session_state.get("email", "")
                    if _em1 and not validate_email(_em1):
                        _errs1["email"] = t("err_email")
                    if _errs1:
                        st.session_state.field_errors = _errs1
                        st.session_state.scroll_target = "anchor_email"
                        st.rerun()
                    else:
                        st.session_state.field_errors = {}
                        st.session_state.scroll_target = None
                        st.session_state["step"] += 1
                        st.rerun()
                else:
                    st.session_state["step"] += 1
                    st.rerun()

# =========================================================
# PRZEWIJANIE DO BŁĘDU
# =========================================================
if st.session_state.scroll_target:
    scroll_to_anchor(st.session_state.scroll_target)

# Zapisz draft po każdym renderze
if not st.session_state.get("form_success"):
    _save_draft(_sid)
