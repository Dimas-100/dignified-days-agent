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
        "name": "Margaret Johnson",
        "equipment": "Hospital Bed",
        "delivery_date": "April 4, 2026",
        "delivery_window": "10:00 AM to 2:00 PM",
        "address": "123 Peachtree St, Atlanta, GA",
        "phone": "404-555-1001",
        "dob": "03/12/1942",
        "insurance": "Medicare",
        "return_scheduled": False,
        "technician_notes": "Standard delivery, no special instructions."
    },
    "robert davis": {
        "name": "Robert Davis",
        "equipment": "Oxygen Concentrator",
        "delivery_date": "April 5, 2026",
        "delivery_window": "8:00 AM to 12:00 PM",
        "address": "456 Magnolia Ave, Birmingham, AL",
        "phone": "205-555-2002",
        "dob": "07/23/1938",
        "insurance": "Medicaid",
        "return_scheduled": False,
        "technician_notes": "Patient requires oxygen at 2 liters per minute."
    },
    "helen carter": {
        "name": "Helen Carter",
        "equipment": "Wheelchair",
        "delivery_date": "April 3, 2026",
        "delivery_window": "12:00 PM to 4:00 PM",
        "address": "789 Oak Street, Savannah, GA",
        "phone": "912-555-3003",
        "dob": "11/05/1945",
        "insurance": "Blue Cross",
        "return_scheduled": True,
        "technician_notes": "Return already scheduled for April 10."
    },
    "james wilson": {
        "name": "James Wilson",
        "equipment": "Hospital Bed and Bedside Commode",
        "delivery_date": "April 6, 2026",
        "delivery_window": "10:00 AM to 2:00 PM",
        "address": "321 Elm Drive, Jacksonville, FL",
        "phone": "904-555-4004",
        "dob": "02/14/1940",
        "insurance": "Medicare",
        "return_scheduled": False,
        "technician_notes": "Two items on order, deliver together."
    },
    "dorothy harris": {
        "name": "Dorothy Harris",
        "equipment": "Rollator Walker",
        "delivery_date": "April 4, 2026",
        "delivery_window": "2:00 PM to 6:00 PM",
        "address": "654 Pine Blvd, Montgomery, AL",
        "phone": "334-555-5005",
        "dob": "09/30/1950",
        "insurance": "Aetna",
        "return_scheduled": False,
        "technician_notes": "Patient prefers afternoon delivery."
    },
    "charles martinez": {
        "name": "Charles Martinez",
        "equipment": "Suction Machine",
        "delivery_date": "April 7, 2026",
        "delivery_window": "8:00 AM to 12:00 PM",
        "address": "987 Riverside Rd, Tampa, FL",
        "phone": "813-555-6006",
        "dob": "06/18/1935",
        "insurance": "Medicaid",
        "return_scheduled": False,
        "technician_notes": "Urgent delivery, patient needs unit by morning."
    },
    "patricia thompson": {
        "name": "Patricia Thompson",
        "equipment": "Hospital Bed and Oxygen Concentrator",
        "delivery_date": "April 5, 2026",
        "delivery_window": "10:00 AM to 2:00 PM",
        "address": "147 Willow Lane, Augusta, GA",
        "phone": "706-555-7007",
        "dob": "04/02/1948",
        "insurance": "Medicare",
        "return_scheduled": False,
        "technician_notes": "Two items, family prefers morning setup."
    },
    "william anderson": {
        "name": "William Anderson",
        "equipment": "Wheelchair",
        "delivery_date": "April 3, 2026",
        "delivery_window": "12:00 PM to 4:00 PM",
        "address": "258 Cypress Ave, Pensacola, FL",
        "phone": "850-555-8008",
        "dob": "12/27/1943",
        "insurance": "Blue Cross",
        "return_scheduled": True,
        "technician_notes": "Return pickup requested, coordinate with family."
    },
    "barbara jackson": {
        "name": "Barbara Jackson",
        "equipment": "Hospital Bed",
        "delivery_date": "April 8, 2026",
        "delivery_window": "8:00 AM to 12:00 PM",
        "address": "369 Maple Court, Columbus, GA",
        "phone": "706-555-9009",
        "dob": "08/15/1952",
        "insurance": "Humana",
        "return_scheduled": False,
        "technician_notes": "First floor delivery only, no elevator."
    },
    "richard white": {
        "name": "Richard White",
        "equipment": "Oxygen Concentrator and Rollator Walker",
        "delivery_date": "April 6, 2026",
        "delivery_window": "2:00 PM to 6:00 PM",
        "address": "741 Birch Street, Huntsville, AL",
        "phone": "256-555-0010",
        "dob": "01/09/1937",
        "insurance": "Medicare",
        "return_scheduled": False,
        "technician_notes": "Patient is hard of hearing, speak clearly with family."
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
            "Look up a patient record by name. Returns full account details including "
            "equipment, delivery info, insurance, and technician notes. "
            "Call this tool as soon as you have the patient's name."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_name": {
                    "type": "string",
                    "description": "The full or partial name of the patient."
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
        name = tool_input.get("patient_name", "").lower()
        # Fuzzy match — check if any word in the query matches a patient key
        found = None
        for key, patient in PATIENTS.items():
            name_parts = key.split()
            for part in name_parts:
                if part in name and len(part) > 2:
                    found = patient
                    break
            if found:
                break
        if found:
            return json.dumps({
                "status": "found",
                "patient": found
            })
        else:
            return json.dumps({
                "status": "not_found",
                "message": f"No patient record found for '{tool_input.get('patient_name')}'."
            })

    elif tool_name == "route_to_delivery_agent":
        st.session_state.active_agent = "delivery"
        st.session_state.agent_log.append("→ Routed to Delivery Status Agent")
        return json.dumps({"status": "routed", "agent": "delivery"})

    elif tool_name == "route_to_scheduling_agent":
        st.session_state.active_agent = "scheduling"
        st.session_state.agent_log.append("→ Routed to Return Scheduling Agent")
        return json.dumps({"status": "routed", "agent": "scheduling"})

    elif tool_name == "route_to_triage_agent":
        st.session_state.active_agent = "triage"
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

Your workflow:
1. Greet the caller as Dana and understand what they need.
2. Ask for the patient's name, then call lookup_patient_record immediately.
3. Once you have the patient record, call the correct routing tool based on intent.
4. The specialist agent will handle the rest of the conversation.

Rules:
- Always call lookup_patient_record before routing to any specialist agent.
- If a patient is not found after 2 attempts, call escalate_to_human_csr.
- Speak naturally and warmly, like a caring person on a phone call.
- Never use bullet points, headers, lists, or emojis — only natural flowing speech.
- Never say "certainly" or "absolutely" — those sound robotic.
- These families are going through a very difficult time. Show genuine empathy."""


DELIVERY_AGENT_SYSTEM = """Your name is Dana. You are a warm and caring AI customer service agent for Dignified Days.
You are currently handling a delivery status inquiry. The patient's verified account is in the conversation history.

Your job:
- Confirm the delivery date and window clearly and warmly.
- Answer any questions about the delivery.
- Use schedule_return_pickup if the caller also wants to arrange a return.
- Use escalate_to_human_csr if the issue cannot be resolved.

Speak naturally, warmly, and with genuine care. No bullet points, headers, or emojis.
Never say "certainly" or "absolutely." These families are going through a very hard time."""


SCHEDULING_AGENT_SYSTEM = """Your name is Dana. You are a warm and caring AI customer service agent for Dignified Days.
You are currently handling a return scheduling request. The patient's verified account is in the conversation history.

Your job:
- Help the caller schedule a return pickup for their equipment.
- Offer three time slots naturally in conversation: morning (8am-noon), afternoon (noon-4pm), evening (4-7pm).
- Once they choose a slot, call schedule_return_pickup to confirm and generate a confirmation number.
- Use escalate_to_human_csr if the issue cannot be resolved.

Speak naturally, warmly, and with genuine care. No bullet points, headers, or emojis.
Never say "certainly" or "absolutely.""""


TRIAGE_AGENT_SYSTEM = """Your name is Dana. You are a warm and caring AI customer service agent for Dignified Days.
You are currently handling an equipment issue. The patient's verified account is in the conversation history.

Your job:
- Stay calm and reassuring. Most issues are user error.
- Walk through simple troubleshooting steps one at a time.
- Guide the caller gently — check power, connections, settings.
- If the issue truly cannot be resolved by troubleshooting, call escalate_to_human_csr with a
  clear summary so a technician can be dispatched.

Speak naturally, warmly, with genuine empathy. No bullet points, headers, or emojis.
These families are under enormous stress — be their calm in the storm."""


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
            max_tokens=500,
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
                    st.session_state.agent_log.append(
                        f"🔧 {st.session_state.active_agent.title()} Agent called: {block.name}({json.dumps(block.input)})"
                    )
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
    text = re.sub(r'[-]\s', '', text)
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
    "agent_log":          [],
    "call_started":       False,
    "last_spoken":        None,
    "pending_speech":     None,
    "escalation_summary": ""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

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
    st.markdown("### Demo Patients")
    st.markdown("""
- Margaret Johnson
- Robert Davis
- Helen Carter
- James Wilson
- Dorothy Harris
- Charles Martinez
- Patricia Thompson
- William Anderson
- Barbara Jackson
- Richard White
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
