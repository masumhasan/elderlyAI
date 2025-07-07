from dotenv import load_dotenv
from google.generativeai.client import configure as genai_configure
from google.generativeai.generative_models import GenerativeModel as genai
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    noise_cancellation,
)
from livekit.plugins import google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from tools import get_weather, recognize_song,get_agent_capabilities, search_web, send_email, read_emails, search_emails, set_reminder, calculate_medication_schedule, check_health_symptoms, help_with_technology, get_news_summary, convert_units, emergency_contacts_info, find_local_services, get_current_date_time, spark_imagination, search_google, search_google_news, visit_website, read_article, write_code_with_gemini, explain_code_with_gemini, debug_code_with_gemini, learn_programming_with_gemini


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                voice="Aoede",
                temperature=0.8,
            ),
            tools=[
                get_weather,
                search_web,
                search_google,
                search_google_news,
                send_email,
                read_emails,
                search_emails,
                set_reminder,
                calculate_medication_schedule,
                check_health_symptoms,
                help_with_technology,
                get_news_summary,
                convert_units,
                emergency_contacts_info,
                find_local_services,
                get_current_date_time,
                spark_imagination,
                visit_website,
                read_article,
                write_code_with_gemini,
                explain_code_with_gemini,
                debug_code_with_gemini,
                learn_programming_with_gemini,
                recognize_song,
                get_agent_capabilities
            ]
        )


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    
    session = AgentSession()

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))