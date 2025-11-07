# app.py
import streamlit as st
from datetime import datetime, date, time, timedelta
from dataclasses import dataclass
from typing import Optional, List

# ----------------------------
# CONFIG
# ----------------------------
NUM_SLOTS = 8
VEHICLE_TYPES = ["car", "bike", "heavy"]
RATE = {"car": 20, "bike": 10, "heavy": 30}    # ₹/minute
PREBOOK_SURCHARGE = 0.15                       # 15% extra

USERS = {
    "admin": {"password": "1234", "role": "staff"},
    "user": {"password": "pass", "role": "customer"},
}

# ----------------------------
# DATA MODEL
# ----------------------------
@dataclass
class Slot:
    id: int
    status: str = "empty"         # empty / reserved / occupied
    plate: Optional[str] = None
    vtype: Optional[str] = None
    start_time: Optional[datetime] = None
    reserved_for: Optional[str] = None
    reserve_time: Optional[datetime] = None
    is_prebook: bool = False

    def clear(self):
        self.status = "empty"
        self.plate = None
        self.vtype = None
        self.start_time = None
        self.reserved_for = None
        self.reserve_time = None
        self.is_prebook = False

# ----------------------------
# STATE INIT
# ----------------------------
def init():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "slots" not in st.session_state:
        st.session_state.slots: List[Slot] = [Slot(i+1) for i in range(NUM_SLOTS)]
    if "selected" not in st.session_state:
        st.session_state.selected = None

init()

# ----------------------------
# LOGIN SCREEN
# ----------------------------
def login():
    st.title("🚗 Smart Parking System (Cloud Phase 3)")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.user = username
            st.success("Login Successful ✅")
            st.experimental_rerun()
        else:
            st.error("Invalid Login ❌")

# ----------------------------
# HELPERS
# ----------------------------
def fare(vtype, minutes, pre):
    base = RATE[vtype] * minutes
    if pre:
        base *= (1 + PREBOOK_SURCHARGE)
    return round(base, 2)

def slot_display(s: Slot):
    if s.status == "empty":
        return f"🟩 Slot {s.id} - Empty"
    if s.status == "reserved":
        return f"🟨 Slot {s.id} - Reserved ({s.reserved_for})"
    if s.status == "occupied":
        return f"🟥 Slot {s.id} - {s.plate} ({s.vtype})"
    return f"Slot {s.id}"

# ----------------------------
# MAIN DASHBOARD
# ----------------------------
def dashboard():
    st.write(f"**Logged in as:** {st.session_state.user}")
    if st.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()

    st.subheader("Parking Slots (8 Slots)")
    cols = st.columns(4)
    for i, s in enumerate(st.session_state.slots):
        with cols[i % 4]:
            if st.button(slot_display(s), key=f"slot_{s.id}"):
                st.session_state.selected = s.id

    s = st.session_state.selected
    if not s:
        st.warning("Select a slot above ⬆️")
        return

    slot = st.session_state.slots[s-1]
    st.markdown(f"### Selected Slot: {slot_display(slot)}")

    # --- BOOK NOW ---
    st.write("#### Book Now (Park Immediately)")
    plate = st.text_input("Vehicle Number", key="plate_now")
    vtype = st.selectbox("Vehicle Type", VEHICLE_TYPES, key="vtype_now")
    if st.button("Park Now"):
        if slot.status == "occupied":
            st.error("This slot is already occupied.")
        else:
            slot.status = "occupied"
            slot.plate = plate
            slot.vtype = vtype
            slot.start_time = datetime.now()
            slot.is_prebook = False
            st.success("Vehicle Parked ✅")

    # --- PREBOOK ---
    st.write("#### Pre-Book")
    plate2 = st.text_input("Vehicle Number (Pre-book)", key="plate_pre")
    vtype2 = st.selectbox("Vehicle Type (Pre-book)", VEHICLE_TYPES, key="vtype_pre")
    date_res = st.date_input("Date")
    time_res = st.time_input("Time")
    if st.button("Reserve Slot"):
        slot.status = "reserved"
        slot.reserved_for = st.session_state.user
        slot.reserve_time = datetime.combine(date_res, time_res)
        slot.plate = plate2
        slot.vtype = vtype2
        slot.is_prebook = True
        st.success("Slot Reserved ✅")

    # --- ARRIVED (convert reservation) ---
    if slot.status == "reserved":
        if st.button("Arrived → Start Parking"):
            slot.status = "occupied"
            slot.start_time = datetime.now()
            st.success("Parking Started ✅")

    # --- CHECKOUT ---
    st.write("#### Checkout (Remove Vehicle)")
    if slot.status == "occupied":
        if st.button("Checkout"):
            mins = max(1, int((datetime.now() - slot.start_time).total_seconds() / 60))
            amount = fare(slot.vtype, mins, slot.is_prebook)
            st.success(f"""
### Receipt
Slot: {slot.id}
Vehicle: {slot.plate} ({slot.vtype})
Duration: {mins} min
Pre-booked: {"Yes" if slot.is_prebook else "No"}
**Total Fare: ₹{amount}** ✅
""")
            slot.clear()

    # --- FIND CAR ---
    st.write("#### Search Vehicle by Number")
    q = st.text_input("Enter number to search", key="search")
    if st.button("Find"):
        for sl in st.session_state.slots:
            if sl.plate and sl.plate.lower() == q.lower():
                st.success(f"Vehicle Found → Slot {sl.id}")
                st.session_state.selected = sl.id
                st.experimental_rerun()
        st.error("Not Found ❌")

# ----------------------------
# APP ENTRY
# ----------------------------
if not st.session_state.user:
    login()
else:
    dashboard()
