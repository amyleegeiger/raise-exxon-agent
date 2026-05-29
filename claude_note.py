import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


SYSTEM_PROMPT = """You are a recruiting coordinator assistant for Raise, a staffing firm managing the ExxonMobil direct sourcing program.

Your job is to generate a concise, professional candidate handoff note for WorkLlama based on structured screening data. 

The note must:
- Be 3-5 sentences maximum
- Lead with candidate name, role, and key experience
- Include availability, location, and pay rate
- Flag any ExxonMobil history (previous contractor or FTE)
- Note work authorization and background check consent
- End with a brief fit rationale
- Use plain prose — no bullet points, no headers
- Match the tone of an experienced recruiter writing for a curation lead

Do not include date of birth in the note. Do not add any preamble — output only the note text itself."""


def generate_handoff_note(data: dict) -> str:
    candidate_summary = f"""
Candidate: {data.get('first_name')} {data.get('last_name')}
Role: {data.get('req_title')} (Req #{data.get('req_id')})
Location: {data.get('city')}, {data.get('state')}
Pay rate: ${data.get('pay_rate')}/hr
Available: {data.get('available_start')}
Work authorization: {data.get('work_auth')}
Background check consent: {data.get('bg_consent')}
Previous ExxonMobil history: {data.get('prev_xom', 'No')}
Last day at XOM (if applicable): {data.get('xom_last_day', 'N/A')}
Rehire eligible: {data.get('rehire_eligible', 'N/A')}
Commute confirmed: {data.get('commute_confirmed')}
Candidate source: {data.get('source')}
Recruiter notes: {data.get('recruiter_notes', '')}
Key skills / experience summary: {data.get('skills_summary', '')}
""".strip()

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Generate a WorkLlama handoff note for this candidate:\n\n{candidate_summary}"
            }
        ]
    )

    return message.content[0].text.strip()
