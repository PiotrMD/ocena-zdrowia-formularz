import os
import re
import smtplib
import tempfile
from datetime import date, datetime
from email.message import EmailMessage
from typing import Any, Dict, List, Optional

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

load_dotenv()

# =========================================================
# KONFIGURACJA STRONY
# =========================================================
st.set_page_config(
    page_title="Ocena stanu zdrowia - wywiad lekarski",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =========================================================
# CSS
# =========================================================
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .main .block-container {
        max-width: 980px;
        padding-top: 0.65rem;
        padding-bottom: 2rem;
    }

    .top-card {
        padding: 18px 18px;
        border-radius: 18px;
        border: 1px solid rgba(120,120,120,0.22);
        margin-bottom: 16px;
        background: rgba(250,250,250,0.03);
    }

    .title-main {
        text-align: center;
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        margin-top: 0.1rem;
        margin-bottom: 0.1rem;
    }

    .title-sub {
        text-align: center;
        font-size: 1.15rem;
        font-weight: 700;
        margin-top: 0;
        margin-bottom: 0.35rem;
    }

    .doctor-line {
        text-align: center;
        font-size: 1rem;
        margin-top: 0;
        margin-bottom: 0.4rem;
    }

    .site-line {
        text-align: center;
        font-size: 1rem;
        margin-top: 0;
        margin-bottom: 0.2rem;
        font-weight: 700;
    }

    .contact-line {
        text-align: center;
        font-size: 0.95rem;
        margin-top: 0;
        margin-bottom: 1rem;
    }

    .progress-box {
        padding: 12px 14px;
        border-radius: 14px;
        border: 1px solid rgba(120,120,120,0.22);
        margin-top: 6px;
        margin-bottom: 16px;
        background: rgba(250,250,250,0.02);
    }

    .send-button > button {
        width: 100%;
        height: 3.25rem;
        font-size: 1.05rem;
        font-weight: 700;
        border-radius: 12px;
    }

    .field-anchor {
        position: relative;
        top: -95px;
        visibility: hidden;
    }

    .field-error-box {
        border: 2px solid #d93025;
        border-radius: 10px;
        padding: 10px 12px;
        color: #d93025;
        background: rgba(217, 48, 37, 0.06);
        font-weight: 600;
        margin-top: -0.15rem;
        margin-bottom: 0.9rem;
    }

    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 0.45rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }

        .title-main {
            font-size: 1.55rem;
        }

        .title-sub {
            font-size: 1rem;
        }

        .doctor-line, .site-line, .contact-line {
            font-size: 0.9rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# SECRETS / ENV
# =========================================================
def get_secret(name: str) -> str:
    value = os.getenv(name)
    if not value:
        st.error(f"Brakuje zmiennej środowiskowej: {name}")
        st.stop()
    return value


EMAIL_NADAWCA = get_secret("EMAIL_NADAWCA")
HASLO_APLIKACJI = get_secret("HASLO_APLIKACJI")
EMAIL_ODBIORCA1 = get_secret("EMAIL_ODBIORCA1")
EMAIL_ODBIORCA2 = get_secret("EMAIL_ODBIORCA2")


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
        format_func=lambda x: "wybierz" if x == "" else x,
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


def make_pdf(data: Dict[str, Any]) -> str:
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
            f"Pacjent: {data['initials']}",
            f"Telefon kontaktowy: {data['phone']}",
            f"Data urodzenia: {data['birth_date']}",
            f"Rodzaj wizyty: {data['visit_type']}",
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


def send_email_with_pdf(subject: str, body_text: str, pdf_path: str):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_NADAWCA
    msg["To"] = EMAIL_NADAWCA
    msg["Bcc"] = f"{EMAIL_ODBIORCA1}, {EMAIL_ODBIORCA2}"
    msg.set_content(body_text)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename="wywiad_lekarski.pdf",
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
# STAN SESJI
# =========================================================
if "field_errors" not in st.session_state:
    st.session_state.field_errors = {}
if "scroll_target" not in st.session_state:
    st.session_state.scroll_target = None

field_errors: Dict[str, str] = st.session_state.field_errors

# =========================================================
# GÓRA APLIKACJI
# =========================================================
progress_placeholder = st.empty()

if os.path.exists("logo.PNG"):
    st.image("logo.PNG", use_container_width=True)
elif os.path.exists("logo.png"):
    st.image("logo.png", use_container_width=True)
elif os.path.exists("Logo OCENA ZDROWIA.PNG"):
    st.image("Logo OCENA ZDROWIA.PNG", use_container_width=True)

st.markdown("<div class='title-main'>OCENA STANU ZDROWIA</div>", unsafe_allow_html=True)
st.markdown("<div class='title-sub'>Wywiad lekarski</div>", unsafe_allow_html=True)
st.markdown("<div class='doctor-line'>dr n. med. Piotr Niedziałkowski</div>", unsafe_allow_html=True)
st.markdown("<div class='site-line'>www.ocenazdrowia.pl</div>", unsafe_allow_html=True)
st.markdown("<div class='contact-line'>W sprawie pytań proszę kontaktować się z recepcją: +48 690 584 584</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="top-card">
    Szanowni Państwo,<br><br>
    każda wizyta jest przygotowywana indywidualnie.<br>
    Bardzo proszę o szczere i możliwie dokładne odpowiedzi dotyczące stanu zdrowia.<br>
    Im więcej szczegółów, tym większa szansa na wcześniejsze wykrycie problemów i trafną ocenę sytuacji zdrowotnej.<br><br>
    W przypadku dzieci proszę o wypełnienie odpowiednich pól.<br><br>
    Dane z formularza nie są zapisywane w bazie aplikacji. Po wysłaniu formularza dokument trafia wyłącznie do lekarza w celu przygotowania wizyty.<br><br>
    Serdecznie pozdrawiam i do zobaczenia na wizycie.
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# FORMULARZ
# =========================================================
with st.form("medical_form"):
    with st.expander("1. Dane podstawowe", expanded=True):
        visit_type = select_with_placeholder("Rodzaj wizyty", ["Pierwsza", "Kontrolna"], key="visit_type")

        st.markdown('<div id="anchor_first_name" class="field-anchor"></div>', unsafe_allow_html=True)
        first_name = st.text_input("Imię", key="first_name")
        if "first_name" in field_errors:
            error_box(field_errors["first_name"])

        st.markdown('<div id="anchor_last_name" class="field-anchor"></div>', unsafe_allow_html=True)
        last_name = st.text_input("Nazwisko", key="last_name")
        if "last_name" in field_errors:
            error_box(field_errors["last_name"])

        st.markdown('<div id="anchor_phone" class="field-anchor"></div>', unsafe_allow_html=True)
        phone = st.text_input(
            "Telefon kontaktowy",
            key="phone",
            help="Może być z numerem kierunkowym albo bez, np. 690584584 lub +48690584584",
        )
        if "phone" in field_errors:
            error_box(field_errors["phone"])

        st.markdown('<div id="anchor_email" class="field-anchor"></div>', unsafe_allow_html=True)
        email = st.text_input("Adres e-mail", key="email")
        if "email" in field_errors:
            error_box(field_errors["email"])

        st.markdown('<div id="anchor_birth_date" class="field-anchor"></div>', unsafe_allow_html=True)
        birth_date_text = st.text_input(
            "Data urodzenia",
            key="birth_date_text",
            help="Najlepiej w formacie DD.MM.RRRR",
        )
        if "birth_date" in field_errors:
            error_box(field_errors["birth_date"])

        nationality = st.text_input("Narodowość", key="nationality")
        sex = select_with_placeholder("Płeć", ["kobieta", "mężczyzna", "inne"], key="sex")
        current_status = select_with_placeholder(
            "Aktualny status",
            ["pracujący", "dziecko", "uczeń", "student", "emeryt", "inne"],
            key="current_status",
        )
        profession = st.text_input("Obecnie wykonywany zawód", key="profession")
        height_cm_text = st.text_input("Wzrost (cm)", key="height_cm_text")
        weight_kg_text = st.text_input("Masa ciała (kg)", key="weight_kg_text")

        height_cm = parse_optional_float(height_cm_text)
        weight_kg = parse_optional_float(weight_kg_text)
        bmi = bmi_calc(weight_kg, height_cm)

        if bmi is not None:
            st.info(f"BMI: {bmi:.1f} ({bmi_label(bmi)})")
        else:
            st.info("BMI: brak danych")

    with st.expander("2. Ocena ogólna"):
        physical_score = select_with_placeholder(
            "Jak oceniasz swój stan fizyczny? 0 = bardzo zły, 10 = bardzo dobry",
            [str(i) for i in range(0, 11)],
            key="physical_score",
        )
        mental_score = select_with_placeholder(
            "Jak oceniasz swój stan psychiczny? 0 = bardzo zły, 10 = bardzo dobry",
            [str(i) for i in range(0, 11)],
            key="mental_score",
        )
        weight_change = select_with_placeholder(
            "Czy w ostatnim roku zmieniła się masa ciała?",
            ["wzrosła", "spadła", "bez zmian"],
            key="weight_change",
        )
        weight_change_amount = ""
        if weight_change in ["wzrosła", "spadła"]:
            weight_change_amount = st.text_input("O ile mniej więcej kilogramów zmieniła się masa ciała?", key="weight_change_amount")

    with st.expander("3. Badania wykonane w ciągu ostatnich 2 lat"):
        performed_tests = st.multiselect(
            "Zaznacz wykonane badania",
            [
                "RTG klatki piersiowej",
                "EKG",
                "Echo serca",
                "Holter EKG",
                "Holter ciśnieniowy",
                "Gastroskopia",
                "Kolonoskopia",
                "USG jamy brzusznej",
                "USG miednicy",
                "USG ginekologiczne",
                "USG tarczycy",
                "USG jąder",
                "USG prostaty",
                "USG piersi",
                "Mammografia",
                "Tomografia komputerowa",
                "Tomografia głowy",
                "Rezonans magnetyczny",
                "Rezonans głowy",
                "Doppler tętnic szyjnych",
                "Przepływy w naczyniach kończyn dolnych",
                "Densytometria",
                "Scyntygrafia",
            ],
            placeholder="Wybierz badania",
            key="performed_tests",
        )

    with st.expander("4. Objawy główne"):
        symptom_1 = st.text_input("Objaw 1", key="symptom_1")
        symptom_1_since = st.text_input("Od kiedy występuje objaw 1?", key="symptom_1_since")
        symptom_2 = st.text_input("Objaw 2", key="symptom_2")
        symptom_2_since = st.text_input("Od kiedy występuje objaw 2?", key="symptom_2_since")
        symptom_3 = st.text_input("Objaw 3", key="symptom_3")
        symptom_3_since = st.text_input("Od kiedy występuje objaw 3?", key="symptom_3_since")
        symptom_4 = st.text_input("Objaw 4", key="symptom_4")
        symptom_4_since = st.text_input("Od kiedy występuje objaw 4?", key="symptom_4_since")
        symptom_5 = st.text_input("Objaw 5", key="symptom_5")
        symptom_5_since = st.text_input("Od kiedy występuje objaw 5?", key="symptom_5_since")
        additional_symptoms = st.text_area("Pozostałe dolegliwości, nawet mniej nasilone", key="additional_symptoms")

    with st.expander("5. Charakter objawów"):
        symptom_pattern = select_with_placeholder(
            "Czy objawy są stałe czy pojawiają się okresowo?",
            ["stałe", "okresowe", "trudno powiedzieć"],
            key="symptom_pattern",
        )
        symptom_periodicity = st.text_area("Jeśli okresowe, napisz kiedy się pojawiają i jak często w ciągu roku", key="symptom_periodicity")
        symptom_past = st.text_area("Czy podobne objawy występowały wcześniej? Jeśli tak, kiedy?", key="symptom_past")

        worsening_factors = st.multiselect(
            "Co powoduje pogorszenie objawów?",
            ["wysiłek", "głód", "posiłek", "mówienie", "śmiech", "inne"],
            placeholder="Wybierz czynniki pogorszenia",
            key="worsening_factors",
        )
        worsening_other = ""
        if "inne" in worsening_factors:
            worsening_other = st.text_input("Jeśli inne, napisz co powoduje pogorszenie objawów", key="worsening_other")

        improvement_factors = st.multiselect(
            "Co powoduje poprawę lub zmniejszenie objawów?",
            ["wypoczynek", "wysiłek", "głód", "posiłek", "inne"],
            placeholder="Wybierz czynniki poprawy",
            key="improvement_factors",
        )
        improvement_other = ""
        if "inne" in improvement_factors:
            improvement_other = st.text_input("Jeśli inne, napisz co powoduje poprawę objawów", key="improvement_other")

    with st.expander("6. Chronologia zdrowia i leki"):
        health_timeline = st.text_area("Opisz przebieg zdrowia od pierwszych problemów zdrowotnych do dziś", key="health_timeline")
        current_meds = st.text_area("Jakie leki obecnie przyjmujesz? Podaj nazwę i dawkowanie. Najlepiej wpisuj każdy lek w osobnej linii.", key="current_meds")

    with st.expander("7. Tryb życia"):
        lifestyle = select_with_placeholder(
            "Tryb życia",
            ["leżący", "siedzący", "nisko aktywny", "średnio aktywny", "bardzo aktywny", "inne"],
            key="lifestyle",
        )
        stimulants = st.multiselect(
            "Używki i codzienne nawyki",
            ["kawa", "herbata", "papierosy", "alkohol", "narkotyki", "słodycze", "inne"],
            placeholder="Wybierz używki i nawyki",
            key="stimulants",
        )
        stimulants_other = ""
        if "inne" in stimulants:
            stimulants_other = st.text_input("Jeśli zaznaczono inne, napisz jakie", key="stimulants_other")
        sleep_hours = select_with_placeholder("Ile średnio trwa sen na dobę?", ["3", "4", "5", "6", "7", "8", "9", "10", "11", "12"], key="sleep_hours")

    with st.expander("8. Podróże"):
        travel_abroad = yes_no("Czy w ciągu ostatnich 3 miesięcy był wyjazd za granicę?", key="travel_abroad")
        travel_where = ""
        if travel_abroad == "tak":
            travel_where = st.text_input("Jeśli tak, to gdzie?", key="travel_where")

    with st.expander("9. Zwierzęta"):
        animal_contact = yes_no("Czy w ostatnich miesiącach było pogryzienie, zadrapanie lub bliski kontakt ze zwierzęciem?", key="animal_contact")
        animal_contact_details = ""
        if animal_contact == "tak":
            animal_contact_details = st.text_area("Jeśli tak, opisz kiedy i jakie zwierzę", key="animal_contact_details")

    with st.expander("10. Urazy"):
        major_injuries = st.text_area("Czy były duże urazy ciała? Podaj rok i opisz, np. upadek z wysokości, uraz komunikacyjny, pobicie, tonięcie, operacja", key="major_injuries")

    with st.expander("11. COVID-19"):
        covid = yes_no_unknown("Czy i kiedy wystąpiło zachorowanie na COVID-19?", key="covid")
        covid_details = ""
        if covid == "tak":
            covid_details = st.text_area("Jeśli tak, opisz kiedy i jaki był przebieg", key="covid_details")

    with st.expander("12. Stres"):
        strong_stress = st.text_area("Czy w ciągu życia były silne reakcje stresowe lub trudne wydarzenia? Jeśli tak, opisz i podaj rok", key="strong_stress")

    with st.expander("13. Urodzenie i dzieciństwo"):
        birth_delivery = select_with_placeholder(
            "Sposób porodu",
            ["poród naturalny", "poród przez cesarskie cięcie", "nie wiem", "inne"],
            key="birth_delivery",
        )
        birth_timing = select_with_placeholder(
            "Czas porodu",
            ["poród przedwczesny", "poród o czasie", "poród po terminie", "nie wiem", "inne"],
            key="birth_timing",
        )
        green_water = yes_no_unknown("Czy były zielone wody płodowe?", key="green_water")
        birth_info_other = st.text_input("Inne informacje o urodzeniu", key="birth_info_other")

        breastfeeding = select_with_placeholder(
            "Czy było karmienie mlekiem matki?",
            ["tak, do 3 miesięcy", "tak, do 6 miesięcy", "tak, powyżej 6 miesięcy", "nie", "nie wiem"],
            key="breastfeeding",
        )
        childhood_diseases = st.multiselect(
            "Poważne choroby w dzieciństwie",
            ["astma", "atopowe zapalenie skóry", "skaza białkowa", "częste przeziębienia", "pobyty w szpitalu", "częste zapalenia płuc", "problemy jelitowe", "choroby psychiczne", "problemy ze śledzioną", "problemy z trzustką", "inne"],
            placeholder="Wybierz choroby dzieciństwa",
            key="childhood_diseases",
        )
        childhood_diseases_other = ""
        if "inne" in childhood_diseases:
            childhood_diseases_other = st.text_input("Jeśli zaznaczono inne, napisz jakie", key="childhood_diseases_other")

    with st.expander("14. Objawy ogólne i neurologiczne"):
        fever_now = yes_no("Czy aktualnie występuje gorączka?", key="fever_now")
        fever_details = ""
        if fever_now == "tak":
            fever_details = st.text_area("Jeśli tak, opisz dokładniej", key="fever_details")

        headache_dizziness = yes_no("Czy występują bóle i zawroty głowy?", key="headache_dizziness")
        headache_dizziness_details = ""
        if headache_dizziness == "tak":
            headache_dizziness_details = st.text_area("Jeśli tak, opisz dokładniej", key="headache_dizziness_details")

        headache_assoc = st.text_area("Czy bólom głowy towarzyszą wymioty, omdlenia, zaburzenia widzenia, osłabienie, światłowstręt, niepamięć?", key="headache_assoc")
        hearing_vision = st.text_area("Czy w ostatnich latach pogorszył się słuch lub wzrok?", key="hearing_vision")
        attacks = st.text_area("Czy występują ataki lub nagłe epizody? Jeśli tak, opisz.", key="attacks")
        sinus_problems = st.text_area("Czy występują problemy z zatokami?", key="sinus_problems")
        nose_problems = st.text_area("Czy są problemy z nosem, np. krwawienia, suchość, zapalenia, trudności w oddychaniu przez nos?", key="nose_problems")
        allergies = st.text_area("Czy występują alergie? Jeśli tak, na co, o jakiej porze roku i jak nasilone?", key="allergies")
        herpes = st.text_area("Czy pojawia się opryszczka? Jeśli tak, jak często?", key="herpes")
        mouth_corners = st.text_area("Czy występują zajady?", key="mouth_corners")
        fresh_food_reaction = st.text_area("Czy po spożyciu świeżych warzyw i owoców pojawia się pieczenie lub zaczerwienienie wokół ust?", key="fresh_food_reaction")
        epilepsy = yes_no("Czy kiedykolwiek rozpoznano padaczkę?", key="epilepsy")
        smell_taste = st.text_area("Czy są zaburzenia węchu lub smaku? Jeśli tak, od kiedy?", key="smell_taste")
        colds = st.text_input("Jak często zdarzają się przeziębienia w ciągu roku?", key="colds")

    with st.expander("15. Układ oddechowy"):
        throat_morning = yes_no("Czy rano występuje ból gardła?", key="throat_morning")
        esophagus_burning = yes_no("Czy pojawia się pieczenie w przełyku?", key="esophagus_burning")
        asthma_dx = yes_no("Czy kiedykolwiek rozpoznano astmę?", key="asthma_dx")
        pneumonia = yes_no("Czy kiedykolwiek było zapalenie płuc?", key="pneumonia")
        pneumonia_details = ""
        if pneumonia == "tak":
            pneumonia_details = st.text_area("Jeśli tak, podaj daty i po której stronie płuc było zapalenie", key="pneumonia_details")
        dyspnea = st.text_area("Czy zdarza się duszność lub zadyszka? Jeśli tak, opisz w jakich sytuacjach.", key="dyspnea")
        night_breath = st.text_area("Czy dochodzi do wybudzania w nocy z powodu braku tchu?", key="night_breath")
        chest_heaviness = st.text_area("Czy występuje ciężkość w klatce piersiowej? Jeśli tak, opisz nasilenie.", key="chest_heaviness")
        breathing_type = select_with_placeholder(
            "Czy są trudności z oddychaniem?",
            ["nie mam takich trudności", "z nabieraniem powietrza", "z wypuszczaniem powietrza", "z oboma"],
            key="breathing_type",
        )
        wheezing = st.multiselect(
            "Czy występuje świszczący oddech?",
            ["podczas wysiłku", "podczas infekcji", "w nocy", "rano", "podczas alergii", "w zimnej pogodzie"],
            placeholder="Wybierz okoliczności świszczącego oddechu",
            key="wheezing",
        )
        cough = st.text_area("Czy jest kaszel? Jeśli tak, od kiedy, czy jest suchy czy z wydzieliną, jakiego koloru?", key="cough")

    with st.expander("16. Układ sercowo-naczyniowy"):
        chest_pain = st.text_area("Czy występują bóle w klatce piersiowej? Czy są miejscowe czy rozległe? Czy promieniują?", key="chest_pain")
        pressure_type = select_with_placeholder(
            "Czy są problemy z ciśnieniem?",
            ["nie mam kłopotów z ciśnieniem", "mam skłonność do niskiego ciśnienia", "mam skłonność do wysokiego ciśnienia"],
            key="pressure_type",
        )
        current_bp = st.text_input("Jakie jest aktualne ciśnienie tętnicze?", key="current_bp")
        current_hr = st.text_input("Jakie jest aktualne tętno?", key="current_hr")
        pain_press = yes_no("Czy odczuwasz ból przy naciskaniu klatki piersiowej?", key="pain_press")
        pain_position = yes_no("Czy przy zmianie pozycji występują bóle w klatce piersiowej?", key="pain_position")
        palpitations = st.text_area("Czy odczuwasz nierówne bicie serca? Jeśli tak, opisz porę dnia, okoliczności i częstość.", key="palpitations")

    with st.expander("17. Przewód pokarmowy"):
        gi_problem = yes_no("Czy występują problemy z przewodem pokarmowym?", key="gi_problem")
        gi_symptoms = []
        if gi_problem == "tak":
            gi_symptoms = st.multiselect(
                "Zaznacz problemy",
                ["zgaga", "wzdęcia", "biegunki", "zaparcia", "hemoroidy", "gazy", "skurcze", "wymioty", "nudności"],
                placeholder="Wybierz objawy przewodu pokarmowego",
                key="gi_symptoms",
            )
        worsening_foods = st.text_area("Czy są potrawy, po których samopoczucie się pogarsza?", key="worsening_foods")
        gi_infections = st.text_area("Czy kiedykolwiek było zakażenie bakteryjne lub wirusowe przewodu pokarmowego? Jeśli tak, kiedy i czy było badanie kontrolne z wynikiem ujemnym?", key="gi_infections")

    with st.expander("18. Układ moczowy"):
        urine_problems = st.text_area("Czy są problemy z oddawaniem moczu, np. pieczenie, trudności, inne?", key="urine_problems")
        night_urination = select_with_placeholder("Ile razy w nocy wstajesz oddać mocz?", ["0", "1", "2", "3", "4", "5", "6", "7 lub więcej"], key="night_urination")
        fluids = select_with_placeholder("Ile litrów płynów wypijasz dziennie?", ["1", "2", "3", "4", "5", "więcej niż 5"], key="fluids")

    with st.expander("19. Stawy i mięśnie"):
        joints = st.text_area("Czy występują bóle stawów? Jeśli tak, to których?", key="joints")
        stiffness = st.text_area("Czy po wstaniu z łóżka występuje ból lub sztywność stawów?", key="stiffness")

    with st.expander("20. Skóra"):
        skin_changes = st.text_area("Czy są jakieś zmiany na skórze? Jeśli tak, opisz dokładnie. Kiedy pojawiły się pierwszy raz? Czy od tej pory jest poprawa lub pogorszenie?", key="skin_changes")
        skin_itch = st.text_area("Czy występuje swędzenie skóry? Jeśli tak, których partii ciała dotyczy?", key="skin_itch")
        acne = yes_no("Czy występował lub występuje nasilony trądzik na twarzy lub plecach?", key="acne")
        acne_details = ""
        if acne == "tak":
            acne_details = st.text_area("Jeśli tak, możesz opisać dokładniej", key="acne_details")
        skin_sensation = st.text_area("Czy są zaburzenia czucia skóry? Jeśli tak, opisz lokalizację i od kiedy.", key="skin_sensation")
        wound_healing = yes_no("Czy występują problemy z gojeniem się ran?", key="wound_healing")
        wound_healing_details = ""
        if wound_healing == "tak":
            wound_healing_details = st.text_area("Jeśli tak, opisz problemy z gojeniem", key="wound_healing_details")

    with st.expander("21. Sen i psychika"):
        sleep_problem = yes_no("Czy są problemy ze snem?", key="sleep_problem")
        sleep_problem_types = []
        if sleep_problem == "tak":
            sleep_problem_types = st.multiselect(
                "Jakie problemy ze snem występują?",
                ["trudności z zasypianiem", "wybudzanie w nocy", "wstawanie zmęczony lub zmęczona", "chrapanie", "zbyt krótki sen", "bardzo głęboki sen"],
                placeholder="Wybierz rodzaj problemów ze snem",
                key="sleep_problem_types",
            )
        psych_contact = select_with_placeholder("Czy kiedykolwiek była porada psychologa lub psychiatry?", ["nie", "psycholog", "psychiatra", "oba"], key="psych_contact")
        psych_dx = st.text_area("Czy kiedykolwiek rozpoznano chorobę psychiczną? Jeśli tak, napisz jaką.", key="psych_dx")

    with st.expander("22. Krążenie obwodowe"):
        edema = yes_no("Czy pojawiają się obrzęki na podudziach lub kostkach?", key="edema")
        edema_details = ""
        if edema == "tak":
            edema_details = st.text_area("Jeśli tak, napisz czy występują stale czy po staniu, siedzeniu lub w innych sytuacjach.", key="edema_details")
        calf_pain = st.text_area("Czy występują bóle łydek podczas chodzenia? Jeśli tak, po jakim dystansie i po jakim czasie ustępują?", key="calf_pain")
        cold_fingers = st.text_area("Czy palce rąk lub nóg łatwo stają się zimne lub zmieniają kolor?", key="cold_fingers")
        tingling = st.text_area("Czy występuje mrowienie lub drętwienie rąk lub nóg?", key="tingling")
        varicose = st.text_area("Czy są obecne żylaki?", key="varicose")

    with st.expander("23. Odbyt i okolice odbytu"):
        anal_problems = st.multiselect(
            "Czy występują problemy ze śluzówką odbytu?",
            ["hemoroidy", "stany zapalne błony śluzowej odbytu", "pieczenie", "świąd", "grzybica", "inne"],
            placeholder="Wybierz problemy w okolicy odbytu",
            key="anal_problems",
        )
        anal_other = ""
        if "inne" in anal_problems:
            anal_other = st.text_input("Jeśli zaznaczono inne, opisz", key="anal_other")

    with st.expander("24. Ginekologia lub andrologia"):
        gyn_problems = ""
        menstruation = ""
        first_menses = ""
        last_menses_text = ""
        potency = ""

        if sex == "kobieta":
            gyn_problems = st.text_area("Czy występują problemy ginekologiczne?", key="gyn_problems")
            menstruation = st.text_area("Czy występuje nieregularna miesiączka, menopauza lub leczenie hormonalne? Jeśli tak, napisz od kiedy.", key="menstruation")
            first_menses = st.text_input("Podaj miesiąc i rok pierwszej miesiączki", key="first_menses")
            last_menses_text = st.text_input("Data ostatniej miesiączki", key="last_menses_text", help="Najlepiej w formacie DD.MM.RRRR")
        elif sex == "mężczyzna":
            potency = select_with_placeholder("Czy są problemy z potencją?", ["nie", "czasami", "często"], key="potency")

    with st.expander("25. Wywiad rodzinny"):
        mother_history = st.text_area("Na jakie choroby choruje lub chorowała mama?", key="mother_history")
        father_history = st.text_area("Na jakie choroby choruje lub chorował ojciec?", key="father_history")
        maternal_grandmother = st.text_area("Na jakie choroby choruje lub chorowała babcia ze strony mamy?", key="maternal_grandmother")
        paternal_grandmother = st.text_area("Na jakie choroby choruje lub chorowała babcia ze strony ojca?", key="paternal_grandmother")
        maternal_grandfather = st.text_area("Na jakie choroby choruje lub chorował dziadek ze strony mamy?", key="maternal_grandfather")
        paternal_grandfather = st.text_area("Na jakie choroby choruje lub chorował dziadek ze strony ojca?", key="paternal_grandfather")

    with st.expander("26. Dotychczasowe rozpoznania, operacje i ważne informacje"):
        own_diagnoses = st.text_area("Proszę wymienić wszystkie dotychczasowe rozpoznania oraz operacje", key="own_diagnoses")
        important_info = st.text_area("Czy są jakieś ważne informacje, które chcesz przekazać lekarzowi?", key="important_info")
        current_reason = st.text_area("Co jest powodem obecnych dolegliwości lub problemów zdrowotnych?", key="current_reason")
        key_question = st.text_area("Jakie jest najważniejsze pytanie do lekarza lub najważniejszy problem do omówienia na wizycie?", key="key_question")

    with st.expander("27. Informacje organizacyjne i zgody", expanded=True):
        st.markdown(
            """
**Proszę przesłać wszystkie posiadane wyniki badań na adres:**  
niedzialkowski@ocenazdrowia.pl  

**lub wgrać je po zalogowaniu się na stronie:**  
https://aplikacja.medyc.pl/NiedzialkowskiPortal/#/login  

Po założeniu konta możesz wgrać pliki bezpośrednio do swojej kartoteki zdrowotnej.  
Najlepiej przesłać lub wgrać jeden plik PDF z wynikami ułożonymi chronologicznie.  

Proszę również przynieść na wizytę posiadane wyniki badań w formie papierowej.
"""
        )

        st.markdown('<div id="anchor_consent" class="field-anchor"></div>', unsafe_allow_html=True)
        consent_true = st.checkbox("Oświadczam, że podane informacje są prawdziwe.", key="consent_true")
        consent_visit = st.checkbox("Wyrażam zgodę na wykorzystanie tych informacji wyłącznie przez lekarza do przygotowania wizyty.", key="consent_visit")
        consent_privacy = st.checkbox("Przyjmuję do wiadomości, że formularz nie zapisuje danych w bazie aplikacji, a dokument wysyłany do lekarza zawiera ograniczone dane identyfikacyjne.", key="consent_privacy")
        contact_consent = st.checkbox("Wyrażam zgodę na kontakt telefoniczny lub mailowy w sprawach organizacyjnych związanych z wizytą.", key="contact_consent")

        if "consent" in field_errors:
            error_box(field_errors["consent"])

    progress_values = [
        visit_type, first_name, last_name, phone, email, birth_date_text, nationality, sex, current_status,
        profession, height_cm_text, weight_kg_text,
        physical_score, mental_score, weight_change, weight_change_amount,
        performed_tests,
        symptom_1, symptom_1_since, symptom_2, symptom_2_since, symptom_3, symptom_3_since,
        symptom_4, symptom_4_since, symptom_5, symptom_5_since, additional_symptoms,
        symptom_pattern, symptom_periodicity, symptom_past, worsening_factors, worsening_other,
        improvement_factors, improvement_other,
        health_timeline, current_meds,
        lifestyle, stimulants, stimulants_other, sleep_hours,
        travel_abroad, travel_where,
        animal_contact, animal_contact_details,
        major_injuries,
        covid, covid_details,
        strong_stress,
        birth_delivery, birth_timing, green_water, birth_info_other, breastfeeding, childhood_diseases, childhood_diseases_other,
        fever_now, fever_details, headache_dizziness, headache_dizziness_details, headache_assoc,
        hearing_vision, attacks, sinus_problems, nose_problems, allergies, herpes, mouth_corners,
        fresh_food_reaction, epilepsy, smell_taste, colds,
        throat_morning, esophagus_burning, asthma_dx, pneumonia, pneumonia_details, dyspnea,
        night_breath, chest_heaviness, breathing_type, wheezing, cough,
        chest_pain, pressure_type, current_bp, current_hr, pain_press, pain_position, palpitations,
        gi_problem, gi_symptoms, worsening_foods, gi_infections,
        urine_problems, night_urination, fluids,
        joints, stiffness,
        skin_changes, skin_itch, acne, acne_details, skin_sensation, wound_healing, wound_healing_details,
        sleep_problem, sleep_problem_types, psych_contact, psych_dx,
        edema, edema_details, calf_pain, cold_fingers, tingling, varicose,
        anal_problems, anal_other,
        gyn_problems, menstruation, first_menses, last_menses_text, potency,
        mother_history, father_history, maternal_grandmother, paternal_grandmother, maternal_grandfather, paternal_grandfather,
        own_diagnoses, important_info, current_reason, key_question,
        consent_true, consent_visit, consent_privacy, contact_consent
    ]

    progress_percent = calc_progress(progress_values)

    st.markdown('<div class="send-button">', unsafe_allow_html=True)
    send_clicked = st.form_submit_button("Wyślij")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# POSTĘP
# =========================================================
with progress_placeholder.container():
    st.markdown("<div class='progress-box'>", unsafe_allow_html=True)
    st.write(f"**Postęp wypełniania formularza: {progress_percent}%**")
    st.progress(progress_percent / 100)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# WALIDACJA I WYSYŁKA
# =========================================================
if send_clicked:
    st.session_state.field_errors = {}
    st.session_state.scroll_target = None

    first_name_clean = st.session_state.get("first_name", "").strip()
    last_name_clean = st.session_state.get("last_name", "").strip()
    phone_raw = st.session_state.get("phone", "").strip()
    email_raw = st.session_state.get("email", "").strip()
    birth_date_raw = st.session_state.get("birth_date_text", "").strip()

    validated_phone = validate_phone(phone_raw)
    validated_email = validate_email(email_raw) if email_raw else None
    birth_date = parse_polish_date(birth_date_raw)

    full_name = f"{first_name_clean} {last_name_clean}".strip()

    if not visit_type:
        st.session_state.field_errors["visit_type"] = "Wybierz rodzaj wizyty."
    if not first_name_clean:
        st.session_state.field_errors["first_name"] = "Wpisz imię."
    if not last_name_clean:
        st.session_state.field_errors["last_name"] = "Wpisz nazwisko."
    if not validated_phone:
        st.session_state.field_errors["phone"] = "Wpisz poprawny numer telefonu. Może być z +48 albo bez."
    if email_raw and not validated_email:
        st.session_state.field_errors["email"] = "Wpisz poprawny adres e-mail."
    if not birth_date:
        st.session_state.field_errors["birth_date"] = "Wpisz poprawną datę urodzenia w formacie DD.MM.RRRR."
    if not consent_true or not consent_visit or not consent_privacy:
        st.session_state.field_errors["consent"] = "Zaznacz wszystkie wymagane zgody."

    anchor_order = [
        ("visit_type", "anchor_first_name"),
        ("first_name", "anchor_first_name"),
        ("last_name", "anchor_last_name"),
        ("phone", "anchor_phone"),
        ("email", "anchor_email"),
        ("birth_date", "anchor_birth_date"),
        ("consent", "anchor_consent"),
    ]

    if st.session_state.field_errors:
        for field_key, anchor_id in anchor_order:
            if field_key in st.session_state.field_errors:
                st.session_state.scroll_target = anchor_id
                break
        st.rerun()

    patient_initials = initials(full_name)
    submitted_at = datetime.now().strftime("%d.%m.%Y, %H:%M")

    last_menses = parse_polish_date(last_menses_text) if last_menses_text else None

    main_symptom_rows = []
    if nonempty(symptom_1):
        main_symptom_rows.append(f"1. {symptom_1}" + (f" - od {symptom_1_since}" if nonempty(symptom_1_since) else ""))
    if nonempty(symptom_2):
        main_symptom_rows.append(f"2. {symptom_2}" + (f" - od {symptom_2_since}" if nonempty(symptom_2_since) else ""))
    if nonempty(symptom_3):
        main_symptom_rows.append(f"3. {symptom_3}" + (f" - od {symptom_3_since}" if nonempty(symptom_3_since) else ""))
    if nonempty(symptom_4):
        main_symptom_rows.append(f"4. {symptom_4}" + (f" - od {symptom_4_since}" if nonempty(symptom_4_since) else ""))
    if nonempty(symptom_5):
        main_symptom_rows.append(f"5. {symptom_5}" + (f" - od {symptom_5_since}" if nonempty(symptom_5_since) else ""))

    pdf_data = {
        "initials": patient_initials,
        "phone": validated_phone,
        "birth_date": birth_date.strftime("%d.%m.%Y") if birth_date else "",
        "visit_type": visit_type,
        "submitted_at": submitted_at,
        "sec_basic": [
            f"Płeć: {sex}" if nonempty(sex) else "",
            f"Narodowość: {nationality}" if nonempty(nationality) else "",
            f"Aktualny status: {current_status}" if nonempty(current_status) else "",
            f"Zawód: {profession}" if nonempty(profession) else "",
            f"Wzrost: {height_cm:.0f} cm" if height_cm is not None else "",
            f"Masa ciała: {weight_kg:.1f} kg" if weight_kg is not None else "",
            f"BMI: {bmi:.1f} ({bmi_label(bmi)})" if bmi is not None else "",
        ],
        "sec_overall": [
            f"Ocena stanu fizycznego: {physical_score}/10" if nonempty(physical_score) else "",
            f"Ocena stanu psychicznego: {mental_score}/10" if nonempty(mental_score) else "",
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
            f"Tryb życia: {lifestyle}" if nonempty(lifestyle) else "",
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
        "sec_injuries": [
            f"Duże urazy: {major_injuries}" if nonempty(major_injuries) else ""
        ],
        "sec_covid": [
            f"Zachorowanie na COVID-19: {covid}" + (f", {covid_details}" if nonempty(covid_details) else "") if nonempty(covid) else ""
        ],
        "sec_stress": [
            f"Silne reakcje stresowe: {strong_stress}" if nonempty(strong_stress) else ""
        ],
        "sec_birth_childhood": [
            f"Sposób porodu: {birth_delivery}" if nonempty(birth_delivery) else "",
            f"Czas porodu: {birth_timing}" if nonempty(birth_timing) else "",
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
Rodzaj wizyty: {visit_type}
Data i godzina wypełnienia formularza: {submitted_at}
Zgoda na kontakt organizacyjny: {"tak" if contact_consent else "nie"}
"""

    pdf_path = None
    try:
        with st.spinner("Trwa wysyłanie formularza..."):
            pdf_path = make_pdf(pdf_data)
            send_email_with_pdf(
                subject=f"Nowy formularz pacjenta - {full_name}",
                body_text=email_body,
                pdf_path=pdf_path,
            )

        st.session_state.field_errors = {}
        st.session_state.scroll_target = None
        st.success("Formularz został wysłany. Dziękujemy.")

    except Exception as e:
        st.error(f"Nie udało się wysłać formularza. Szczegóły: {e}")

    finally:
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception:
                pass

# =========================================================
# PRZEWIJANIE DO BŁĘDU
# =========================================================
if st.session_state.scroll_target:
    scroll_to_anchor(st.session_state.scroll_target)
