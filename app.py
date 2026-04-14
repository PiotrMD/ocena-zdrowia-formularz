import io
import textwrap
from datetime import date
from typing import List

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(
    page_title="Ocena stanu zdrowia, wywiad lekarski",
    layout="centered",
    initial_sidebar_state="collapsed",
)

try:
    st.set_option("client.showErrorDetails", False)
except Exception:
    pass

st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 980px;
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
    }
    .top-card {
        padding: 16px 18px;
        border-radius: 14px;
        border: 1px solid rgba(120,120,120,0.22);
        margin-bottom: 14px;
        background: rgba(250,250,250,0.03);
    }
    .stDownloadButton button, .stFormSubmitButton button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def nonempty(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, list):
        return len(value) > 0
    return True


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


def add_section(summary: List[str], title: str, rows: List[str]):
    cleaned = [r for r in rows if nonempty(r)]
    if cleaned:
        summary.append(title)
        summary.extend(cleaned)
        summary.append("")


def wrap_lines_for_pdf(text: str, width: int = 105) -> List[str]:
    lines: List[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
        else:
            lines.extend(textwrap.wrap(paragraph, width=width))
    return lines


def simplify_polish(text: str) -> str:
    return (
        text.replace("ą", "a").replace("ć", "c").replace("ę", "e").replace("ł", "l")
        .replace("ń", "n").replace("ó", "o").replace("ś", "s").replace("ź", "z").replace("ż", "z")
        .replace("Ą", "A").replace("Ć", "C").replace("Ę", "E").replace("Ł", "L")
        .replace("Ń", "N").replace("Ó", "O").replace("Ś", "S").replace("Ź", "Z").replace("Ż", "Z")
    )


def make_pdf(title: str, body: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    _, page_height = A4
    y = page_height - 40
    margin = 40

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(margin, y, simplify_polish(title))
    y -= 22

    pdf.setFont("Helvetica", 10)
    for line in wrap_lines_for_pdf(body, width=105):
        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = page_height - 40
        pdf.drawString(margin, y, simplify_polish(line))
        y -= 14

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def list_text(values: List[str]) -> str:
    return ", ".join([v for v in values if v])


st.title("Ocena stanu zdrowia, wywiad lekarski")
st.caption("dr n. med. Piotr Niedziałkowski")

st.markdown(
    """
    <div class="top-card">
    Szanowni Państwo,<br><br>
    każda wizyta jest przygotowywana indywidualnie.<br>
    Bardzo proszę o szczere i możliwie dokładne odpowiedzi dotyczące stanu zdrowia.<br>
    Im więcej szczegółów, tym większa szansa na wcześniejsze wykrycie problemów i trafną ocenę sytuacji zdrowotnej.<br><br>
    W przypadku dzieci proszę o wypełnienie odpowiednich pól.<br><br>
    Serdecznie pozdrawiam i do zobaczenia na wizycie.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("ankieta_zdrowia"):
    with st.expander("1. Dane podstawowe", expanded=True):
        email = st.text_input("Adres e-mail")
        full_name = st.text_input("Imię i nazwisko")
        birth_date = st.date_input(
            "Data urodzenia",
            value=date(1990, 1, 1),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
        )
        nationality = st.text_input("Narodowość")
        sex = st.selectbox("Płeć", ["kobieta", "mężczyzna", "inne"])
        current_status = st.selectbox(
            "Aktualny status",
            ["pracujący", "dziecko", "uczeń", "student", "emeryt", "inne"],
        )
        profession = st.text_input("Obecnie wykonywany zawód")
        height_cm = st.number_input("Wzrost (cm)", min_value=30.0, max_value=250.0, value=170.0, step=1.0)
        weight_kg = st.number_input("Masa ciała (kg)", min_value=1.0, max_value=300.0, value=70.0, step=0.1)

        bmi = bmi_calc(weight_kg, height_cm)
        if bmi is not None:
            st.info(f"BMI: {bmi:.1f} ({bmi_label(bmi)})")
        else:
            st.info("BMI: brak danych")

    with st.expander("2. Ocena ogólna"):
        physical_score = st.slider(
            "Jak oceniasz swój stan fizyczny? 0 = bardzo zły, 10 = bardzo dobry",
            0, 10, 6
        )
        mental_score = st.slider(
            "Jak oceniasz swój stan psychiczny? 0 = bardzo zły, 10 = bardzo dobry",
            0, 10, 6
        )
        weight_change = st.radio(
            "Czy w ostatnim roku zmieniła się masa ciała?",
            ["wzrosła", "spadła", "bez zmian"]
        )
        weight_change_amount = ""
        if weight_change != "bez zmian":
            weight_change_amount = st.text_input("O ile mniej więcej zmieniła się masa ciała?", key="weight_change_amount")

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
                "USG miednicy",
                "USG ginekologiczne",
                "USG tarczycy",
                "USG jąder",
                "USG prostaty",
                "Tomografia komputerowa",
                "Tomografia głowy",
                "Rezonans głowy",
                "Doppler tętnic szyjnych",
                "Przepływy kończyn dolnych",
                "Densytometria",
                "Scyntygrafia",
                "Mammografia",
                "USG piersi",
            ]
        )

    with st.expander("4. Objawy główne"):
        main_symptoms = []
        for i in range(1, 6):
            st.markdown(f"**Objaw {i}**")
            symptom_name = st.text_input(f"Nazwa objawu {i}", key=f"main_symptom_{i}")
            symptom_since = st.text_input(
                f"Od kiedy występuje objaw {i}?",
                key=f"main_symptom_since_{i}",
                placeholder="np. 03.2024 lub 2021"
            )
            if symptom_name.strip():
                if symptom_since.strip():
                    main_symptoms.append(f"{symptom_name.strip()} - od {symptom_since.strip()}")
                else:
                    main_symptoms.append(symptom_name.strip())

        additional_symptoms = st.text_area(
            "Pozostałe dolegliwości, nawet mniej nasilone",
            key="additional_symptoms"
        )

    with st.expander("5. Charakter objawów"):
        symptom_pattern = st.radio(
            "Czy objawy są stałe czy pojawiają się okresowo?",
            ["stałe", "okresowe", "trudno powiedzieć"],
            key="symptom_pattern"
        )
        symptom_periodicity = st.text_area(
            "Jeśli okresowe, napisz kiedy się pojawiają i jak często w ciągu roku",
            key="symptom_periodicity"
        )
        symptom_past = st.text_area(
            "Czy podobne objawy występowały wcześniej? Jeśli tak, kiedy?",
            key="symptom_past"
        )

        worsen_factors = st.multiselect(
            "Co nasila objawy?",
            [
                "po wysiłku",
                "na czczo",
                "po posiłku",
                "podczas mówienia",
                "podczas śmiechu",
                "rano",
                "w ciągu dnia",
                "wieczorem",
                "wybudzenie ze snu",
            ],
            key="worsen_factors"
        )
        worsen_other = st.text_input("Inne sytuacje nasilające objawy", key="worsen_other")

        relieve_factors = st.multiselect(
            "Co osłabia objawy?",
            [
                "podczas wypoczynku",
                "po wysiłku",
                "na czczo",
                "po posiłku",
                "rano",
                "w ciągu dnia",
                "wieczorem",
            ],
            key="relieve_factors"
        )
        relieve_other = st.text_input("Inne sytuacje zmniejszające objawy", key="relieve_other")

    with st.expander("6. Chronologia zdrowia i leki"):
        health_timeline = st.text_area(
            "Opisz przebieg zdrowia od pierwszych problemów zdrowotnych do dziś",
            key="health_timeline"
        )
        current_meds = st.text_area(
            "Jakie leki obecnie przyjmujesz? Podaj nazwę i dawkowanie",
            key="current_meds"
        )

    with st.expander("7. Tryb życia"):
        lifestyle = st.selectbox(
            "Tryb życia",
            ["leżący", "siedzący", "nisko aktywny", "średnio aktywny", "bardzo aktywny", "inne"],
            key="lifestyle"
        )
        stimulants = st.multiselect(
            "Używki i codzienne nawyki",
            ["kawa", "herbata", "papierosy", "alkohol", "narkotyki", "słodycze", "inne"],
            key="stimulants"
        )
        stimulants_other = st.text_input("Jeśli zaznaczono inne, napisz jakie", key="stimulants_other")
        sleep_hours = st.selectbox("Ile średnio trwa sen na dobę?", [3, 4, 5, 6, 7, 8, 9, 10, 11, 12], key="sleep_hours")

    with st.expander("8. Podróże, zwierzęta, urazy, COVID, stres"):
        travel_abroad = st.radio("Czy w ciągu ostatnich 3 miesięcy był wyjazd za granicę?", ["tak", "nie"], key="travel_abroad")
        travel_where = st.text_input("Jeśli tak, to gdzie?", key="travel_where") if travel_abroad == "tak" else ""

        animal_contact = st.radio(
            "Czy w ostatnich miesiącach było pogryzienie, zadrapanie lub bliski kontakt ze zwierzęciem?",
            ["tak", "nie"],
            key="animal_contact"
        )
        animal_contact_details = st.text_area("Jeśli tak, opisz kiedy i jakie zwierzę", key="animal_contact_details") if animal_contact == "tak" else ""

        major_injuries = st.text_area(
            "Czy były duże urazy ciała? Podaj rok i opisz, np. upadek z wysokości, uraz komunikacyjny, pobicie, tonięcie, operacja",
            key="major_injuries"
        )

        covid = st.radio("Czy było przechorowanie COVID-19?", ["tak", "nie", "nie wiem"], key="covid")
        covid_details = st.text_area("Jeśli tak, opisz kiedy i jaki był przebieg", key="covid_details") if covid == "tak" else ""

        strong_stress = st.text_area(
            "Czy w ciągu życia były silne reakcje stresowe lub trudne wydarzenia? Jeśli tak, opisz i podaj rok",
            key="strong_stress"
        )

    with st.expander("9. Urodzenie i dzieciństwo"):
        birth_info = st.multiselect(
            "Informacje o urodzeniu",
            [
                "poród naturalny",
                "poród przez cesarskie cięcie",
                "poród przedwczesny",
                "poród o czasie",
                "poród po terminie",
                "zielone wody płodowe",
                "nie wiem",
            ],
            key="birth_info"
        )
        birth_info_other = st.text_input("Inne ważne informacje o urodzeniu", key="birth_info_other")

        breastfeeding = st.selectbox(
            "Czy było karmienie mlekiem matki?",
            ["tak, do 3 miesięcy", "tak, do 6 miesięcy", "tak, powyżej 6 miesięcy", "nie", "nie wiem"],
            key="breastfeeding"
        )

        childhood_diseases = st.multiselect(
            "Poważne choroby w dzieciństwie",
            [
                "astma",
                "atopowe zapalenie skóry",
                "skaza białkowa",
                "częste przeziębienia",
                "pobyty w szpitalu",
                "częste zapalenia płuc",
                "problemy jelitowe",
                "choroby psychiczne",
                "problemy ze śledzioną",
                "problemy z trzustką",
                "inne",
            ],
            key="childhood_diseases"
        )
        childhood_diseases_other = st.text_input("Inne ważne choroby w dzieciństwie", key="childhood_diseases_other")

    with st.expander("10. Objawy ogólne i neurologiczne"):
        fever_now = st.radio("Czy aktualnie występuje gorączka?", ["tak", "nie"], key="fever_now")
        fever_details = st.text_area(
            "Jeśli tak, opisz dokładniej",
            key="fever_details"
        ) if fever_now == "tak" else ""

        headache_dizziness = st.radio("Czy występują bóle i zawroty głowy?", ["tak", "nie"], key="headache_dizziness")
        headache_dizziness_details = st.text_area(
            "Jeśli tak, opisz dokładniej",
            key="headache_dizziness_details"
        ) if headache_dizziness == "tak" else ""

        headache_assoc = st.text_area(
            "Czy bólom głowy towarzyszą wymioty, omdlenia, zaburzenia widzenia, osłabienie, światłowstręt, niepamięć?",
            key="headache_assoc"
        )
        hearing_vision = st.text_area("Czy w ostatnich latach pogorszył się słuch lub wzrok?", key="hearing_vision")
        attacks = st.text_area("Czy występują ataki lub nagłe epizody? Jeśli tak, opisz.", key="attacks")
        sinus_problems = st.text_area("Czy występują problemy z zatokami?", key="sinus_problems")
        nose_problems = st.text_area("Czy są problemy z nosem, np. krwawienia, suchość, zapalenia, trudności w oddychaniu przez nos?", key="nose_problems")
        allergies = st.text_area("Czy występują alergie? Jeśli tak, to na co, o jakiej porze roku i jak nasilone?", key="allergies")
        herpes = st.text_area("Czy pojawia się opryszczka? Jeśli tak, jak często?", key="herpes")
        mouth_corners = st.text_area("Czy występują zajady?", key="mouth_corners")
        fresh_food_reaction = st.text_area(
            "Czy po spożyciu świeżych warzyw i owoców pojawia się pieczenie lub zaczerwienienie wokół ust?",
            key="fresh_food_reaction"
        )
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
        breathing_type = st.selectbox(
            "Czy są trudności z oddychaniem?",
            ["nie mam takich trudności", "z nabieraniem powietrza", "z wypuszczaniem powietrza", "z oboma"],
            key="breathing_type"
        )
        wheezing = st.multiselect(
            "Czy występuje świszczący oddech?",
            ["nie", "podczas wysiłku", "podczas infekcji", "w nocy", "rano", "podczas alergii", "w zimnej pogodzie"],
            key="wheezing"
        )
        cough = st.text_area("Czy jest kaszel? Jeśli tak, od kiedy, czy jest suchy czy z wydzieliną, jakiego koloru?", key="cough")

    with st.expander("12. Układ sercowo-naczyniowy"):
        chest_pain = st.text_area("Czy występują bóle w klatce piersiowej? Czy są miejscowe czy rozległe? Czy promieniują?", key="chest_pain")
        pressure_type = st.selectbox(
            "Czy są problemy z ciśnieniem?",
            [
                "nie mam kłopotów z ciśnieniem",
                "mam skłonność do niskiego ciśnienia",
                "mam skłonność do wysokiego ciśnienia",
            ],
            key="pressure_type"
        )
        current_bp = st.text_input("Jakie jest aktualne ciśnienie tętnicze?", key="current_bp")
        current_hr = st.text_input("Jakie jest aktualne tętno?", key="current_hr")
        pain_press = st.radio("Czy odczuwasz ból przy naciskaniu klatki piersiowej?", ["tak", "nie"], key="pain_press")
        pain_position = st.radio("Czy przy zmianie pozycji występują bóle w klatce piersiowej?", ["tak", "nie"], key="pain_position")
        palpitations = st.text_area("Czy odczuwasz nierówne bicie serca? Jeśli tak, opisz porę dnia, okoliczności i częstość.", key="palpitations")

    with st.expander("13. Przewód pokarmowy"):
        gi_problem = st.radio("Czy występują problemy z przewodem pokarmowym?", ["tak", "nie"], key="gi_problem")
        gi_symptoms = []
        if gi_problem == "tak":
            gi_symptoms = st.multiselect(
                "Zaznacz problemy",
                ["zgaga", "wzdęcia", "biegunki", "zaparcia", "hemoroidy", "gazy", "skurcze", "wymioty", "nudności"],
                key="gi_symptoms"
            )
        worsening_foods = st.text_area("Czy są potrawy, po których samopoczucie się pogarsza?", key="worsening_foods")
        gi_infections = st.text_area(
            "Czy kiedykolwiek było zakażenie bakteryjne lub wirusowe przewodu pokarmowego? Jeśli tak, kiedy i czy było badanie kontrolne z wynikiem ujemnym?",
            key="gi_infections"
        )

    with st.expander("14. Układ moczowy"):
        urine_problems = st.text_area("Czy są problemy z oddawaniem moczu, np. pieczenie, trudności, inne?", key="urine_problems")
        night_urination = st.selectbox("Ile razy w nocy wstajesz oddać mocz?", ["0", "1", "2", "3", "4", "5", "6", "7 lub więcej"], key="night_urination")
        fluids = st.selectbox("Ile litrów płynów wypijasz dziennie?", ["1", "2", "3", "4", "5", "więcej niż 5"], key="fluids")

    with st.expander("15. Stawy i mięśnie"):
        joints = st.text_area("Czy występują bóle stawów? Jeśli tak, to których?", key="joints")
        stiffness = st.text_area("Czy po wstaniu z łóżka występuje ból lub sztywność stawów?", key="stiffness")

    with st.expander("16. Skóra"):
        skin_changes = st.text_area(
            "Czy są jakieś zmiany na skórze? Jeśli tak, opisz dokładnie. Kiedy pojawiły się pierwszy raz? Czy od tej pory jest poprawa lub pogorszenie?",
            key="skin_changes"
        )
        skin_itch = st.text_area("Czy występuje swędzenie skóry? Jeśli tak, których partii ciała dotyczy?", key="skin_itch")
        acne = st.radio("Czy występował lub występuje nasilony trądzik na twarzy lub plecach?", ["tak", "nie"], key="acne")
        acne_details = st.text_area("Jeśli tak, możesz opisać dokładniej", key="acne_details") if acne == "tak" else ""
        skin_sensation = st.text_area("Czy są zaburzenia czucia skóry? Jeśli tak, opisz lokalizację i od kiedy.", key="skin_sensation")
        wound_healing = st.radio("Czy występują problemy z gojeniem się ran?", ["tak", "nie"], key="wound_healing")
        wound_healing_details = st.text_area("Jeśli tak, opisz problemy z gojeniem", key="wound_healing_details") if wound_healing == "tak" else ""

    with st.expander("17. Sen i psychika"):
        sleep_problem = st.radio("Czy są problemy ze snem?", ["tak", "nie"], key="sleep_problem")
        sleep_problem_types = []
        if sleep_problem == "tak":
            sleep_problem_types = st.multiselect(
                "Jakie problemy ze snem występują?",
                [
                    "trudności z zasypianiem",
                    "wybudzanie w nocy",
                    "wstawanie zmęczony lub zmęczona",
                    "chrapanie",
                    "zbyt krótki sen",
                    "bardzo głęboki sen",
                ],
                key="sleep_problem_types"
            )
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
            key="anal_problems"
        )
        anal_other = st.text_input("Jeśli zaznaczono inne, opisz", key="anal_other")

    if sex == "kobieta":
        with st.expander("20. Ginekologia"):
            gyn_problems = st.text_area("Czy występują problemy ginekologiczne?", key="gyn_problems")
            menstruation = st.text_area("Czy występuje nieregularna miesiączka, menopauza lub leczenie hormonalne? Jeśli tak, napisz od kiedy.", key="menstruation")
            first_menses = st.text_input("Podaj miesiąc i rok pierwszej miesiączki", key="first_menses")
            last_menses = st.date_input(
                "Data ostatniej miesiączki",
                value=date.today(),
                min_value=date(1950, 1, 1),
                max_value=date.today(),
                key="last_menses"
            )
    else:
        gyn_problems = ""
        menstruation = ""
        first_menses = ""
        last_menses = None

    if sex == "mężczyzna":
        with st.expander("20. Andrologia"):
            potency = st.selectbox("Czy są problemy z potencją?", ["nie", "czasami", "często"], key="potency")
    else:
        potency = ""

    with st.expander("21. Wywiad rodzinny"):
        mother_history = st.text_area("Na jakie choroby choruje lub chorowała mama?", key="mother_history")
        father_history = st.text_area("Na jakie choroby choruje lub chorował ojciec?", key="father_history")
        maternal_grandmother = st.text_area("Na jakie choroby choruje lub chorowała babcia ze strony mamy?", key="maternal_grandmother")
        paternal_grandmother = st.text_area("Na jakie choroby choruje lub chorowała babcia ze strony ojca?", key="paternal_grandmother")
        maternal_grandfather = st.text_area("Na jakie choroby choruje lub chorował dziadek ze strony mamy?", key="maternal_grandfather")
        paternal_grandfather = st.text_area("Na jakie choroby choruje lub chorował dziadek ze strony ojca?", key="paternal_grandfather")

    with st.expander("22. Rozpoznania, operacje i ważne informacje"):
        own_diagnoses = st.text_area("Proszę wymienić wszystkie dotychczasowe rozpoznania oraz operacje", key="own_diagnoses")
        important_info = st.text_area("Czy są jakieś ważne informacje, które chcesz przekazać lekarzowi?", key="important_info")
        current_reason = st.text_area("Co jest powodem obecnych dolegliwości lub problemów zdrowotnych?", key="current_reason")
        visit_reason = st.radio(
            "Wykonuję ocenę zdrowia z powodu:",
            [
                "nic mi nie dolega, chcę poznać swój stan zdrowia",
                "mam dolegliwości, szukam pomocy",
                "nie wiem",
            ],
            key="visit_reason"
        )

    with st.expander("23. Załączniki i informacja końcowa", expanded=True):
        attachments = st.file_uploader(
            "Możesz dodać wyniki badań",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="attachments"
        )

        st.markdown(
            """
**Proszę wyślij wszystkie posiadane wyniki badań na adres:**  
niedzialkowski@ocenazdrowia.pl  

**lub załącz pliki logując się na stronie:**  
https://aplikacja.medyc.pl/NiedzialkowskiPortal/#/login  

Po założeniu konta możesz wgrać pliki bezpośrednio do swojej kartoteki zdrowotnej.  
Najlepiej wysłać lub wgrać jeden plik PDF układając wyniki chronologicznie.  

Proszę przynieść na wizytę posiadane wyniki badań w formie papierowej.  

**Bardzo dziękuję.**
"""
        )

    submitted = st.form_submit_button("Utwórz podsumowanie", use_container_width=True)

if submitted:
    summary: List[str] = []
    summary.append("PODSUMOWANIE ANKIETY PACJENTA")
    summary.append("")

    add_section(summary, "Dane podstawowe", [
        f"Imię i nazwisko: {full_name}" if nonempty(full_name) else "",
        f"Adres e-mail: {email}" if nonempty(email) else "",
        f"Data urodzenia: {birth_date.isoformat()}" if birth_date else "",
        f"Narodowość: {nationality}" if nonempty(nationality) else "",
        f"Płeć: {sex}" if nonempty(sex) else "",
        f"Aktualny status: {current_status}" if nonempty(current_status) else "",
        f"Zawód: {profession}" if nonempty(profession) else "",
        f"Wzrost: {height_cm:.0f} cm",
        f"Masa ciała: {weight_kg:.1f} kg",
        f"BMI: {bmi:.1f} ({bmi_label(bmi)})" if bmi is not None else "",
    ])

    add_section(summary, "Ocena ogólna", [
        f"Ocena stanu fizycznego: {physical_score}/10",
        f"Ocena stanu psychicznego: {mental_score}/10",
        f"Zmiana masy ciała: {weight_change}" + (f", {weight_change_amount}" if nonempty(weight_change_amount) else ""),
    ])

    add_section(summary, "Badania wykonane w ciągu ostatnich 2 lat", [f"• {x}" for x in performed_tests])
    add_section(summary, "Objawy główne", [f"{i+1}. {x}" for i, x in enumerate(main_symptoms)])
    add_section(summary, "Pozostałe dolegliwości", [additional_symptoms])

    add_section(summary, "Charakter objawów", [
        f"Objawy: {symptom_pattern}",
        symptom_periodicity,
        symptom_past,
    ])

    add_section(summary, "Co nasila objawy", [
        list_text(worsen_factors),
        f"Inne: {worsen_other}" if nonempty(worsen_other) else "",
    ])

    add_section(summary, "Co osłabia objawy", [
        list_text(relieve_factors),
        f"Inne: {relieve_other}" if nonempty(relieve_other) else "",
    ])

    add_section(summary, "Chronologia zdrowia", [health_timeline])
    add_section(summary, "Aktualnie przyjmowane leki", [x.strip() for x in current_meds.splitlines() if x.strip()])

    add_section(summary, "Tryb życia", [
        f"Tryb życia: {lifestyle}",
        f"Używki i nawyki: {list_text(stimulants)}" if stimulants else "",
        f"Inne używki lub nawyki: {stimulants_other}" if nonempty(stimulants_other) else "",
        f"Sen: {sleep_hours} godzin na dobę",
    ])

    add_section(summary, "Podróże, zwierzęta, urazy, COVID, stres", [
        f"Wyjazd za granicę: {travel_abroad}" + (f", {travel_where}" if nonempty(travel_where) else ""),
        f"Kontakt lub uraz od zwierzęcia: {animal_contact}" + (f", {animal_contact_details}" if nonempty(animal_contact_details) else ""),
        major_injuries,
        f"COVID-19: {covid}" + (f", {covid_details}" if nonempty(covid_details) else ""),
        strong_stress,
    ])

    add_section(summary, "Informacje o urodzeniu i dzieciństwie", [
        f"Informacje o urodzeniu: {list_text(birth_info)}" if birth_info else "",
        f"Inne informacje o urodzeniu: {birth_info_other}" if nonempty(birth_info_other) else "",
        f"Karmienie mlekiem matki: {breastfeeding}" if nonempty(breastfeeding) else "",
        f"Choroby dzieciństwa: {list_text(childhood_diseases)}" if childhood_diseases else "",
        f"Inne choroby dzieciństwa: {childhood_diseases_other}" if nonempty(childhood_diseases_other) else "",
    ])

    add_section(summary, "Objawy ogólne i neurologiczne", [
        f"Gorączka: {fever_now}" + (f", {fever_details}" if nonempty(fever_details) else ""),
        f"Bóle lub zawroty głowy: {headache_dizziness}" + (f", {headache_dizziness_details}" if nonempty(headache_dizziness_details) else ""),
        headache_assoc,
        hearing_vision,
        attacks,
        sinus_problems,
        nose_problems,
        allergies,
        herpes,
        mouth_corners,
        fresh_food_reaction,
        f"Padaczka: {epilepsy}",
        smell_taste,
        f"Częstość przeziębień: {colds}" if nonempty(colds) else "",
    ])

    add_section(summary, "Układ oddechowy", [
        f"Ból gardła rano: {throat_morning}",
        f"Pieczenie w przełyku: {esophagus_burning}",
        f"Rozpoznana astma: {asthma_dx}",
        f"Zapalenie płuc: {pneumonia}" + (f", {pneumonia_details}" if nonempty(pneumonia_details) else ""),
        dyspnea,
        night_breath,
        chest_heaviness,
        f"Trudności z oddychaniem: {breathing_type}",
        f"Świszczący oddech: {list_text(wheezing)}" if wheezing else "",
        cough,
    ])

    add_section(summary, "Układ sercowo-naczyniowy", [
        chest_pain,
        f"Problemy z ciśnieniem: {pressure_type}",
        f"Aktualne ciśnienie: {current_bp}" if nonempty(current_bp) else "",
        f"Aktualne tętno: {current_hr}" if nonempty(current_hr) else "",
        f"Ból przy nacisku na klatkę piersiową: {pain_press}",
        f"Ból przy zmianie pozycji: {pain_position}",
        palpitations,
    ])

    add_section(summary, "Przewód pokarmowy", [
        f"Problemy z przewodem pokarmowym: {gi_problem}",
        f"Objawy: {list_text(gi_symptoms)}" if gi_symptoms else "",
        worsening_foods,
        gi_infections,
    ])

    add_section(summary, "Układ moczowy", [
        urine_problems,
        f"Liczba mikcji nocnych: {night_urination}",
        f"Ilość wypijanych płynów dziennie: {fluids} l",
    ])

    add_section(summary, "Stawy i mięśnie", [
        joints,
        stiffness,
    ])

    add_section(summary, "Skóra", [
        skin_changes,
        skin_itch,
        f"Trądzik: {acne}" + (f", {acne_details}" if nonempty(acne_details) else ""),
        skin_sensation,
        f"Problemy z gojeniem ran: {wound_healing}" + (f", {wound_healing_details}" if nonempty(wound_healing_details) else ""),
    ])

    add_section(summary, "Sen i psychika", [
        f"Problemy ze snem: {sleep_problem}",
        f"Rodzaj problemów ze snem: {list_text(sleep_problem_types)}" if sleep_problem_types else "",
        f"Kontakt z psychologiem lub psychiatrą: {psych_contact}",
        psych_dx,
    ])

    add_section(summary, "Krążenie obwodowe", [
        f"Obrzęki: {edema}" + (f", {edema_details}" if nonempty(edema_details) else ""),
        calf_pain,
        cold_fingers,
        tingling,
        varicose,
    ])

    add_section(summary, "Odbyt i okolice odbytu", [
        f"Problemy: {list_text(anal_problems)}" if anal_problems else "",
        f"Inne: {anal_other}" if nonempty(anal_other) else "",
    ])

    if sex == "kobieta":
        add_section(summary, "Ginekologia", [
            gyn_problems,
            menstruation,
            f"Pierwsza miesiączka: {first_menses}" if nonempty(first_menses) else "",
            f"Ostatnia miesiączka: {last_menses.isoformat()}" if last_menses else "",
        ])

    if sex == "mężczyzna":
        add_section(summary, "Andrologia", [
            f"Problemy z potencją: {potency}" if nonempty(potency) else "",
        ])

    add_section(summary, "Wywiad rodzinny", [
        f"Mama: {mother_history}" if nonempty(mother_history) else "",
        f"Ojciec: {father_history}" if nonempty(father_history) else "",
        f"Babcia ze strony mamy: {maternal_grandmother}" if nonempty(maternal_grandmother) else "",
        f"Babcia ze strony ojca: {paternal_grandmother}" if nonempty(paternal_grandmother) else "",
        f"Dziadek ze strony mamy: {maternal_grandfather}" if nonempty(maternal_grandfather) else "",
        f"Dziadek ze strony ojca: {paternal_grandfather}" if nonempty(paternal_grandfather) else "",
    ])

    add_section(summary, "Dotychczasowe rozpoznania, operacje i ważne informacje", [
        own_diagnoses,
        important_info,
        current_reason,
        f"Cel wizyty: {visit_reason}",
    ])

    if attachments:
        attachment_names = ", ".join([f.name for f in attachments])
        add_section(summary, "Załączniki", [f"Dołączone pliki: {attachment_names}"])

    add_section(summary, "Informacja końcowa", [
        "Proszę wyślij wszystkie posiadane wyniki badań na adres: niedzialkowski@ocenazdrowia.pl",
        "lub załącz pliki logując się na stronie:",
        "https://aplikacja.medyc.pl/NiedzialkowskiPortal/#/login",
        "Po założeniu konta możesz wgrać pliki bezpośrednio do swojej kartoteki zdrowotnej.",
        "Najlepiej wysłać lub wgrać jeden plik PDF układając wyniki chronologicznie.",
        "Proszę przynieść na wizytę posiadane wyniki badań w formie papierowej.",
        "Bardzo dziękuję.",
    ])

    final_summary = "\n".join(summary).strip()

    st.subheader("Podsumowanie dla lekarza")
    st.text_area("Podsumowanie", value=final_summary, height=900, label_visibility="collapsed")

    pdf_bytes = make_pdf("Ocena stanu zdrowia, wywiad lekarski", final_summary)

    st.download_button(
        "Pobierz PDF",
        data=pdf_bytes,
        file_name="podsumowanie_ankiety_zdrowia.pdf",
        mime="application/pdf",
    )

    st.download_button(
        "Pobierz TXT",
        data=final_summary.encode("utf-8"),
        file_name="podsumowanie_ankiety_zdrowia.txt",
        mime="text/plain",
    )
