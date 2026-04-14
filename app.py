import streamlit as st
from datetime import date
import smtplib
from email.message import EmailMessage
import tempfile
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ===== MAIL =====
EMAIL_NADAWCA = "twojmail@gmail.com"
HASLO = "twoje_haslo_aplikacji"
EMAIL_ODBIORCA = "piotr@spirometria.pl"

st.set_page_config(page_title="Ocena zdrowia", layout="centered")

# ===== NAGŁÓWEK =====
st.title("Ocena stanu zdrowia - wywiad lekarski")
st.markdown("### dr n. med. Piotr Niedziałkowski")
st.markdown("📞 Kontakt do recepcji: +48 690 584 584")

# ===== FUNKCJE =====
def inicjaly(imie):
    return " ".join([x[0]+"." for x in imie.split()]) if imie else ""

def generuj_pdf(dane):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp.name)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Ocena stanu zdrowia - wywiad lekarski", styles["Title"]))
    story.append(Spacer(1,10))
    story.append(Paragraph("dr n. med. Piotr Niedziałkowski", styles["Normal"]))
    story.append(Spacer(1,10))

    for k,v in dane.items():
        story.append(Paragraph(f"<b>{k}</b>: {v}", styles["Normal"]))
        story.append(Spacer(1,8))

    doc.build(story)
    return tmp.name

def wyslij_mail(pdf, tresc):
    msg = EmailMessage()
    msg["Subject"] = "Nowy wywiad pacjenta"
    msg["From"] = EMAIL_NADAWCA
    msg["To"] = EMAIL_ODBIORCA
    msg.set_content(tresc)

    with open(pdf, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="wywiad.pdf")

    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login(EMAIL_NADAWCA, HASLO)
        smtp.send_message(msg)

# ===== FORMULARZ =====
with st.form("form"):

    st.subheader("Dane podstawowe")
    imie = st.text_input("Imię i nazwisko")
    telefon = st.text_input("Telefon")
    email = st.text_input("Email")
    data_urodzenia = st.date_input("Data urodzenia")

    st.subheader("Stan zdrowia")
    fiz = st.slider("Stan fizyczny",0,10)
    psy = st.slider("Stan psychiczny",0,10)

    st.subheader("Objawy główne")
    obj1 = st.text_input("Objaw 1")
    obj2 = st.text_input("Objaw 2")
    obj3 = st.text_input("Objaw 3")
    obj4 = st.text_input("Objaw 4")
    obj5 = st.text_input("Objaw 5")

    st.subheader("Pozostałe objawy")
    inne_obj = st.text_area("Inne objawy")

    st.subheader("Leki")
    leki = st.text_area("Jakie leki przyjmujesz")

    st.subheader("Styl życia")
    tryb = st.selectbox("Tryb życia",["niski","średni","wysoki"])
    sen = st.selectbox("Ile śpisz",["5","6","7","8","9"])

    st.subheader("Choroby")
    choroby = st.text_area("Choroby przewlekłe")

    st.subheader("Układ oddechowy")
    kaszel = st.text_area("Kaszel / duszność")

    st.subheader("Układ krążenia")
    serce = st.text_area("Objawy sercowe")

    st.subheader("Układ pokarmowy")
    brzuch = st.text_area("Objawy jelitowe")

    st.subheader("Układ nerwowy")
    glowa = st.text_area("Bóle głowy / zawroty")

    st.subheader("Skóra")
    skora = st.text_area("Zmiany skórne")

    st.subheader("Wywiad rodzinny")
    rodzina = st.text_area("Choroby w rodzinie")

    st.subheader("Powód wizyty")
    powod = st.text_area("Dlaczego zgłaszasz się")

    st.subheader("Zgody")

    zgoda = st.checkbox("Zgadzam się na przetwarzanie danych do przygotowania wizyty")
    prawda = st.checkbox("Potwierdzam że dane są prawdziwe")

    submit = st.form_submit_button("Wyślij")

# ===== WYSYŁKA =====
if submit:

    if not zgoda or not prawda:
        st.error("Zaznacz zgody")
    else:
        inic = inicjaly(imie)

        dane = {
            "Pacjent": inic,
            "Telefon": telefon,
            "Data urodzenia": str(data_urodzenia),
            "Stan fizyczny": fiz,
            "Stan psychiczny": psy,
            "Objawy": f"{obj1}, {obj2}, {obj3}, {obj4}, {obj5}",
            "Inne objawy": inne_obj,
            "Leki": leki,
            "Styl życia": tryb,
            "Sen": sen,
            "Choroby": choroby,
            "Oddech": kaszel,
            "Serce": serce,
            "Brzuch": brzuch,
            "Neurologia": glowa,
            "Skóra": skora,
            "Rodzina": rodzina,
            "Powód": powod
        }

        pdf = generuj_pdf(dane)

        tresc = f"""
NOWY PACJENT

{imie}
Telefon: {telefon}
"""

        wyslij_mail(pdf, tresc)

        st.success("Wysłano formularz")
