from tools import function_tool, RunContext
from typing import Optional


@function_tool()
async def get_agent_capabilities(
    context: RunContext,  # type: ignore
    capability_category: Optional[str] = "all"
) -> str:
    """
    Explain what the AI assistant can help with based on available functions.
    
    Args:
        capability_category: Category of capabilities - 'all', 'health', 'communication', 'information', 'daily_help', 'emergency', 'programming', 'web', 'entertainment'
    """
    try:
        capabilities = {
            'health': """🏥 Health & Wellness Features:
• Check general health symptom information (not medical advice)
• Calculate medication schedules based on dosing frequency
• Set reminders for medications or appointments
• Emergency contact information and instructions
• Find local senior-friendly health services
• Get news summaries about health topics
• Search Google News for health topics
• Convert health-related units (weight, temperature, etc.)
• Read and simplify online health articles

⚠️ Important: Always consult healthcare professionals for medical advice.""",

            'communication': """📧 Communication Features:
• Send emails through Gmail
• Read emails from your Gmail inbox
• Search for specific emails
• Search the web (DuckDuckGo or Google)
• Get current news summaries (general, health, technology, local, world)
• Answer complex questions with comprehensive research
• Share information and summaries via email""",

            'information': """📚 Information & Learning:
• Get current date and time information
• Search for factual information on any topic
• Get weather information for any city
• Convert between different units of measurement
• Help with technology issues in simple terms
• Summarize or read online articles
• Visit and summarize website content
• Extract headlines or links from web pages
• Find local services (doctors, pharmacies, delivery, etc.)
• Spark imagination and creativity with activities""",

            'daily_help': """🏠 Daily Life Assistance:
• Set reminders for important tasks
• Find local services (doctors, pharmacies, delivery, etc.)
• Get help with technology problems
• Calculate medication schedules
• Unit conversions for cooking, measurements, etc.
• Spark imagination and creativity with activities
• Get current date, time, and day info
• Read and manage emails""",

            'emergency': """🚨 Emergency & Safety:
• Provide emergency contact numbers and instructions
• Medical emergency guidance
• Fire safety procedures
• Police emergency protocols
• Poison control information
• Tips for keeping emergency info handy""",

            'programming': """💻 Programming & Coding Help:
• Write code in Python and other languages using Google Gemini
• Explain code in simple terms
• Debug code and fix errors
• Create beginner-friendly programming lessons
• Help with learning programming concepts step-by-step""",

            'web': """🌐 Web & Online Tools:
• Search the web using DuckDuckGo or Google
• Search Google News for current topics
• Visit and summarize website content
• Read and simplify online articles
• Extract headlines or links from web pages
• Get summaries or full content from websites
• Search for news by topic and time range""",

            'entertainment': """🎵 Entertainment:
• Recognize songs by listening to a short audio clip
• Provide information about the recognized song and artist
• Suggest similar songs or artists""",

            'all': """🤖 I'm your AI assistant designed to help elderly users with daily tasks, information, and learning.

Here's what I can help you with:

🏥 **Health & Wellness:**
• General health symptom information (not medical advice)
• Medication schedule calculations
• Health reminders and emergency contacts
• Find local health services
• Health news and Google News search
• Unit conversions for health (weight, temperature, etc.)
• Read and simplify health articles

📧 **Communication & Information:**
• Send and read emails through Gmail
• Search for specific emails
• Search the web (DuckDuckGo or Google)
• Get current news summaries
• Answer complex questions with research
• Summarize or read online articles

📅 **Daily Life Assistance:**
• Tell you current date, time, day, month, year
• Set reminders for important tasks
• Find local services (senior-friendly options)
• Help with technology problems
• Weather information for any city
• Spark imagination and creativity

🔧 **Practical Tools:**
• Convert units (temperature, weight, measurements)
• Calculate medication schedules
• Technology help in simple terms

💻 **Programming & Coding:**
• Write, explain, and debug code (Python and more)
• Beginner-friendly
• Read and simplify articles
• Extract headlines and links from web pages

🚨 **Emergency & Safety:**
• Emergency contact information
• Safety procedures for different emergencies
• Important phone numbers to keep handy

💡 **How to use me:**
• Speak naturally - ask questions or make requests
• I can search for current information online
• All responses are designed to be clear and helpful for seniors
• I prioritize safety and always recommend consulting professionals when appropriate

What would you like help with today?"""
        }

        if capability_category and capability_category != "all":
            response = capabilities.get(capability_category, capabilities['all'])
        else:
            response = capabilities['all']

        logging.info(f"Agent capabilities explained for category: {capability_category}")
        return response

    except Exception as e:
        logging.error(f"Error explaining agent capabilities: {e}")
        return """I'm your AI assistant designed to help with daily tasks. I can:
• Answer questions and search for information
• Help with health reminders and medication schedules
• Send and read emails, and provide technology help
• Give you current date/time and weather information
• Provide emergency contact information
• Find local services and convert units
• Help with programming and web tasks

Just ask me naturally what you need help with!"""
