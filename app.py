import os
import smtplib
import tempfile
from datetime import date, datetime
from email.message import EmailMessage
from typing import Any, Dict, List

import streamlit as st
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


# =========================
# KONFIGURACJA STRONY
# =========================
st.set_page_config(
    page_title="Ocena stanu zdrowia - wywiad lekarski",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =========================
# UKRYCIE ELEMENTÓW STREAMLIT + STYL
# =========================
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .main .block-container {
        max-width: 980px;
        padding-top: 0.8rem;
        padding-bottom: 2rem;
    }

    .top-card {
        padding: 18px 18px;
        border-radius: 18px;
        border: 1px solid rgba(120,120,120,0.20);
        margin-bottom: 16px;
        background: rgba(250,250,250,0.03);
    }

    .site-url {
        text-align: center;
        font-size: 18px;
        margin-top: -10px;
        margin-bottom: 8px;
        opacity: 0.95;
    }

    .doctor-line {
        text-align: center;
        font-size: 17px;
        margin-top: 0px;
        margin-bottom: 8px;
    }

    .contact-line {
        text-align: center;
        font-size: 15px;
        margin-top: 0px;
        margin-bottom: 16px;
        opacity: 0.95;
    }

    .progress-box {
        padding: 12px 14px;
        border-radius: 12px;
        border: 1px solid rgba(120,120,120,0.20);
        margin-top: 10px;
        margin-bottom: 16px;
    }

    .send-button > button {
        width: 100%;
        height: 3.2rem;
        font-size: 1.05rem;
        font-weight: 700;
        border-radius: 12px;
    }

    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 0.5rem;
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        .site-url {
            font-size: 15px;
        }
        .doctor-line {
            font-size: 15px;
        }
        .contact-line {
            font-size: 14px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# SECRETS
# =========================
def get_secret(name: str) -> str:
    if name not in st.secrets:
        st.error(f"Brakuje sekretu: {name}")
        st.stop()
    return st.secrets[name]


EMAIL_NADAWCA = get_secret("EMAIL_NADAWCA")
HASLO_APLIKACJI = get_secret("HASLO_APLIKACJI")
EMAIL_ODBIORCA1 = get_secret("EMAIL_ODBIORCA1")
EMAIL_ODBIORCA2 = get_secret("EMAIL_ODBIORCA2")


# =========================
# FUNKCJE POMOCNICZE
# =========================
def nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, list):
        return len(value) > 0
    return True


def safe(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    return str(value).strip()


def list_text(values: List[str]) -> str:
    return ", ".join([v for v in values if v])


def lines_from_text(text: str) -> List[str]:
    return [x.strip() for x in text.splitlines() if x.strip()]


def initials(full_name: str) -> str:
    parts = [p for p in full_name.strip().split() if p]
    if not parts:
        return ""
    return " ".join([p[0].upper() + "." for p in parts])


def bmi_calc(weight_kg: float, height_cm: float):
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
    add_pdf_section(story, "Podróże, zwierzęta, urazy, COVID-19, stres", data["sec_exposures"], styles_dict)
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
    msg["To"] = f"{EMAIL_ODBIORCA1}, {EMAIL_ODBIORCA2}"
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


# =========================
# GÓRA APLIKACJI
# =========================
if os.path.exists("logo.png"):
    st.image("logo.png", use_container_width=True)

st.markdown("<div class='site-url'>www.ocenazdrowia.pl</div>", unsafe_allow_html=True)
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

# =========================
# FORMULARZ
# =========================
with st.expander("1. Dane podstawowe", expanded=True):
    visit_type = st.radio("Rodzaj wizyty", ["Pierwsza", "Kontrolna"], key="visit_type")
    first_name = st.text_input("Imię", key="first_name")
    last_name = st.text_input("Nazwisko", key="last_name")
    phone = st.text_input("Telefon kontaktowy", key="phone")
    email = st.text_input("Adres e-mail", key="email")
    birth_date = st.date_input(
        "Data urodzenia",
        value=date(1990, 1, 1),
        min_value=date(1900, 1, 1),
        max_value=date.today(),
        key="birth_date",
    )
    nationality = st.text_input("Narodowość", key="nationality")
    sex = st.selectbox("Płeć", ["kobieta", "mężczyzna", "inne"], key="sex")
    current_status = st.selectbox(
        "Aktualny status",
        ["pracujący", "dziecko", "uczeń", "student", "emeryt", "inne"],
        key="current_status",
    )
    profession = st.text_input("Obecnie wykonywany zawód", key="profession")
    height_cm = st.number_input("Wzrost (cm)", min_value=30.0, max_value=250.0, value=170.0, step=1.0, key="height_cm")
    weight_kg = st.number_input("Masa ciała (kg)", min_value=1.0, max_value=300.0, value=70.0, step=0.1, key="weight_kg")

    bmi = bmi_calc(weight_kg, height_cm)
    if bmi is not None:
        st.info(f"BMI: {bmi:.1f} ({bmi_label(bmi)})")
    else:
        st.info("BMI: brak danych")

with st.expander("2. Ocena ogólna"):
    physical_score = st.slider("Jak oceniasz swój stan fizyczny? 0 = bardzo zły, 10 = bardzo dobry", 0, 10, 6, key="physical_score")
    mental_score = st.slider("Jak oceniasz swój stan psychiczny? 0 = bardzo zły, 10 = bardzo dobry", 0, 10, 6, key="mental_score")
    weight_change = st.radio("Czy w ostatnim roku zmieniła się masa ciała?", ["wzrosła", "spadła", "bez zmian"], key="weight_change")
    weight_change_amount = st.text_input("O ile mniej więcej zmieniła się masa ciała?", key="weight_change_amount") if weight_change != "bez zmian" else ""

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
    symptom_pattern = st.radio("Czy objawy są stałe czy pojawiają się okresowo?", ["stałe", "okresowe", "trudno powiedzieć"], key="symptom_pattern")
    symptom_periodicity = st.text_area("Jeśli okresowe, napisz kiedy się pojawiają i jak często w ciągu roku", key="symptom_periodicity")
    symptom_past = st.text_area("Czy podobne objawy występowały wcześniej? Jeśli tak, kiedy?", key="symptom_past")
    aggravating_factors = st.multiselect(
        "Co nasila objawy?",
        ["po wysiłku", "na czczo", "po posiłku", "podczas mówienia", "podczas śmiechu", "rano", "w ciągu dnia", "wieczorem", "wybudzenie ze snu", "inne"],
        placeholder="Wybierz czynniki nasilające",
        key="aggravating_factors",
    )
    aggravating_other = st.text_input("Jeśli zaznaczono inne, napisz jakie", key="aggravating_other")
    relieving_factors = st.multiselect(
        "Co osłabia objawy?",
        ["podczas wypoczynku", "po wysiłku", "na czczo", "po posiłku", "rano", "w ciągu dnia", "wieczorem", "inne"],
        placeholder="Wybierz czynniki zmniejszające",
        key="relieving_factors",
    )
    relieving_other = st.text_input("Jeśli zaznaczono inne, napisz jakie", key="relieving_other")

with st.expander("6. Chronologia zdrowia i leki"):
    health_timeline = st.text_area("Opisz przebieg zdrowia od pierwszych problemów zdrowotnych do dziś", key="health_timeline")
    current_meds = st.text_area("Jakie leki obecnie przyjmujesz? Podaj nazwę i dawkowanie", key="current_meds")

with st.expander("7. Tryb życia"):
    lifestyle = st.selectbox("Tryb życia", ["leżący", "siedzący", "nisko aktywny", "średnio aktywny", "bardzo aktywny", "inne"], key="lifestyle")
    stimulants = st.multiselect(
        "Używki i codzienne nawyki",
        ["kawa", "herbata", "papierosy", "alkohol", "narkotyki", "słodycze", "inne"],
        placeholder="Wybierz używki i nawyki",
        key="stimulants",
    )
    stimulants_other = st.text_input("Jeśli zaznaczono inne, napisz jakie", key="stimulants_other")
    sleep_hours = st.selectbox("Ile średnio trwa sen na dobę?", [3, 4, 5, 6, 7, 8, 9, 10, 11, 12], key="sleep_hours")

with st.expander("8. Podróże, zwierzęta, urazy, COVID-19, stres"):
    travel_abroad = st.radio("Czy w ciągu ostatnich 3 miesięcy był wyjazd za granicę?", ["tak", "nie"], key="travel_abroad")
    travel_where = st.text_input("Jeśli tak, to gdzie?", key="travel_where") if travel_abroad == "tak" else ""
    animal_contact = st.radio("Czy w ostatnich miesiącach było pogryzienie, zadrapanie lub bliski kontakt ze zwierzęciem?", ["tak", "nie"], key="animal_contact")
    animal_contact_details = st.text_area("Jeśli tak, opisz kiedy i jakie zwierzę", key="animal_contact_details") if animal_contact == "tak" else ""
    major_injuries = st.text_area("Czy były duże urazy ciała? Podaj rok i opisz, np. upadek z wysokości, uraz komunikacyjny, pobicie, tonięcie, operacja", key="major_injuries")
    covid = st.radio("Czy i kiedy wystąpiło zachorowanie na COVID-19?", ["tak", "nie", "nie wiem"], key="covid")
    covid_details = st.text_area("Jeśli tak, opisz kiedy i jaki był przebieg", key="covid_details") if covid == "tak" else ""
    strong_stress = st.text_area("Czy w ciągu życia były silne reakcje stresowe lub trudne wydarzenia? Jeśli tak, opisz i podaj rok", key="strong_stress")

with st.expander("9. Urodzenie i dzieciństwo"):
    birth_info = st.multiselect(
        "Informacje o urodzeniu",
        ["poród naturalny", "poród przez cesarskie cięcie", "poród przedwczesny", "poród o czasie", "poród po terminie", "zielone wody płodowe", "nie wiem", "inne"],
        placeholder="Wybierz informacje o urodzeniu",
        key="birth_info",
    )
    birth_info_other = st.text_input("Jeśli zaznaczono inne, napisz jakie", key="birth_info_other")
    breastfeeding = st.selectbox(
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
    childhood_diseases_other = st.text_input("Jeśli zaznaczono inne, napisz jakie", key="childhood_diseases_other")

with st.expander("10. Objawy ogólne i neurologiczne"):
    fever_now = st.radio("Czy aktualnie występuje gorączka?", ["tak", "nie"], key="fever_now")
    fever_details = st.text_area("Jeśli tak, opisz dokładniej", key="fever_details") if fever_now == "tak" else ""
    headache_dizziness = st.radio("Czy występują bóle i zawroty głowy?", ["tak", "nie"], key="headache_dizziness")
    headache_dizziness_details = st.text_area("Jeśli tak, opisz dokładniej", key="headache_dizziness_details") if headache_dizziness == "tak" else ""
    headache_assoc = st.text_area("Czy bólom głowy towarzyszą wymioty, omdlenia, zaburzenia widzenia, osłabienie, światłowstręt, niepamięć?", key="headache_assoc")
    hearing_vision = st.text_area("Czy w ostatnich latach pogorszył się słuch lub wzrok?", key="hearing_vision")
    attacks = st.text_area("Czy występują ataki lub nagłe epizody? Jeśli tak, opisz.", key="attacks")
    sinus_problems = st.text_area("Czy występują problemy z zatokami?", key="sinus_problems")
    nose_problems = st.text_area("Czy są problemy z nosem, np. krwawienia, suchość, zapalenia, trudności w oddychaniu przez nos?", key="nose_problems")
    allergies = st.text_area("Czy występują alergie? Jeśli tak, na co, o jakiej porze roku i jak nasilone?", key="allergies")
    herpes = st.text_area("Czy pojawia się opryszczka? Jeśli tak, jak często?", key="herpes")
    mouth_corners = st.text_area("Czy występują zajady?", key="mouth_corners")
    fresh_food_reaction = st.text_area("Czy po spożyciu świeżych warzyw i owoców pojawia się pieczenie lub zaczerwienienie wokół ust?", key="fresh_food_reaction")
    epilepsy = st.radio("Czy kiedykolwiek rozpoznano padaczkę?", ["tak", "nie"], key="epilepsy")
    smell_taste = st.text_area("Czy są zaburzenia węchu lub smaku? Jeśli tak, od kiedy?", key="smell_taste")
    colds = st.text_input("Jak często zdarzają się przeziębienia w ciągu roku?", key="colds")

with st.expander("11. Układ oddechowy"):
    throat_morning = st.radio("Czy rano występuje ból gardła?", ["tak", "nie"], key="throat_morning")
    esophagus_burning = st.radio("Czy pojawia się pieczenie w przełyku?", ["tak", "nie"], key="esophagus_burning")
    asthma_dx = st.radio("Czy kiedykolwiek rozpoznano astmę?", ["tak", "nie"], key="asthma_dx")
    pneumonia = st.radio("Czy kiedykolwiek było zapalenie płuc?", ["tak", "nie"], key="pneumonia")
    pneumonia_details = st.text_area("Jeśli tak, podaj daty i po której stronie płuc było zapalenie", key="pneumonia_details") if pneumonia == "tak" else ""
    dyspnea = st.text_area("Czy zdarza się duszność lub zadyszka? Jeśli tak, opisz w jakich sytuacjach.", key="dyspnea")
    night_breath = st.text_area("Czy dochodzi do wybudzania w nocy z powodu braku tchu?", key="night_breath")
    chest_heaviness = st.text_area("Czy występuje ciężkość w klatce piersiowej? Jeśli tak, opisz nasilenie.", key="chest_heaviness")
    breathing_type = st.selectbox("Czy są trudności z oddychaniem?", ["nie mam takich trudności", "z nabieraniem powietrza", "z wypuszczaniem powietrza", "z oboma"], key="breathing_type")
    wheezing = st.multiselect(
        "Czy występuje świszczący oddech?",
        ["nie", "podczas wysiłku", "podczas infekcji", "w nocy", "rano", "podczas alergii", "w zimnej pogodzie"],
        placeholder="Wybierz okoliczności świszczącego oddechu",
        key="wheezing",
    )
    cough = st.text_area("Czy jest kaszel? Jeśli tak, od kiedy, czy jest suchy czy z wydzieliną, jakiego koloru?", key="cough")

with st.expander("12. Układ sercowo-naczyniowy"):
    chest_pain = st.text_area("Czy występują bóle w klatce piersiowej? Czy są miejscowe czy rozległe? Czy promieniują?", key="chest_pain")
    pressure_type = st.selectbox("Czy są problemy z ciśnieniem?", ["nie mam kłopotów z ciśnieniem", "mam skłonność do niskiego ciśnienia", "mam skłonność do wysokiego ciśnienia"], key="pressure_type")
    current_bp = st.text_input("Jakie jest aktualne ciśnienie tętnicze?", key="current_bp")
    current_hr = st.text_input("Jakie jest aktualne tętno?", key="current_hr")
    pain_press = st.radio("Czy odczuwasz ból przy naciskaniu klatki piersiowej?", ["tak", "nie"], key="pain_press")
    pain_position = st.radio("Czy przy zmianie pozycji występują bóle w klatce piersiowej?", ["tak", "nie"], key="pain_position")
    palpitations = st.text_area("Czy odczuwasz nierówne bicie serca? Jeśli tak, opisz porę dnia, okoliczności i częstość.", key="palpitations")

with st.expander("13. Przewód pokarmowy"):
    gi_problem = st.radio("Czy występują problemy z przewodem pokarmowym?", ["tak", "nie"], key="gi_problem")
    gi_symptoms = st.multiselect(
        "Zaznacz problemy",
        ["zgaga", "wzdęcia", "biegunki", "zaparcia", "hemoroidy", "gazy", "skurcze", "wymioty", "nudności"],
        placeholder="Wybierz objawy przewodu pokarmowego",
        key="gi_symptoms",
    ) if gi_problem == "tak" else []
    worsening_foods = st.text_area("Czy są potrawy, po których samopoczucie się pogarsza?", key="worsening_foods")
    gi_infections = st.text_area("Czy kiedykolwiek było zakażenie bakteryjne lub wirusowe przewodu pokarmowego? Jeśli tak, kiedy i czy było badanie kontrolne z wynikiem ujemnym?", key="gi_infections")

with st.expander("14. Układ moczowy"):
    urine_problems = st.text_area("Czy są problemy z oddawaniem moczu, np. pieczenie, trudności, inne?", key="urine_problems")
    night_urination = st.selectbox("Ile razy w nocy wstajesz oddać mocz?", ["0", "1", "2", "3", "4", "5", "6", "7 lub więcej"], key="night_urination")
    fluids = st.selectbox("Ile litrów płynów wypijasz dziennie?", ["1", "2", "3", "4", "5", "więcej niż 5"], key="fluids")

with st.expander("15. Stawy i mięśnie"):
    joints = st.text_area("Czy występują bóle stawów? Jeśli tak, to których?", key="joints")
    stiffness = st.text_area("Czy po wstaniu z łóżka występuje ból lub sztywność stawów?", key="stiffness")

with st.expander("16. Skóra"):
    skin_changes = st.text_area("Czy są jakieś zmiany na skórze? Jeśli tak, opisz dokładnie. Kiedy pojawiły się pierwszy raz? Czy od tej pory jest poprawa lub pogorszenie?", key="skin_changes")
    skin_itch = st.text_area("Czy występuje swędzenie skóry? Jeśli tak, których partii ciała dotyczy?", key="skin_itch")
    acne = st.radio("Czy występował lub występuje nasilony trądzik na twarzy lub plecach?", ["tak", "nie"], key="acne")
    acne_details = st.text_area("Jeśli tak, możesz opisać dokładniej", key="acne_details") if acne == "tak" else ""
    skin_sensation = st.text_area("Czy są zaburzenia czucia skóry? Jeśli tak, opisz lokalizację i od kiedy.", key="skin_sensation")
    wound_healing = st.radio("Czy występują problemy z gojeniem się ran?", ["tak", "nie"], key="wound_healing")
    wound_healing_details = st.text_area("Jeśli tak, opisz problemy z gojeniem", key="wound_healing_details") if wound_healing == "tak" else ""

with st.expander("17. Sen i psychika"):
    sleep_problem = st.radio("Czy są problemy ze snem?", ["tak", "nie"], key="sleep_problem")
    sleep_problem_types = st.multiselect(
        "Jakie problemy ze snem występują?",
        ["trudności z zasypianiem", "wybudzanie w nocy", "wstawanie zmęczony lub zmęczona", "chrapanie", "zbyt krótki sen", "bardzo głęboki sen"],
        placeholder="Wybierz rodzaj problemów ze snem",
        key="sleep_problem_types",
    ) if sleep_problem == "tak" else []
    psych_contact = st.selectbox("Czy kiedykolwiek była porada psychologa lub psychiatry?", ["nie", "psycholog", "psychiatra", "oba"], key="psych_contact")
    psych_dx = st.text_area("Czy kiedykolwiek rozpoznano chorobę psychiczną? Jeśli tak, napisz jaką.", key="psych_dx")

with st.expander("18. Krążenie obwodowe"):
    edema = st.radio("Czy pojawiają się obrzęki na podudziach lub kostkach?", ["tak", "nie"], key="edema")
    edema_details = st.text_area("Jeśli tak, napisz czy występują stale czy po staniu, siedzeniu lub w innych sytuacjach.", key="edema_details") if edema == "tak" else ""
    calf_pain = st.text_area("Czy występują bóle łydek podczas chodzenia? Jeśli tak, po jakim dystansie i po jakim czasie ustępują?", key="calf_pain")
    cold_fingers = st.text_area("Czy palce rąk lub nóg łatwo stają się zimne lub zmieniają kolor?", key="cold_fingers")
    tingling = st.text_area("Czy występuje mrowienie lub drętwienie rąk lub nóg?", key="tingling")
    varicose = st.text_area("Czy są obecne żylaki?", key="varicose")

with st.expander("19. Odbyt i okolice odbytu"):
    anal_problems = st.multiselect(
        "Czy występują problemy ze śluzówką odbytu?",
        ["nie", "hemoroidy", "stany zapalne błony śluzowej odbytu", "pieczenie", "świąd", "grzybica", "inne"],
        placeholder="Wybierz problemy w okolicy odbytu",
        key="anal_problems",
    )
    anal_other = st.text_input("Jeśli zaznaczono inne, opisz", key="anal_other")

with st.expander("20. Ginekologia lub andrologia"):
    if sex == "kobieta":
        gyn_problems = st.text_area("Czy występują problemy ginekologiczne?", key="gyn_problems")
        menstruation = st.text_area("Czy występuje nieregularna miesiączka, menopauza lub leczenie hormonalne? Jeśli tak, napisz od kiedy.", key="menstruation")
        first_menses = st.text_input("Podaj miesiąc i rok pierwszej miesiączki", key="first_menses")
        last_menses = st.date_input("Data ostatniej miesiączki", value=date.today(), min_value=date(1950, 1, 1), max_value=date.today(), key="last_menses")
        potency = ""
    elif sex == "mężczyzna":
        potency = st.selectbox("Czy są problemy z potencją?", ["nie", "czasami", "często"], key="potency")
        gyn_problems = ""
        menstruation = ""
        first_menses = ""
        last_menses = None
    else:
        gyn_problems = ""
        menstruation = ""
        first_menses = ""
        last_menses = None
        potency = ""

with st.expander("21. Wywiad rodzinny"):
    mother_history = st.text_area("Na jakie choroby choruje lub chorowała mama?", key="mother_history")
    father_history = st.text_area("Na jakie choroby choruje lub chorował ojciec?", key="father_history")
    maternal_grandmother = st.text_area("Na jakie choroby choruje lub chorowała babcia ze strony mamy?", key="maternal_grandmother")
    paternal_grandmother = st.text_area("Na jakie choroby choruje lub chorowała babcia ze strony ojca?", key="paternal_grandmother")
    maternal_grandfather = st.text_area("Na jakie choroby choruje lub chorował dziadek ze strony mamy?", key="maternal_grandfather")
    paternal_grandfather = st.text_area("Na jakie choroby choruje lub chorował dziadek ze strony ojca?", key="paternal_grandfather")

with st.expander("22. Dotychczasowe rozpoznania, operacje i ważne informacje"):
    own_diagnoses = st.text_area("Proszę wymienić wszystkie dotychczasowe rozpoznania oraz operacje", key="own_diagnoses")
    important_info = st.text_area("Czy są jakieś ważne informacje, które chcesz przekazać lekarzowi?", key="important_info")
    current_reason = st.text_area("Co jest powodem obecnych dolegliwości lub problemów zdrowotnych?", key="current_reason")
    key_question = st.text_area("Jakie jest najważniejsze pytanie do lekarza lub najważniejszy problem do omówienia na wizycie?", key="key_question")

with st.expander("23. Informacje organizacyjne i zgody", expanded=True):
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

    consent_true = st.checkbox("Oświadczam, że podane informacje są prawdziwe.", key="consent_true")
    consent_visit = st.checkbox("Wyrażam zgodę na wykorzystanie tych informacji wyłącznie przez lekarza do przygotowania wizyty.", key="consent_visit")
    consent_privacy = st.checkbox("Przyjmuję do wiadomości, że formularz nie zapisuje danych w bazie aplikacji, a dokument wysyłany do lekarza zawiera ograniczone dane identyfikacyjne.", key="consent_privacy")
    contact_consent = st.checkbox("Wyrażam zgodę na kontakt telefoniczny lub mailowy w sprawach organizacyjnych związanych z wizytą.", key="contact_consent")

# =========================
# POSTĘP
# =========================
progress_values = [
    first_name, last_name, phone, email, nationality, profession,
    physical_score, mental_score, weight_change_amount,
    performed_tests, symptom_1, symptom_2, symptom_3, symptom_4, symptom_5,
    additional_symptoms, symptom_periodicity, symptom_past,
    aggravating_factors, relieving_factors,
    health_timeline, current_meds,
    lifestyle, stimulants, stimulants_other, sleep_hours,
    travel_where, animal_contact_details, major_injuries, covid_details, strong_stress,
    birth_info, birth_info_other, childhood_diseases, childhood_diseases_other,
    fever_details, headache_dizziness_details, headache_assoc, hearing_vision, attacks,
    sinus_problems, nose_problems, allergies, herpes, mouth_corners, fresh_food_reaction, smell_taste, colds,
    pneumonia_details, dyspnea, night_breath, chest_heaviness, wheezing, cough,
    chest_pain, current_bp, current_hr, palpitations,
    gi_symptoms, worsening_foods, gi_infections,
    urine_problems, joints, stiffness,
    skin_changes, skin_itch, acne_details, skin_sensation, wound_healing_details,
    sleep_problem_types, psych_dx,
    edema_details, calf_pain, cold_fingers, tingling, varicose,
    anal_problems, anal_other,
    gyn_problems, menstruation, first_menses, potency,
    mother_history, father_history, maternal_grandmother, paternal_grandmother, maternal_grandfather, paternal_grandfather,
    own_diagnoses, important_info, current_reason, key_question,
    consent_true, consent_visit, consent_privacy, contact_consent
]

progress_percent = calc_progress(progress_values)

st.markdown("<div class='progress-box'>", unsafe_allow_html=True)
st.write(f"**Postęp wypełniania formularza: {progress_percent}%**")
st.progress(progress_percent / 100)
st.markdown("</div>", unsafe_allow_html=True)

# =========================
# PRZYCISK WYSYŁKI
# =========================
st.markdown('<div class="send-button">', unsafe_allow_html=True)
send_clicked = st.button("Wyślij")
st.markdown("</div>", unsafe_allow_html=True)

# =========================
# WYSYŁKA
# =========================
if send_clicked:
    full_name = f"{safe(first_name)} {safe(last_name)}".strip()

    errors = []
    if not full_name:
        errors.append("Wpisz imię i nazwisko.")
    if not phone.strip():
        errors.append("Wpisz telefon kontaktowy.")
    if not consent_true or not consent_visit or not consent_privacy:
        errors.append("Zaznacz wszystkie wymagane zgody.")

    if errors:
        for err in errors:
            st.error(err)
    else:
        patient_initials = initials(full_name)
        submitted_at = datetime.now().strftime("%d.%m.%Y, %H:%M")

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
            "phone": phone,
            "birth_date": birth_date.strftime("%d.%m.%Y"),
            "visit_type": visit_type,
            "submitted_at": submitted_at,
            "sec_basic": [
                f"Płeć: {sex}",
                f"Narodowość: {nationality}" if nonempty(nationality) else "",
                f"Aktualny status: {current_status}",
                f"Zawód: {profession}" if nonempty(profession) else "",
                f"Wzrost: {height_cm:.0f} cm",
                f"Masa ciała: {weight_kg:.1f} kg",
                f"BMI: {bmi:.1f} ({bmi_label(bmi)})" if bmi is not None else "",
            ],
            "sec_overall": [
                f"Ocena stanu fizycznego: {physical_score}/10",
                f"Ocena stanu psychicznego: {mental_score}/10",
                f"Zmiana masy ciała: {weight_change}" + (f", {weight_change_amount}" if nonempty(weight_change_amount) else ""),
            ],
            "sec_tests": [f"• {x}" for x in performed_tests],
            "sec_main_symptoms": main_symptom_rows,
            "sec_other_symptoms": [additional_symptoms],
            "sec_symptom_character": [
                f"Objawy: {symptom_pattern}",
                f"Okresowość: {symptom_periodicity}" if nonempty(symptom_periodicity) else "",
                f"Czy występowały wcześniej: {symptom_past}" if nonempty(symptom_past) else "",
                f"Co nasila objawy: {list_text(aggravating_factors)}" if aggravating_factors else "",
                f"Inne czynniki nasilające: {aggravating_other}" if nonempty(aggravating_other) else "",
                f"Co osłabia objawy: {list_text(relieving_factors)}" if relieving_factors else "",
                f"Inne czynniki zmniejszające objawy: {relieving_other}" if nonempty(relieving_other) else "",
            ],
            "sec_timeline_meds": [
                f"Chronologia zdrowia: {health_timeline}" if nonempty(health_timeline) else "",
                "Aktualnie przyjmowane leki:" if nonempty(current_meds) else "",
                *lines_from_text(current_meds),
            ],
            "sec_lifestyle": [
                f"Tryb życia: {lifestyle}",
                f"Używki i nawyki: {list_text(stimulants)}" if stimulants else "",
                f"Inne używki lub nawyki: {stimulants_other}" if nonempty(stimulants_other) else "",
                f"Sen: {sleep_hours} godzin na dobę",
            ],
            "sec_exposures": [
                f"Wyjazd za granicę: {travel_abroad}" + (f", {travel_where}" if nonempty(travel_where) else ""),
                f"Kontakt lub uraz od zwierzęcia: {animal_contact}" + (f", {animal_contact_details}" if nonempty(animal_contact_details) else ""),
                f"Duże urazy: {major_injuries}" if nonempty(major_injuries) else "",
                f"Zachorowanie na COVID-19: {covid}" + (f", {covid_details}" if nonempty(covid_details) else ""),
                f"Silne reakcje stresowe: {strong_stress}" if nonempty(strong_stress) else "",
            ],
            "sec_birth_childhood": [
                f"Informacje o urodzeniu: {list_text(birth_info)}" if birth_info else "",
                f"Inne informacje o urodzeniu: {birth_info_other}" if nonempty(birth_info_other) else "",
                f"Karmienie mlekiem matki: {breastfeeding}",
                f"Choroby dzieciństwa: {list_text(childhood_diseases)}" if childhood_diseases else "",
                f"Inne choroby dzieciństwa: {childhood_diseases_other}" if nonempty(childhood_diseases_other) else "",
            ],
            "sec_general_neuro": [
                f"Gorączka: {fever_now}" + (f", {fever_details}" if nonempty(fever_details) else ""),
                f"Bóle lub zawroty głowy: {headache_dizziness}" + (f", {headache_dizziness_details}" if nonempty(headache_dizziness_details) else ""),
                f"Objawy towarzyszące bólom głowy: {headache_assoc}" if nonempty(headache_assoc) else "",
                f"Słuch lub wzrok: {hearing_vision}" if nonempty(hearing_vision) else "",
                f"Ataki lub nagłe epizody: {attacks}" if nonempty(attacks) else "",
                f"Problemy z zatokami: {sinus_problems}" if nonempty(sinus_problems) else "",
                f"Problemy z nosem: {nose_problems}" if nonempty(nose_problems) else "",
                f"Alergie: {allergies}" if nonempty(allergies) else "",
                f"Opryszczka: {herpes}" if nonempty(herpes) else "",
                f"Zajady: {mouth_corners}" if nonempty(mouth_corners) else "",
                f"Reakcja po świeżych warzywach i owocach: {fresh_food_reaction}" if nonempty(fresh_food_reaction) else "",
                f"Padaczka: {epilepsy}",
                f"Zaburzenia węchu lub smaku: {smell_taste}" if nonempty(smell_taste) else "",
                f"Częstość przeziębień: {colds}" if nonempty(colds) else "",
            ],
            "sec_respiratory": [
                f"Ból gardła rano: {throat_morning}",
                f"Pieczenie w przełyku: {esophagus_burning}",
                f"Rozpoznana astma: {asthma_dx}",
                f"Zapalenie płuc: {pneumonia}" + (f", {pneumonia_details}" if nonempty(pneumonia_details) else ""),
                f"Duszność lub zadyszka: {dyspnea}" if nonempty(dyspnea) else "",
                f"Wybudzanie w nocy z powodu braku tchu: {night_breath}" if nonempty(night_breath) else "",
                f"Ciężkość w klatce piersiowej: {chest_heaviness}" if nonempty(chest_heaviness) else "",
                f"Trudności z oddychaniem: {breathing_type}",
                f"Świszczący oddech: {list_text(wheezing)}" if wheezing else "",
                f"Kaszel: {cough}" if nonempty(cough) else "",
            ],
            "sec_cardio": [
                f"Bóle w klatce piersiowej: {chest_pain}" if nonempty(chest_pain) else "",
                f"Problemy z ciśnieniem: {pressure_type}",
                f"Aktualne ciśnienie: {current_bp}" if nonempty(current_bp) else "",
                f"Aktualne tętno: {current_hr}" if nonempty(current_hr) else "",
                f"Ból przy nacisku na klatkę piersiową: {pain_press}",
                f"Ból przy zmianie pozycji: {pain_position}",
                f"Nierówne bicie serca: {palpitations}" if nonempty(palpitations) else "",
            ],
            "sec_gi": [
                f"Problemy z przewodem pokarmowym: {gi_problem}",
                f"Objawy: {list_text(gi_symptoms)}" if gi_symptoms else "",
                f"Potrawy pogarszające stan: {worsening_foods}" if nonempty(worsening_foods) else "",
                f"Przebyte infekcje przewodu pokarmowego: {gi_infections}" if nonempty(gi_infections) else "",
            ],
            "sec_urinary": [
                f"Problemy z oddawaniem moczu: {urine_problems}" if nonempty(urine_problems) else "",
                f"Liczba mikcji nocnych: {night_urination}",
                f"Ilość wypijanych płynów dziennie: {fluids} l",
            ],
            "sec_msk": [
                f"Bóle stawów: {joints}" if nonempty(joints) else "",
                f"Sztywność po wstaniu z łóżka: {stiffness}" if nonempty(stiffness) else "",
            ],
            "sec_skin": [
                f"Zmiany skórne: {skin_changes}" if nonempty(skin_changes) else "",
                f"Świąd skóry: {skin_itch}" if nonempty(skin_itch) else "",
                f"Trądzik: {acne}" + (f", {acne_details}" if nonempty(acne_details) else ""),
                f"Zaburzenia czucia skóry: {skin_sensation}" if nonempty(skin_sensation) else "",
                f"Problemy z gojeniem ran: {wound_healing}" + (f", {wound_healing_details}" if nonempty(wound_healing_details) else ""),
            ],
            "sec_sleep_psych": [
                f"Problemy ze snem: {sleep_problem}",
                f"Rodzaj problemów ze snem: {list_text(sleep_problem_types)}" if sleep_problem_types else "",
                f"Kontakt z psychologiem lub psychiatrą: {psych_contact}",
                f"Rozpoznana choroba psychiczna: {psych_dx}" if nonempty(psych_dx) else "",
            ],
            "sec_peripheral": [
                f"Obrzęki: {edema}" + (f", {edema_details}" if nonempty(edema_details) else ""),
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
            "sec_question": [
                key_question
            ],
        }

        email_body = f"""Nowy formularz pacjenta został wysłany.

Imię i nazwisko: {full_name}
Telefon kontaktowy: {phone}
Adres e-mail: {email}
Data urodzenia: {birth_date.strftime("%d.%m.%Y")}
Rodzaj wizyty: {visit_type}
Data i godzina wypełnienia formularza: {submitted_at}
Zgoda na kontakt organizacyjny: {"tak" if contact_consent else "nie"}
"""

        try:
            with st.spinner("Trwa wysyłanie formularza..."):
                pdf_path = make_pdf(pdf_data)
                send_email_with_pdf(
                    subject=f"Nowy formularz pacjenta - {full_name}",
                    body_text=email_body,
                    pdf_path=pdf_path,
                )
                try:
                    os.remove(pdf_path)
                except Exception:
                    pass
            st.success("Formularz został wysłany. Dziękujemy.")
        except Exception as e:
            st.error(f"Nie udało się wysłać formularza. Szczegóły: {e}")
