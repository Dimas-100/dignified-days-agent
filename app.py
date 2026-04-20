import streamlit as st
import anthropic
import io
import re
import json
import base64
import asyncio
import edge_tts
import streamlit.components.v1 as components
from streamlit_mic_recorder import speech_to_text

# ── API Client ─────────────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# ══════════════════════════════════════════════════════════════════════════════
# PATIENT DATABASE
# ══════════════════════════════════════════════════════════════════════════════
PATIENTS = {
    "margaret johnson": {
        "order_number": "DD-10001",
        "name": "Margaret Johnson",
        "equipment": "Hospital Bed",
        "delivery_date": "April 4, 2026",
        "delivery_window": "10:00 AM to 2:00 PM",
        "address": "123 Peachtree St, Atlanta, GA",
        "phone": "404-555-1001",
        "dob": "03/12/1942",
        "insurance": "Medicare",
        "insurance_coverage": "Medicare covers 80% of the rental cost. The remaining 20% is billed to the secondary insurance on file.",
        "copay": "No out-of-pocket copay expected based on current coverage.",
        "billing_status": "No outstanding balance.",
        "return_scheduled": False,
        "return_date": None,
        "return_window": None,
        "delivery_status": "On time",
        "driver_name": "Marcus T.",
        "driver_phone": "404-555-9101",
        "driver_status": "Driver is loaded and departing the warehouse this morning.",
        "equipment_setup_notes": "Our technician will assemble the bed on arrival. Please clear a space of at least 7 feet by 4 feet in the room.",
        "equipment_issue": None,
        "technician_notes": "Standard delivery, no special instructions.",
        "special_instructions": "Please have an adult present at the time of delivery to sign for the equipment."
    },
    "robert davis": {
        "order_number": "DD-10002",
        "name": "Robert Davis",
        "equipment": "Oxygen Concentrator",
        "delivery_date": "April 5, 2026",
        "delivery_window": "8:00 AM to 12:00 PM",
        "address": "456 Magnolia Ave, Birmingham, AL",
        "phone": "205-555-2002",
        "dob": "07/23/1938",
        "insurance": "Medicaid",
        "insurance_coverage": "Medicaid covers the full rental cost for approved home hospice equipment.",
        "copay": "No copay required under current Medicaid plan.",
        "billing_status": "No outstanding balance.",
        "return_scheduled": False,
        "return_date": None,
        "return_window": None,
        "delivery_status": "Delivered",
        "driver_name": "Sandra K.",
        "driver_phone": "205-555-9202",
        "driver_status": "Equipment was successfully delivered on April 5th.",
        "equipment_setup_notes": "The concentrator was plugged in and tested by our technician on arrival. Flow rate set to 2 liters per minute as prescribed. Tubing and nasal cannula connected and demonstrated to family.",
        "equipment_issue": "Unit was delivered and working. Common issues: power loss if unplugged, alarm if tubing is kinked or disconnected, reduced flow if air filter is clogged.",
        "technician_notes": "Patient requires oxygen at 2 liters per minute.",
        "special_instructions": "Please ensure there is an accessible power outlet near the patient bedside. Do not use an extension cord."
    },
    "helen carter": {
        "order_number": "DD-10003",
        "name": "Helen Carter",
        "equipment": "Wheelchair",
        "delivery_date": "April 3, 2026",
        "delivery_window": "12:00 PM to 4:00 PM",
        "address": "789 Oak Street, Savannah, GA",
        "phone": "912-555-3003",
        "dob": "11/05/1945",
        "insurance": "Blue Cross",
        "insurance_coverage": "Blue Cross covers the rental under the durable medical equipment benefit. A prior authorization was obtained.",
        "copay": "Patient is responsible for a $25 monthly copay.",
        "billing_status": "Current. Last payment received March 15, 2026.",
        "return_scheduled": True,
        "return_date": "April 10, 2026",
        "return_window": "10:00 AM to 2:00 PM",
        "delivery_status": "Delivered",
        "driver_name": "James R.",
        "driver_phone": "912-555-9303",
        "driver_status": "Equipment was successfully delivered on April 3rd. Return pickup is scheduled for April 10th.",
        "equipment_setup_notes": "Wheelchair was adjusted to patient size on delivery. Brakes and footrests confirmed functional.",
        "equipment_issue": None,
        "technician_notes": "Return already scheduled for April 10.",
        "special_instructions": "Please have the wheelchair near the front door on pickup day."
    },
    "james wilson": {
        "order_number": "DD-10004",
        "name": "James Wilson",
        "equipment": "Hospital Bed and Bedside Commode",
        "delivery_date": "April 6, 2026",
        "delivery_window": "10:00 AM to 2:00 PM",
        "address": "321 Elm Drive, Jacksonville, FL",
        "phone": "904-555-4004",
        "dob": "02/14/1940",
        "insurance": "Medicare",
        "insurance_coverage": "Medicare covers 80% of rental for both items. Secondary insurance on file covers the remaining 20%.",
        "copay": "No out-of-pocket copay expected.",
        "billing_status": "No outstanding balance.",
        "return_scheduled": False,
        "return_date": None,
        "return_window": None,
        "delivery_status": "On time",
        "driver_name": "Tony B.",
        "driver_phone": "904-555-9404",
        "driver_status": "Both items are loaded together and delivery is on schedule.",
        "equipment_setup_notes": "Both items will be set up by our technician. Please clear space for the bed and place the commode near the bathroom.",
        "equipment_issue": None,
        "technician_notes": "Two items on order, deliver together.",
        "special_instructions": "Both items must be delivered and signed for together. Do not accept a partial delivery."
    },
    "dorothy harris": {
        "order_number": "DD-10005",
        "name": "Dorothy Harris",
        "equipment": "Rollator Walker",
        "delivery_date": "April 4, 2026",
        "delivery_window": "2:00 PM to 6:00 PM",
        "address": "654 Pine Blvd, Montgomery, AL",
        "phone": "334-555-5005",
        "dob": "09/30/1950",
        "insurance": "Aetna",
        "insurance_coverage": "Aetna covers durable medical equipment at 80% after the deductible is met.",
        "copay": "Patient may owe up to $40 depending on deductible status. Billing will confirm after delivery.",
        "billing_status": "No outstanding balance. Deductible status pending confirmation.",
        "return_scheduled": False,
        "return_date": None,
        "return_window": None,
        "delivery_status": "Slight delay",
        "driver_name": "Keisha M.",
        "driver_phone": "334-555-9505",
        "driver_status": "Driver is running about 45 minutes behind due to traffic. Expected arrival is closer to 3:00 PM.",
        "equipment_setup_notes": "The rollator comes pre-assembled. Our technician will adjust the height for the patient and walk the family through safe use.",
        "equipment_issue": None,
        "technician_notes": "Patient prefers afternoon delivery.",
        "special_instructions": "Patient requested afternoon delivery. Please confirm someone is home after 2 PM."
    },
    "charles martinez": {
        "order_number": "DD-10006",
        "name": "Charles Martinez",
        "equipment": "Suction Machine",
        "delivery_date": "April 7, 2026",
        "delivery_window": "8:00 AM to 12:00 PM",
        "address": "987 Riverside Rd, Tampa, FL",
        "phone": "813-555-6006",
        "dob": "06/18/1935",
        "insurance": "Medicaid",
        "insurance_coverage": "Medicaid covers the full cost of the suction machine rental under the hospice benefit.",
        "copay": "No copay required.",
        "billing_status": "No outstanding balance.",
        "return_scheduled": False,
        "return_date": None,
        "return_window": None,
        "delivery_status": "On time",
        "driver_name": "Luis G.",
        "driver_phone": "813-555-9606",
        "driver_status": "Marked urgent. Driver is prioritizing this delivery and is on track for early morning arrival.",
        "equipment_setup_notes": "Technician will demonstrate how to operate the suction machine, clean the tubing, and handle an emergency shutoff.",
        "equipment_issue": None,
        "technician_notes": "Urgent delivery, patient needs unit by morning.",
        "special_instructions": "This is an urgent delivery. Please ensure someone is available from 8 AM onward."
    },
    "patricia thompson": {
        "order_number": "DD-10007",
        "name": "Patricia Thompson",
        "equipment": "Hospital Bed and Oxygen Concentrator",
        "delivery_date": "April 5, 2026",
        "delivery_window": "10:00 AM to 2:00 PM",
        "address": "147 Willow Lane, Augusta, GA",
        "phone": "706-555-7007",
        "dob": "04/02/1948",
        "insurance": "Medicare",
        "insurance_coverage": "Medicare covers 80% for both items. No secondary insurance on file — patient is responsible for the remaining 20% coinsurance.",
        "copay": "Patient is responsible for 20% coinsurance. Estimated monthly cost is approximately $45.",
        "billing_status": "First invoice sent April 6, 2026. Balance of $45 currently due. Patient has not yet paid.",
        "billing_dispute_note": "Billing disputes and insurance coverage changes cannot be processed by this system and require a billing specialist.",
        "return_scheduled": False,
        "return_date": None,
        "return_window": None,
        "delivery_status": "Delivered",
        "driver_name": "Angela F.",
        "driver_phone": "706-555-9707",
        "driver_status": "Both items were successfully delivered on April 5th.",
        "equipment_setup_notes": "Bed assembled in master bedroom. Concentrator plugged in, tested, and set to prescribed flow rate. Family received full usage walkthrough.",
        "equipment_issue": None,
        "technician_notes": "Two items, family prefers morning setup.",
        "special_instructions": "Family prefers setup to be completed before noon if possible."
    },
    "william anderson": {
        "order_number": "DD-10008",
        "name": "William Anderson",
        "equipment": "Wheelchair",
        "delivery_date": "April 3, 2026",
        "delivery_window": "12:00 PM to 4:00 PM",
        "address": "258 Cypress Ave, Pensacola, FL",
        "phone": "850-555-8008",
        "dob": "12/27/1943",
        "insurance": "Blue Cross",
        "insurance_coverage": "Blue Cross covers the rental under the durable medical equipment benefit.",
        "copay": "Patient is responsible for a $25 monthly copay.",
        "billing_status": "Current. No outstanding balance.",
        "return_scheduled": True,
        "return_date": "April 12, 2026",
        "return_window": "9:00 AM to 1:00 PM",
        "delivery_status": "Delivered",
        "driver_name": "Devon C.",
        "driver_phone": "850-555-9808",
        "driver_status": "Equipment was successfully delivered. Return pickup scheduled for April 12th.",
        "equipment_setup_notes": "Wheelchair was fitted and brakes confirmed functional on delivery.",
        "equipment_issue": None,
        "technician_notes": "Return pickup requested, coordinate with family.",
        "special_instructions": "Family requested coordination before pickup. Please call ahead at least one hour before arrival."
    },
    "barbara jackson": {
        "order_number": "DD-10009",
        "name": "Barbara Jackson",
        "equipment": "Hospital Bed",
        "delivery_date": "April 8, 2026",
        "delivery_window": "8:00 AM to 12:00 PM",
        "address": "369 Maple Court, Columbus, GA",
        "phone": "706-555-9009",
        "dob": "08/15/1952",
        "insurance": "Humana",
        "insurance_coverage": "Humana covers durable medical equipment at 80% after prior authorization, which has been approved.",
        "copay": "Patient is responsible for a $30 monthly copay.",
        "billing_status": "No outstanding balance. First bill will be sent after delivery.",
        "return_scheduled": False,
        "return_date": None,
        "return_window": None,
        "delivery_status": "On time",
        "driver_name": "Ray P.",
        "driver_phone": "706-555-9909",
        "driver_status": "Driver is scheduled and on track. First floor delivery noted in the order.",
        "equipment_setup_notes": "First floor delivery only — no elevator access. Technician is aware and will bring appropriate equipment.",
        "equipment_issue": None,
        "technician_notes": "First floor delivery only, no elevator.",
        "special_instructions": "Delivery must be completed on the first floor only. Do not attempt stairs."
    },
    "richard white": {
        "order_number": "DD-10010",
        "name": "Richard White",
        "equipment": "Oxygen Concentrator and Rollator Walker",
        "delivery_date": "April 6, 2026",
        "delivery_window": "2:00 PM to 6:00 PM",
        "address": "741 Birch Street, Huntsville, AL",
        "phone": "256-555-0010",
        "dob": "01/09/1937",
        "insurance": "Medicare",
        "insurance_coverage": "Medicare covers 80% for both items. Secondary insurance on file covers the remaining 20%.",
        "copay": "No out-of-pocket copay expected.",
        "billing_status": "No outstanding balance.",
        "return_scheduled": False,
        "return_date": None,
        "return_window": None,
        "delivery_status": "On time",
        "driver_name": "Nina S.",
        "driver_phone": "256-555-9010",
        "driver_status": "Both items confirmed loaded. Family has been notified to speak clearly with the patient.",
        "equipment_setup_notes": "Concentrator will be set to prescribed flow rate and tested. Walker height will be adjusted. Family will receive full usage instructions — patient is hard of hearing so all communication should go through family.",
        "equipment_issue": None,
        "technician_notes": "Patient is hard of hearing, speak clearly with family.",
        "special_instructions": "All communication should be directed to the family, not the patient directly."
    }
}

AVAILABLE_SLOTS = [
    "morning, from 8 in the morning to noon",
    "afternoon, from noon to 4 in the afternoon",
    "evening, from 4 to 7 in the evening"
]

GREETING = (
    "Thank you for calling Dignified Days. My name is Dana, and I am so glad you reached out today. "
    "How can I help you?"
)

# ══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS  (this is what makes it Agentic AI — agents calling tools)
# ══════════════════════════════════════════════════════════════════════════════

TOOLS = [
    {
        "name": "lookup_patient_record",
        "description": (
            "Look up a patient record by order number or patient name. "
            "Always try the order number first. Returns full account details including "
            "equipment, delivery info, insurance, and technician notes. "
            "Call this tool as soon as you have the order number or patient name."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_name": {
                    "type": "string",
                    "description": "The order number (e.g. DD-10005) or full/partial patient name."
                }
            },
            "required": ["patient_name"]
        }
    },
    {
        "name": "route_to_delivery_agent",
        "description": (
            "Route this call to the Delivery Status Agent. Use when the caller is asking "
            "about delivery status, tracking, or when their equipment will arrive."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Brief reason for routing to the delivery agent."
                }
            },
            "required": ["reason"]
        }
    },
    {
        "name": "route_to_scheduling_agent",
        "description": (
            "Route this call to the Return Scheduling Agent. Use when the caller wants to "
            "schedule, reschedule, or cancel an equipment return or pickup."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Brief reason for routing to the scheduling agent."
                }
            },
            "required": ["reason"]
        }
    },
    {
        "name": "route_to_triage_agent",
        "description": (
            "Route this call to the Equipment Triage Agent. Use when the caller reports "
            "equipment that is not working, malfunctioning, or broken."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Brief reason for routing to the triage agent."
                }
            },
            "required": ["reason"]
        }
    },
    {
        "name": "schedule_return_pickup",
        "description": (
            "Schedule a return pickup for a patient's equipment. Call this after the caller "
            "has chosen a preferred time slot."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_name": {
                    "type": "string",
                    "description": "The patient's full name."
                },
                "time_slot": {
                    "type": "string",
                    "description": "The chosen time slot: morning, afternoon, or evening."
                }
            },
            "required": ["patient_name", "time_slot"]
        }
    },
    {
        "name": "escalate_to_human_csr",
        "description": (
            "Escalate this call to a human CSR. Use when the caller is upset, cannot be helped "
            "by the agent, or specifically requests a human representative."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Reason for escalation."
                },
                "patient_name": {
                    "type": "string",
                    "description": "Patient name if known, otherwise 'unknown'."
                },
                "summary": {
                    "type": "string",
                    "description": "Brief summary of the call so far for the human CSR."
                }
            },
            "required": ["reason", "patient_name", "summary"]
        }
    }
]

# ══════════════════════════════════════════════════════════════════════════════
# TOOL EXECUTION  (what actually happens when an agent calls a tool)
# ══════════════════════════════════════════════════════════════════════════════

def execute_tool(tool_name, tool_input):
    """Execute a tool call and return the result as a string."""

    if tool_name == "lookup_patient_record":
        query = tool_input.get("patient_name", "").strip().lower()

        # Try order number match first (exact, case-insensitive)
        found = None
        for key, patient in PATIENTS.items():
            if patient.get("order_number", "").lower() == query:
                found = patient
                break

        # Fall back to fuzzy name match
        if not found:
            for key, patient in PATIENTS.items():
                name_parts = key.split()
                for part in name_parts:
                    if part in query and len(part) > 2:
                        found = patient
                        break
                if found:
                    break

        if found:
            return json.dumps({"status": "found", "patient": found})
        else:
            return json.dumps({
                "status": "not_found",
                "message": f"No record found for '{tool_input.get('patient_name')}'. Please double check the order number."
            })

    elif tool_name == "route_to_delivery_agent":
        st.session_state.active_agent = "delivery"
        st.session_state.pending_agent = "delivery"
        st.session_state.agent_log.append("→ Routed to Delivery Status Agent")
        return json.dumps({"status": "routed", "agent": "delivery"})

    elif tool_name == "route_to_scheduling_agent":
        st.session_state.active_agent = "scheduling"
        st.session_state.pending_agent = "scheduling"
        st.session_state.agent_log.append("→ Routed to Return Scheduling Agent")
        return json.dumps({"status": "routed", "agent": "scheduling"})

    elif tool_name == "route_to_triage_agent":
        st.session_state.active_agent = "triage"
        st.session_state.pending_agent = "triage"
        st.session_state.agent_log.append("→ Routed to Equipment Triage Agent")
        return json.dumps({"status": "routed", "agent": "triage"})

    elif tool_name == "schedule_return_pickup":
        patient_name = tool_input.get("patient_name", "the patient")
        time_slot = tool_input.get("time_slot", "morning")
        st.session_state.agent_log.append(
            f"✓ Pickup scheduled for {patient_name} — {time_slot}"
        )
        return json.dumps({
            "status": "confirmed",
            "confirmation_number": "DD-2026-" + str(abs(hash(patient_name)) % 9000 + 1000),
            "patient": patient_name,
            "slot": time_slot,
            "message": f"Return pickup scheduled for {patient_name} during the {time_slot}. A text confirmation will be sent."
        })

    elif tool_name == "escalate_to_human_csr":
        st.session_state.active_agent = "escalate"
        st.session_state.pending_agent = "escalate"
        st.session_state.escalation_summary = tool_input.get("summary", "")
        st.session_state.agent_log.append(
            f"⚠ Escalated to human CSR — {tool_input.get('reason', '')}"
        )
        return json.dumps({
            "status": "escalated",
            "message": "A human CSR has been notified and will join the call shortly.",
            "summary_for_csr": tool_input.get("summary", "")
        })

    return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})


# ══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR AGENT  (the main agent that routes and uses tools)
# ══════════════════════════════════════════════════════════════════════════════

ORCHESTRATOR_SYSTEM = """Your name is Dana. You are a warm and caring AI customer service agent for Dignified Days.
Dignified Days delivers rental medical equipment to home hospice patients across Georgia, Alabama, and Florida.

You have access to tools that allow you to look up patient records, route calls to specialist agents,
schedule pickups, and escalate to human CSRs when needed.

Your workflow — follow this exactly:
1. Greet the caller warmly as Dana and understand what they need.
2. Ask for the order number. Say: "Could I get your order number? It should start with DD followed by five digits."
3. The moment you have an order number or name, call lookup_patient_record immediately.
4. The moment lookup_patient_record returns a result, call the correct routing tool immediately
   based on what the caller originally asked for. Do this in the same turn without waiting.
5. After routing, respond directly to the caller as Dana, answering their question naturally.

Routing rules:
- Delivery questions (status, delays, timing, driver, preparation) → route_to_delivery_agent
- Return or pickup scheduling → route_to_scheduling_agent
- Equipment not working, broken, or making noise → route_to_triage_agent
- Insurance, billing, copay, or coverage questions → answer directly using insurance_coverage,
  copay, and billing_status fields from the patient record — no routing needed.
- If truly unanswerable from the data → escalate_to_human_csr

CRITICAL RULES:
- Never tell the caller you are connecting them to another agent or department.
- Never mention the Delivery Status Agent, Scheduling Agent, Triage Agent, or any internal system.
- Never say you are transferring the call.
- Never say certainly or absolutely — those sound robotic.
- Route silently. The caller experiences one seamless conversation with Dana only.
- If a patient is not found after 2 attempts, call escalate_to_human_csr.
- Keep every response to 1 to 3 sentences. Answer only what was asked. Do not add information the caller did not ask for.
- If the caller says "okay", "thank you", "got it", or similar with no follow-up question, ask "Is there anything else I can help you with today?"
- If the caller says "no", "no thank you", "that is all", or anything indicating they are done,
  close the call with: "Thank you so much for calling Dignified Days. We hope [patient name] is
  comfortable and well cared for. Please do not hesitate to call us back anytime. Take care."
  Then stop — do not ask another question.
- Never start a response with filler phrases like "I am glad you called", "Great news", or "I am happy to help" — go straight to the answer.
- No bullet points, headers, lists, or emojis — only natural flowing speech.
- These families are going through a very difficult time. Show genuine empathy."""


DELIVERY_AGENT_SYSTEM = """Your name is Dana. You are a warm and caring AI customer service agent for Dignified Days.
You are handling a delivery inquiry. The verified patient account is already in the conversation history.

Continue the conversation naturally — do not reintroduce yourself, do not acknowledge any handoff.
Just answer the caller directly as if you have always had this information.

Use these fields from the patient record to answer any delivery question:
- delivery_status: on time, slight delay, or delivered
- driver_status: real-time detail on driver location or situation
- driver_name and driver_phone: who the driver is and how to reach them
- delivery_date and delivery_window: scheduled date and time
- address: confirmed delivery address
- equipment_setup_notes: what the technician will do on arrival and how to prepare
- special_instructions: anything the family needs to know or do before delivery

Common questions you can answer using this data:
- Is it on time / will there be delays? Use delivery_status and driver_status.
- Who is the driver? Use driver_name.
- What time will they arrive? Use delivery_window and driver_status.
- What do we need to do to prepare? Use equipment_setup_notes and special_instructions.
- What if no one is home? Let them know an adult must be present to sign, and offer to reschedule.
- Can I change the delivery address? Let them know address changes require a CSR and use escalate_to_human_csr.

If a question cannot be answered with the data available, use escalate_to_human_csr.
Use schedule_return_pickup if the caller also wants to arrange a return pickup.

RESPONSE RULES — follow strictly:
- Keep every response to 1 to 3 sentences. Answer only what was asked — nothing more.
- Never volunteer extra information the caller did not ask for.
- If the caller says something like "okay", "thank you", "got it", or "alright" with no question,
  ask warmly "Is there anything else I can help you with today?"
- If the caller says "no", "no thank you", "that is all", "I am good", or anything indicating
  they are done, close the call with:
  "Thank you so much for calling Dignified Days. We hope [patient name] is comfortable and
  well cared for. Please do not hesitate to call us back anytime. Take care."
  Then stop completely — do not ask another question.
- Never start a response with filler phrases like "I am glad you called" or "Great news" —
  go straight to the answer.
- No bullet points, headers, or emojis. Never say certainly or absolutely.
- These families are going through a very hard time."""


SCHEDULING_AGENT_SYSTEM = """Your name is Dana. You are a warm and caring AI customer service agent for Dignified Days.
You are handling a return scheduling request. The verified patient account is already in the conversation history.

Continue the conversation naturally — do not reintroduce yourself or acknowledge any handoff.
Just pick up exactly where the conversation left off and help the caller efficiently.

Use these fields from the patient record to answer any scheduling question:
- return_scheduled: whether a return is already scheduled
- return_date and return_window: the existing scheduled return date and time if applicable
- equipment: what is being picked up
- address: pickup location
- special_instructions: anything to flag for the pickup

Common questions you can answer:
- When can you pick it up? Offer three slots: morning (8am to noon), afternoon (noon to 4pm), evening (4pm to 7pm).
- Is a return already scheduled? Check return_scheduled, return_date, and return_window.
- How do I prepare the equipment for pickup? Ask them to have it near the front door, cleaned if possible,
  with any accessories included such as chargers, tubing, or cushions.
- Will I get a confirmation? Yes — once scheduled, a text confirmation will be sent to the phone on file.
- Can I reschedule? Yes — call back at least 24 hours before the pickup window to reschedule.
- Will there be a charge for the pickup? No, return pickup is included at no additional cost.

Once the caller chooses a time slot, call schedule_return_pickup to confirm and generate a confirmation number.
If a question cannot be answered with the data available, use escalate_to_human_csr.

Keep every response to 1 to 3 sentences. Answer only what was asked — nothing more.
If the caller says "okay", "thank you", or similar with no question, ask "Is there anything else I can help you with today?"
If the caller says "no", "no thank you", "that is all", or anything indicating they are done, close the call with:
"Thank you so much for calling Dignified Days. We hope [patient name] is comfortable and well cared for. Please do not hesitate to call us back anytime. Take care."
Then stop completely — do not ask another question.
Never start with filler phrases like "I am glad you called" or "Great news" — go straight to the answer.
No bullet points, headers, or emojis. Never say certainly or absolutely."""


TRIAGE_AGENT_SYSTEM = """Your name is Dana. You are a warm and caring AI customer service agent for Dignified Days.
You are handling an equipment issue. The verified patient account is already in the conversation history.

Continue the conversation naturally — do not reintroduce yourself or acknowledge any handoff.
Just pick up exactly where the conversation left off and help the caller efficiently.

Use these fields from the patient record:
- equipment: what type of equipment they have — use this to tailor your troubleshooting
- equipment_setup_notes: how the equipment was set up and what the technician showed them
- technician_notes: any known issues or special circumstances

Troubleshooting guidance by equipment type:
- Hospital Bed: check the power cord is plugged in, the control handset is connected, and the
  outlet is working. Try a different outlet if needed.
- Oxygen Concentrator: check the power cord, make sure the air filter is not blocked, confirm
  the flow setting matches the prescription, and check that tubing is not kinked or disconnected.
- Wheelchair: check the brakes are released for movement, footrests are properly attached,
  and the seat cushion is properly positioned.
- Rollator Walker: check the brakes are not locked, the height is properly adjusted, and
  all four legs or wheels are making contact with the floor.
- Suction Machine: check the power cord, confirm the canister is properly sealed, check the
  tubing for blockages, and make sure the suction setting is not at zero.
- Bedside Commode: check that all four legs are level and locked, and the seat is properly secured.

General approach:
- Stay calm and reassuring. Most issues are user error.
- Walk through one step at a time — do not overwhelm the caller.
- If the issue is resolved, confirm the equipment is working before ending the call.
- If the issue cannot be resolved after troubleshooting, call escalate_to_human_csr with a clear
  summary so a technician can be dispatched. Include the equipment type and what was tried.

Common questions you can answer:
- Is it covered under warranty? All rental equipment is maintained and serviced by Dignified Days
  at no additional cost to the patient.
- How do I get a replacement? If the equipment cannot be fixed remotely, we will send a technician
  or bring a replacement unit — use escalate_to_human_csr to initiate this.
- Is it safe to use? If there is any doubt, advise the caller not to use the equipment until a
  technician has inspected it, and escalate immediately.

Keep every response to 1 to 3 sentences. Ask one troubleshooting question at a time — never stack multiple steps.
If the caller says "okay", "got it", or similar with no new information, ask the next single troubleshooting step.
If the issue is confirmed resolved and the caller indicates they are done, close the call with:
"I am really glad we got that sorted out. Thank you for calling Dignified Days — please do not hesitate to call us back if anything else comes up. Take care."
Then stop completely — do not ask another question.
Never start with filler phrases like "I am glad you called" or "I understand" — go straight to the next step.
No bullet points, headers, or emojis. These families are under enormous stress — be their calm in the storm."""


def get_system_prompt():
    """Return the system prompt for whichever agent is currently active."""
    agent = st.session_state.get("active_agent", "orchestrator")
    prompts = {
        "orchestrator": ORCHESTRATOR_SYSTEM,
        "delivery":     DELIVERY_AGENT_SYSTEM,
        "scheduling":   SCHEDULING_AGENT_SYSTEM,
        "triage":       TRIAGE_AGENT_SYSTEM,
    }
    return prompts.get(agent, ORCHESTRATOR_SYSTEM)


def run_agentic_turn(conversation_history):
    """
    Run one full agentic turn: call Claude with tools, handle any tool calls,
    then return the final text response. This is the core agentic loop.
    """
    messages = conversation_history.copy()
    final_text = ""

    # Agentic loop — keep going until Claude stops calling tools
    for _ in range(10):  # max 10 tool calls per turn (safety limit)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            system=get_system_prompt(),
            tools=TOOLS,
            messages=messages
        )

        # Collect any text Claude produced this step
        for block in response.content:
            if block.type == "text":
                final_text = block.text

        # If Claude is done (no more tool calls), return the response
        if response.stop_reason == "end_turn":
            break

        # If Claude wants to use tools, execute them
        if response.stop_reason == "tool_use":
            # Add Claude's response (including tool_use blocks) to history
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Execute each tool and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_label = {
                        "lookup_patient_record": f"Looking up patient: {block.input.get('patient_name', '')}",
                        "route_to_delivery_agent": "Routing to Delivery Agent",
                        "route_to_scheduling_agent": "Routing to Scheduling Agent",
                        "route_to_triage_agent": "Routing to Triage Agent",
                        "schedule_return_pickup": f"Scheduling pickup for {block.input.get('patient_name', '')} — {block.input.get('time_slot', '')}",
                        "escalate_to_human_csr": f"Escalating to human CSR — {block.input.get('reason', '')}"
                    }.get(block.name, block.name)
                    st.session_state.agent_log.append(f"🔧 {tool_label}")
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Add tool results back to history so Claude can continue
            messages.append({
                "role": "user",
                "content": tool_results
            })
        else:
            break

    return final_text, messages


# ══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def clean_for_speech(text):
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'\*\*?(.*?)\*\*?', r'\1', text)
    text = re.sub(r'#{1,6}\s?', '', text)
    text = re.sub(r'\n+', ' ', text).strip()
    return text

def clean_for_display(text):
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text.strip()

def speak(text):
    """Convert text to speech using edge-tts neural voice and autoplay via HTML."""
    try:
        clean = clean_for_speech(text)
        # Use Microsoft neural voice — sounds natural and warm
        # Female voices: en-US-JennyNeural, en-US-AriaNeural
        # Male voices:   en-US-GuyNeural, en-US-DavisNeural
        voice = "en-US-JennyNeural"
        audio_buffer = io.BytesIO()

        async def _synthesize():
            communicate = edge_tts.Communicate(clean, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])

        asyncio.run(_synthesize())
        audio_buffer.seek(0)
        b64 = base64.b64encode(audio_buffer.read()).decode()

        # Use a unique ID per message so each injection is treated as a new element
        uid = abs(hash(clean)) % 999999
        components.html(
            f"""
            <audio id="tts-{uid}" autoplay>
              <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            <script>
              (function() {{
                var a = document.getElementById('tts-{uid}');
                if (a) a.play().catch(function(){{}});
              }})();
            </script>
            """,
            height=1,
        )
    except Exception as e:
        st.caption(f"Audio unavailable: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Dignified Days Support", page_icon="🏥", layout="centered")
st.markdown("## Dignified Days — AI Customer Support Line")
st.markdown("*Compassionate care, powered by intelligent technology*")
st.divider()

# ── Session State ──────────────────────────────────────────────────────────────
defaults = {
    "messages":           [],
    "display_messages":   [],
    "active_agent":       "orchestrator",
    "pending_agent":      None,
    "agent_log":          [],
    "call_started":       False,
    "last_spoken":        None,
    "pending_speech":     None,
    "escalation_summary": ""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Apply pending agent before sidebar renders ─────────────────────────────────
if st.session_state.pending_agent:
    st.session_state.active_agent = st.session_state.pending_agent
    st.session_state.pending_agent = None

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Active Agent")
    agent_labels = {
        "orchestrator": "Orchestrator Agent",
        "delivery":     "Delivery Status Agent",
        "scheduling":   "Return Scheduling Agent",
        "triage":       "Equipment Triage Agent",
        "escalate":     "Transferred to Human CSR"
    }
    agent_colors = {
        "orchestrator": "info",
        "delivery":     "success",
        "scheduling":   "success",
        "triage":       "warning",
        "escalate":     "error"
    }
    color = agent_colors.get(st.session_state.active_agent, "info")
    label = agent_labels.get(st.session_state.active_agent, "Active")
    if color == "info":
        st.info(label)
    elif color == "success":
        st.success(label)
    elif color == "warning":
        st.warning(label)
    else:
        st.error(label)

    if st.session_state.agent_log:
        st.divider()
        st.markdown("### Agent Activity Log")
        for entry in st.session_state.agent_log[-8:]:
            st.caption(entry)

    if st.session_state.escalation_summary:
        st.divider()
        st.markdown("### CSR Handoff Summary")
        st.info(st.session_state.escalation_summary)

    st.divider()
    st.markdown("### Demo Order Numbers")
    st.markdown("""
| Order | Patient |
|-------|---------|
| DD-10001 | Margaret Johnson |
| DD-10002 | Robert Davis |
| DD-10003 | Helen Carter |
| DD-10004 | James Wilson |
| DD-10005 | Dorothy Harris |
| DD-10006 | Charles Martinez |
| DD-10007 | Patricia Thompson |
| DD-10008 | William Anderson |
| DD-10009 | Barbara Jackson |
| DD-10010 | Richard White |
""")
    st.divider()
    if st.button("End Call / Reset", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()

# ── Start Call ─────────────────────────────────────────────────────────────────
if not st.session_state.call_started:
    st.markdown("### Press the button below to begin the call")
    st.markdown("*This allows Dana's voice to play automatically in your browser.*")
    if st.button("Start Call", use_container_width=True, type="primary"):
        st.session_state.call_started = True
        st.session_state.display_messages.append({
            "role": "assistant", "content": GREETING
        })
        st.session_state.messages.append({
            "role": "assistant", "content": GREETING
        })
        st.session_state.pending_speech = GREETING
        st.rerun()
    st.stop()

# ── Display Chat ───────────────────────────────────────────────────────────────
for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.markdown(clean_for_display(msg["content"]))

# ── Speak Pending ──────────────────────────────────────────────────────────────
# pending_speech is set before rerun so audio plays after page reloads
if st.session_state.pending_speech:
    speak(st.session_state.pending_speech)
    st.session_state.last_spoken = st.session_state.pending_speech
    st.session_state.pending_speech = None

# ── Input ──────────────────────────────────────────────────────────────────────
st.markdown("#### Speak your response:")
spoken_text = speech_to_text(
    language='en',
    just_once=True,
    key='voice_input',
    start_prompt="Click to Speak",
    stop_prompt="Stop Recording"
)
typed_text = st.chat_input("Or type your response here...")
user_input = spoken_text or typed_text

# ── Process Input ──────────────────────────────────────────────────────────────
if user_input:
    # Show user message
    st.session_state.display_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Add user message to Claude's conversation history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Run the agentic turn — Claude decides which tools to call, we execute them
    with st.spinner("Dana is responding..."):
        reply, updated_history = run_agentic_turn(st.session_state.messages)

    # Update conversation history with the full agentic exchange
    st.session_state.messages = updated_history

    if reply:
        st.session_state.display_messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(clean_for_display(reply))
        # Set pending_speech BEFORE rerun so it plays after the page reloads
        st.session_state.pending_speech = reply

    st.rerun()
