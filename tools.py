import logging
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import os
import smtplib
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from typing import Optional
import asyncio
from dotenv import load_dotenv
from google.generativeai.client import configure as genai_configure
from google.generativeai.generative_models import GenerativeModel as genai
# Load environment variables from .env file
load_dotenv()

@function_tool()
async def get_weather(
    context: RunContext,  # type: ignore
    city: str) -> str:
    """
    Get the current weather for a given city.
    """
    try:
        response = requests.get(
            f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            logging.info(f"Weather for {city}: {response.text.strip()}")
            return response.text.strip()   
        else:
            logging.error(f"Failed to get weather for {city}: {response.status_code}")
            return f"Could not retrieve weather for {city}."
    except Exception as e:
        logging.error(f"Error retrieving weather for {city}: {e}")
        return f"An error occurred while retrieving weather for {city}." 

@function_tool()
async def search_web(
    context: RunContext,  # type: ignore
    query: str) -> str:
    """
    Search the web using DuckDuckGo.
    """
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        logging.info(f"Search results for '{query}': {results}")
        return results
    except Exception as e:
        logging.error(f"Error searching the web for '{query}': {e}")
        return f"An error occurred while searching the web for '{query}'."    

@function_tool()
async def answer_complex_question(
    context: RunContext,  # type: ignore
    question: str,
    search_depth: Optional[str] = "basic"
) -> str:
    """
    Answer complex questions by searching multiple sources and providing comprehensive responses.
    
    Args:
        question: The complex question to answer
        search_depth: Either 'basic' for single search or 'comprehensive' for multiple searches
    """
    try:
        logging.info(f"Processing complex question: {question}")
        
        if search_depth == "comprehensive":
            # Break down complex question into multiple search queries
            search_queries = [
                question,
                f"{question} explanation",
                f"{question} examples",
                f"{question} latest information"
            ]
            
            all_results = []
            for query in search_queries:
                try:
                    result = DuckDuckGoSearchRun().run(tool_input=query)
                    all_results.append(f"Search for '{query}':\n{result}\n")
                except Exception as e:
                    logging.warning(f"Failed to search for '{query}': {e}")
                    continue
            
            combined_results = "\n".join(all_results)
            
            # Format comprehensive response
            response = f"""Based on multiple searches, here's a comprehensive answer to your question: "{question}"

{combined_results}

Summary: This information has been gathered from multiple sources to provide you with the most complete answer possible."""
            
        else:
            # Basic single search
            result = DuckDuckGoSearchRun().run(tool_input=question)
            response = f"""Here's what I found about your question: "{question}"

{result}

If you need more detailed information, please let me know and I can search more comprehensively."""
        
        logging.info(f"Complex question answered for: {question}")
        return response
        
    except Exception as e:
        logging.error(f"Error answering complex question '{question}': {e}")
        return f"I apologize, but I encountered an error while researching your question: '{question}'. Please try rephrasing your question or ask me to search for something more specific."

@function_tool()
async def get_factual_information(
    context: RunContext,  # type: ignore
    topic: str,
    information_type: Optional[str] = "general"
) -> str:
    """
    Get factual information about a specific topic with different detail levels.
    
    Args:
        topic: The topic to get information about
        information_type: Type of information - 'general', 'detailed', 'recent', or 'historical'
    """
    try:
        logging.info(f"Getting {information_type} information about: {topic}")
        
        # Customize search query based on information type
        if information_type == "recent":
            query = f"{topic} latest news recent developments 2024 2025"
        elif information_type == "historical":
            query = f"{topic} history background timeline"
        elif information_type == "detailed":
            query = f"{topic} detailed explanation comprehensive guide"
        else:  # general
            query = f"{topic} facts information overview"
        
        result = DuckDuckGoSearchRun().run(tool_input=query)
        
        response = f"""Here's {information_type} information about "{topic}":

{result}

Would you like me to search for more specific aspects of this topic or provide information with a different focus?"""
        
        logging.info(f"Retrieved {information_type} information for: {topic}")
        return response
        
    except Exception as e:
        logging.error(f"Error getting information about '{topic}': {e}")
        return f"I encountered an error while looking up information about '{topic}'. Please try again or rephrase your request."

@function_tool()    
async def send_email(
    context: RunContext,  # type: ignore
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    """
    Send an email through Gmail.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        message: Email body content
        cc_email: Optional CC email address
    """
    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Get credentials from environment variables
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")  # Use App Password, not regular password
        
        if not gmail_user or not gmail_password:
            logging.error("Gmail credentials not found in environment variables")
            return "Email sending failed: Gmail credentials not configured."
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add CC if provided
        recipients = [to_email]
        if cc_email:
            msg['Cc'] = cc_email
            recipients.append(cc_email)
        
        # Attach message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(gmail_user, gmail_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(gmail_user, recipients, text)
        server.quit()
        
        logging.info(f"Email sent successfully to {to_email}")
        return f"Email sent successfully to {to_email}"
        
    except smtplib.SMTPAuthenticationError:
        logging.error("Gmail authentication failed")
        return "Email sending failed: Authentication error. Please check your Gmail credentials."
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
        return f"Email sending failed: SMTP error - {str(e)}"
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return f"An error occurred while sending email: {str(e)}"





@function_tool()
async def set_reminder(
    context: RunContext,  # type: ignore
    reminder_text: str,
    time_delay_minutes: int = 30
) -> str:
    """
    Set a simple reminder for the user.
    
    Args:
        reminder_text: What to remind the user about
        time_delay_minutes: How many minutes from now to remind (default 30)
    """
    try:
        import asyncio
        from datetime import datetime, timedelta
        
        remind_time = datetime.now() + timedelta(minutes=time_delay_minutes)
        
        # Store reminder (in a real app, you'd use a database)
        logging.info(f"Reminder set: '{reminder_text}' for {remind_time.strftime('%I:%M %p')}")
        
        # Simple async reminder (for demo purposes)
        asyncio.create_task(send_reminder_after_delay(reminder_text, time_delay_minutes))
        
        return f"Reminder set: I'll remind you about '{reminder_text}' in {time_delay_minutes} minutes at {remind_time.strftime('%I:%M %p')}."
        
    except Exception as e:
        logging.error(f"Error setting reminder: {e}")
        return f"Sorry, I couldn't set the reminder: {str(e)}"

async def send_reminder_after_delay(reminder_text: str, delay_minutes: int):
    """Helper function to send reminder after delay"""
    await asyncio.sleep(delay_minutes * 60)
    logging.info(f"REMINDER: {reminder_text}")

@function_tool()
async def calculate_medication_schedule(
    context: RunContext,  # type: ignore
    medication_name: str,
    dosage_times_per_day: int,
    first_dose_time: str = "8:00 AM"
) -> str:
    """
    Calculate a medication schedule based on doses per day.
    
    Args:
        medication_name: Name of the medication
        dosage_times_per_day: How many times per day to take it
        first_dose_time: Time for first dose (e.g., "8:00 AM")
    """
    try:
        from datetime import datetime, timedelta
        
        # Parse first dose time
        first_time = datetime.strptime(first_dose_time, "%I:%M %p")
        
        # Calculate intervals
        hours_between = 24 / dosage_times_per_day
        
        schedule = []
        current_time = first_time
        
        for i in range(dosage_times_per_day):
            schedule.append(current_time.strftime("%I:%M %p"))
            current_time += timedelta(hours=hours_between)
        
        schedule_text = "\n".join([f"Dose {i+1}: {time}" for i, time in enumerate(schedule)])
        
        response = f"""Medication Schedule for {medication_name}:

{schedule_text}

Take {dosage_times_per_day} doses per day, approximately {hours_between:.1f} hours apart.

⚠️ Important: Always follow your doctor's specific instructions. This is just a general schedule calculator."""
        
        logging.info(f"Medication schedule created for {medication_name}")
        return response
        
    except Exception as e:
        logging.error(f"Error calculating medication schedule: {e}")
        return f"Sorry, I couldn't calculate the medication schedule: {str(e)}"

@function_tool()
async def check_health_symptoms(
    context: RunContext,  # type: ignore
    symptoms: str,
    urgency_level: Optional[str] = "normal"
) -> str:
    """
    Provide general health information about symptoms (not medical advice).
    
    Args:
        symptoms: Description of symptoms
        urgency_level: 'normal', 'concerning', or 'emergency'
    """
    try:
        # Search for general health information
        query = f"{symptoms} health information general causes when to see doctor"
        search_result = DuckDuckGoSearchRun().run(tool_input=query)
        
        # Emergency warning
        emergency_keywords = ["chest pain", "difficulty breathing", "severe pain", "bleeding", "unconscious", "stroke", "heart attack"]
        is_emergency = any(keyword in symptoms.lower() for keyword in emergency_keywords)
        
        if is_emergency or urgency_level == "emergency":
            warning = """🚨 EMERGENCY WARNING: If you're experiencing severe symptoms, call 911 or go to the nearest emergency room immediately!

"""
        elif urgency_level == "concerning":
            warning = """⚠️ These symptoms may require medical attention. Please consider contacting your doctor.

"""
        else:
            warning = ""
        
        response = f"""{warning}Here's general information about "{symptoms}":

{search_result}

💡 Important Reminders:
- This is general information only, not medical advice
- Always consult with your healthcare provider for proper diagnosis
- If symptoms worsen or you're concerned, contact your doctor
- Keep a list of your symptoms to discuss with your healthcare provider"""
        
        logging.info(f"Health symptom information provided for: {symptoms}")
        return response
        
    except Exception as e:
        logging.error(f"Error checking health symptoms: {e}")
        return "I'm sorry, I couldn't retrieve health information right now. If you're experiencing concerning symptoms, please contact your healthcare provider."

@function_tool()
async def get_news_summary(
    context: RunContext,  # type: ignore
    news_category: Optional[str] = "general",
    location: Optional[str] = "United States"
) -> str:
    """
    Get a summary of current news.
    
    Args:
        news_category: Type of news - 'general', 'health', 'technology', 'local', 'world'
        location: Location for local news
    """
    try:
        if news_category == "local":
            query = f"{location} local news today headlines"
        elif news_category == "health":
            query = "health news medical breakthroughs elderly seniors today"
        elif news_category == "technology":
            query = "technology news simple easy seniors elderly friendly"
        elif news_category == "world":
            query = "world news international headlines today"
        else:
            query = "top news headlines today current events"
        
        result = DuckDuckGoSearchRun().run(tool_input=query)
        
        category_display = news_category.title() if news_category else "General"
        response = f"""📰 {category_display} News Summary:

{result}

Would you like me to search for news about a specific topic or a different category?"""
        
        logging.info(f"News summary provided for category: {news_category}")
        return response
        
    except Exception as e:
        logging.error(f"Error getting news summary: {e}")
        return "I'm sorry, I couldn't retrieve the news right now. Please try again later."

@function_tool()
async def help_with_technology(
    context: RunContext,  # type: ignore
    technology_issue: str,
    device_type: Optional[str] = "general"
) -> str:
    """
    Provide help with technology issues in simple terms.
    
    Args:
        technology_issue: Description of the technology problem
        device_type: Type of device - 'smartphone', 'computer', 'tablet', 'smart TV', 'general'
    """
    try:
        query = f"{technology_issue} {device_type} simple easy steps seniors elderly help tutorial"
        result = DuckDuckGoSearchRun().run(tool_input=query)
        
        device_type_display = device_type.title() if device_type else "General"
        response = f"""🔧 Technology Help for {device_type_display}:

Problem: {technology_issue}

{result}

💡 Tech Tips:
- Take your time with each step
- Don't be afraid to ask for help from family or friends
- Write down steps that work for future reference
- If you're still having trouble, consider visiting a local computer store for hands-on help

Would you like me to explain any of these steps in more detail?"""
        
        logging.info(f"Technology help provided for: {technology_issue}")
        return response
        
    except Exception as e:
        logging.error(f"Error providing technology help: {e}")
        return "I'm sorry, I couldn't find technology help right now. You might want to ask a family member or visit a local computer store for assistance."

@function_tool()
async def find_local_services(
    context: RunContext,  # type: ignore
    service_type: str,
    location: str,
    senior_friendly: bool = True
) -> str:
    """
    Find local services for elderly users.
    
    Args:
        service_type: Type of service (doctor, pharmacy, grocery delivery, transportation, etc.)
        location: City or area to search in
        senior_friendly: Whether to prioritize senior-friendly services
    """
    try:
        senior_terms = "seniors elderly friendly" if senior_friendly else ""
        query = f"{service_type} {location} {senior_terms} services near me"
        
        result = DuckDuckGoSearchRun().run(tool_input=query)
        
        response = f"""📍 Local {service_type.title()} Services in {location}:

{result}

💡 Tips for choosing services:
- Call ahead to ask about senior discounts
- Ask about accessibility features
- Check if they offer home visits or delivery
- Read reviews from other customers
- Ask friends and family for recommendations

Would you like me to search for a different type of service or in a different area?"""
        
        logging.info(f"Local services found for {service_type} in {location}")
        return response
        
    except Exception as e:
        logging.error(f"Error finding local services: {e}")
        return f"I'm sorry, I couldn't find local services right now. You might want to call 211 for local service information or ask your local library for assistance."

@function_tool()
async def convert_units(
    context: RunContext,  # type: ignore
    value: float,
    from_unit: str,
    to_unit: str
) -> str:
    """
    Convert between different units of measurement.
    
    Args:
        value: The number to convert
        from_unit: Starting unit (e.g., 'fahrenheit', 'pounds', 'feet')
        to_unit: Target unit (e.g., 'celsius', 'kilograms', 'meters')
    """
    try:
        conversions = {
            # Temperature
            ('fahrenheit', 'celsius'): lambda f: (f - 32) * 5/9,
            ('celsius', 'fahrenheit'): lambda c: c * 9/5 + 32,
            
            # Weight
            ('pounds', 'kilograms'): lambda lbs: lbs * 0.453592,
            ('kilograms', 'pounds'): lambda kg: kg * 2.20462,
            
            # Length
            ('feet', 'meters'): lambda ft: ft * 0.3048,
            ('meters', 'feet'): lambda m: m * 3.28084,
            ('inches', 'centimeters'): lambda inch: inch * 2.54,
            ('centimeters', 'inches'): lambda cm: cm * 0.393701,
            
            # Volume
            ('cups', 'milliliters'): lambda cups: cups * 236.588,
            ('milliliters', 'cups'): lambda ml: ml * 0.00422675,
            ('tablespoons', 'milliliters'): lambda tbsp: tbsp * 14.7868,
            ('teaspoons', 'milliliters'): lambda tsp: tsp * 4.92892,
        }
        
        key = (from_unit.lower(), to_unit.lower())
        if key in conversions:
            result = conversions[key](value)
            response = f"""Unit Conversion:
{value} {from_unit} = {result:.2f} {to_unit}"""
        else:
            # Fallback to web search
            query = f"convert {value} {from_unit} to {to_unit}"
            search_result = DuckDuckGoSearchRun().run(tool_input=query)
            response = f"Conversion result:\n{search_result}"
        
        logging.info(f"Converted {value} {from_unit} to {to_unit}")
        return response
        
    except Exception as e:
        logging.error(f"Error converting units: {e}")
        return f"Sorry, I couldn't convert {value} {from_unit} to {to_unit}. Please check that both units are valid."

@function_tool()
async def emergency_contacts_info(
    context: RunContext,  # type: ignore
    emergency_type: Optional[str] = "general"
) -> str:
    """
    Provide emergency contact information and instructions.
    
    Args:
        emergency_type: Type of emergency - 'medical', 'fire', 'police', 'poison', 'general'
    """
    try:
        emergency_info = {
            'medical': """🚨 MEDICAL EMERGENCY:
• Call 911 immediately for life-threatening emergencies
• Stay calm and speak clearly
• Have your address ready
• List your symptoms clearly
• Mention any medications you're taking
• If conscious, stay on the line with the operator""",
            
            'fire': """🔥 FIRE EMERGENCY:
• Call 911 immediately
• Get out of the building safely - don't stop for belongings
• Feel doors before opening them (if hot, use alternate route)
• Stay low if there's smoke
• Once outside, stay outside
• Meet at your predetermined family meeting spot""",
            
            'police': """👮 POLICE EMERGENCY:
• Call 911 for immediate danger
• For non-emergencies, call your local police department
• Stay calm and provide clear information
• Give your exact location
• Describe what's happening""",
            
            'poison': """☠️ POISON EMERGENCY:
• Call Poison Control: 1-800-222-1222 (24/7)
• Call 911 if person is unconscious, not breathing, or having convulsions
• Have the poison container ready for information
• Don't make the person vomit unless told to do so""",
            
            'general': """📞 EMERGENCY CONTACTS:
• Emergency Services: 911
• Poison Control: 1-800-222-1222
• National Suicide Prevention Lifeline: 988
• Crisis Text Line: Text HOME to 741741

🏥 Keep these numbers handy:
• Your doctor's office
• Nearest hospital
• Your pharmacy
• A trusted family member or friend
• Your insurance company"""
        }
        
        info = emergency_info.get(emergency_type if emergency_type is not None else 'general', emergency_info['general'])
        
        response = f"""{info}

⚠️ IMPORTANT REMINDERS:
• Save important numbers in your phone
• Keep a written list by your phone
• Make sure family members know your emergency contacts
• Consider wearing a medical alert bracelet if you have health conditions
• Keep your address written down near your phone for emergencies

Stay safe! 💙"""
        
        logging.info(f"Emergency contact info provided for: {emergency_type}")
        return response
        
    except Exception as e:
        logging.error(f"Error providing emergency info: {e}")
        return "In case of emergency, call 999. Keep important phone numbers written down near your phone."
    



@function_tool()
async def get_current_date_time(
    context: RunContext,  # type: ignore
    query_type: Optional[str] = "full"
) -> str:
    """
    Get current date and time information.
    
    Args:
        query_type: Type of information - 'date', 'time', 'day', 'month', 'year', 'full'
    """
    try:
        from datetime import datetime
        
        now = datetime.now()
        
        # Format different types of responses
        if query_type == "date":
            response = f"Today's date is {now.strftime('%B %d, %Y')} ({now.strftime('%m/%d/%Y')})"
        elif query_type == "time":
            response = f"The current time is {now.strftime('%I:%M %p')}"
        elif query_type == "day":
            response = f"Today is {now.strftime('%A')}"
        elif query_type == "month":
            response = f"This month is {now.strftime('%B %Y')}"
        elif query_type == "year":
            response = f"The current year is {now.strftime('%Y')}"
        else:  # full
            response = f"""📅 Current Date & Time:

• Today is: {now.strftime('%A, %B %d, %Y')}
• Time: {now.strftime('%I:%M %p')}
• Day of week: {now.strftime('%A')}
• Month: {now.strftime('%B')}
• Year: {now.strftime('%Y')}

Date formats:
• {now.strftime('%m/%d/%Y')} (MM/DD/YYYY)
• {now.strftime('%B %d, %Y')} (Month Day, Year)"""
        
        logging.info(f"Date/time information provided: {query_type}")
        return response
        
    except Exception as e:
        logging.error(f"Error getting date/time information: {e}")
        return "দুঃখিত, আমি বর্তমান তারিখ এবং সময়ের তথ্য আনতে পারিনি।"

@function_tool()
async def get_agent_capabilities(
    context: RunContext,  # type: ignore
    capability_category: Optional[str] = "all"
) -> str:
    """
    Explain what the AI assistant can help with based on available functions.
    
    Args:
        capability_category: Category of capabilities - 'all', 'health', 'communication', 'information', 'daily_help', 'emergency', 'programming', 'web'
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
• Beginner-friendly programming lessons

🌐 **Web & Online Tools:**
• Search Google and DuckDuckGo
• Search Google News
• Visit and summarize websites
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

@function_tool()
async def spark_imagination(
    context: RunContext,  # type: ignore
    activity_type: Optional[str] = "story",
    topic: Optional[str] = "nature"
) -> str:
    """
    Help spark imagination and creativity through various activities.
    
    Args:
        activity_type: Type of creative activity - 'story', 'memory', 'describe', 'imagine', 'creative_writing', 'what_if'
        topic: Topic or theme for the imaginative exercise
    """
    try:
        from datetime import datetime
        import random
        
        if activity_type == "story":
            prompts = [
                f"Let me tell you a story about {topic}. Once upon a time, in a place where {topic} was the most important thing...",
                f"Imagine a world where {topic} could talk. What would it say about its daily adventures?",
                f"There was once a magical {topic} that had the power to grant one wish to whoever found it...",
                f"In a small town, everyone knew about the mysterious {topic} that appeared every full moon..."
            ]
            
            response = f"""📖 **Imagination Story Starter:**

{random.choice(prompts)}

💭 **Your turn:** 
• What happens next in this story?
• Who are the main characters?
• What challenges do they face?
• How does the story end?

Take your time and let your imagination wander! There are no wrong answers in storytelling."""

        elif activity_type == "memory":
            response = f"""🧠 **Memory & Imagination Exercise:**

Think about a time when {topic} played an important role in your life...

💭 **Reflect on:**
• What did you see, hear, smell, or feel?
• Who was with you during this experience?
• What emotions do you remember?
• If you could go back, what would you do differently?
• What would you tell your younger self about this moment?

✨ **Now imagine:** What if that experience had magical elements? What if {topic} could transport you anywhere in time?"""

        elif activity_type == "describe":
            response = f"""🎨 **Creative Description Exercise:**

Close your eyes and imagine the most beautiful {topic} you've ever seen or could imagine...

🌟 **Describe it using all your senses:**
• What colors do you see? Are they bright, soft, or changing?
• What sounds does it make or what sounds surround it?
• How does it feel to touch? Smooth, rough, warm, cool?
• What scents are in the air around it?
• If it had a taste, what would it be like?

💫 **Creative twist:** Now imagine this {topic} has a personality. What kind of character would it be?"""

        elif activity_type == "imagine":
            scenarios = [
                f"You wake up and discover you can communicate with all {topic}. What's the first conversation like?",
                f"You find a door in your garden that leads to a world made entirely of {topic}. What do you discover?",
                f"A friendly genie grants you the power to transform any {topic} with just a thought. How do you use this gift?",
                f"You inherit a magical shop where every {topic} has a special story. What's the most interesting item?"
            ]
            
            response = f"""✨ **Imagination Adventure:**

{random.choice(scenarios)}

🚀 **Let your mind explore:**
• What does this new world look like?
• What sounds, smells, and feelings are there?
• Who do you meet on this adventure?
• What surprises do you discover?
• How does this experience change you?

Remember, in imagination, anything is possible!"""

        elif activity_type == "creative_writing":
            response = f"""✍️ **Creative Writing Prompt:**

**Topic:** {topic}

**Your mission:** Write a short piece (just a few sentences or paragraphs) about:

🌟 **Option 1:** A day in the life of {topic}
🌟 **Option 2:** A love letter to {topic}
🌟 **Option 3:** {topic} as seen through a child's eyes
🌟 **Option 4:** The secret life of {topic}

💡 **Writing tips:**
• Don't worry about perfect grammar
• Focus on feelings and imagery
• Use your personal experiences
• Have fun with it!
• Read it aloud when you're done"""

        elif activity_type == "what_if":
            what_if_scenarios = [
                f"What if {topic} could solve any problem in the world?",
                f"What if you could give {topic} any superpower?",
                f"What if {topic} existed in ancient times?",
                f"What if {topic} came from another planet?",
                f"What if you could make {topic} any size you wanted?"
            ]
            
            response = f"""🤔 **"What If" Imagination Game:**

{random.choice(what_if_scenarios)}

🎭 **Explore the possibilities:**
• How would the world be different?
• What new adventures would be possible?
• What problems might this create?
• What would be the most exciting part?
• How would people react?

💭 **Bonus challenge:** Come up with your own "What if" question about {topic}!"""

        else:  # default
            response = f"""🎨 **Imagination Boost:**

Let's explore the wonderful world of {topic} through creativity!

🌈 **Choose your adventure:**
• **Story Time:** Create a tale about {topic}
• **Memory Lane:** Recall experiences with {topic}
• **Sensory Journey:** Describe {topic} using all five senses
• **What If Game:** Imagine impossible scenarios with {topic}
• **Creative Writing:** Write something inspired by {topic}

✨ **Benefits of imagination:**
• Keeps your mind active and flexible
• Reduces stress and brings joy
• Connects you with memories and emotions
• Exercises creativity and problem-solving
• Can be shared with family and friends

What type of imaginative activity sounds most appealing to you today?"""

        logging.info(f"Imagination activity provided: {activity_type} about {topic}")
        return response

    except Exception as e:
        logging.error(f"Error providing imagination activity: {e}")
        return """✨ Let's use our imagination! Try this: Close your eyes and think of your favorite place. What do you see, hear, and feel there? What makes it special? Imagination keeps our minds young and creative!"""

@function_tool()
async def search_google(
    context: RunContext,  # type: ignore
    query: str,
    num_results: Optional[int] = 5
) -> str:
    """
    Search Google for more comprehensive results than DuckDuckGo.
    
    Args:
        query: Search query
        num_results: Number of results to return (default 5)
    """
    try:
        from googlesearch import search
        import time
        
        logging.info(f"Searching Google for: {query}")
        
        # Ensure num_results is not None
        if num_results is None:
            num_results = 5

        # Get search results
        results = []
        for i, url in enumerate(search(query, num_results=num_results)):
            results.append(f"{i+1}. {url}")
            if i >= num_results - 1:
                break
        
        if results:
            response = f"""🔍 Google Search Results for "{query}":

{chr(10).join(results)}

💡 These are direct links to websites. You can ask me to search for more specific information or get details about any of these topics."""
        else:
            response = f"I couldn't find Google search results for '{query}'. Let me try a different search method."
            # Fallback to DuckDuckGo
            fallback_result = DuckDuckGoSearchRun().run(tool_input=query)
            response += f"\n\nHere's what I found using an alternative search:\n{fallback_result}"
        
        logging.info(f"Google search completed for: {query}")
        return response
        
    except ImportError:
        logging.warning("Google search library not available, falling back to DuckDuckGo")
        # Fallback to DuckDuckGo search
        result = DuckDuckGoSearchRun().run(tool_input=query)
        return f"Google search not available, but here's what I found:\n\n{result}"
    except Exception as e:
        logging.error(f"Error performing Google search for '{query}': {e}")
        # Fallback to DuckDuckGo search
        try:
            result = DuckDuckGoSearchRun().run(tool_input=query)
            return f"Had trouble with Google search, but here's what I found using alternative search:\n\n{result}"
        except:
            return f"I'm sorry, I couldn't search for '{query}' right now. Please try again later."

@function_tool()
async def search_google_news(
    context: RunContext,  # type: ignore
    topic: str,
    time_range: Optional[str] = "recent"
) -> str:
    """
    Search Google News for current news about a specific topic.
    
    Args:
        topic: News topic to search for
        time_range: Time range - 'recent', 'today', 'week', 'month'
    """
    try:
        # Construct Google News search query
        if time_range == "today":
            query = f"{topic} news today"
        elif time_range == "week":
            query = f"{topic} news this week"
        elif time_range == "month":
            query = f"{topic} news this month"
        else:  # recent
            query = f"{topic} latest news"
        
        # Use DuckDuckGo to search for news since it's more reliable
        result = DuckDuckGoSearchRun().run(tool_input=f"site:news.google.com {query}")
        
        if not result or len(result.strip()) < 10:
            # Fallback to general news search
            result = DuckDuckGoSearchRun().run(tool_input=f"{query} site:cnn.com OR site:bbc.com OR site:reuters.com")
        
        response = f"""📰 News Search Results for "{topic}" ({time_range}):

{result}

💡 For more current news, you can also ask me to search for specific news categories or check different time periods."""
        
        logging.info(f"Google News search completed for: {topic}")
        return response
        
    except Exception as e:
        logging.error(f"Error searching Google News for '{topic}': {e}")
        return f"I couldn't retrieve news about '{topic}' right now. Please try asking for general news or a different topic."




@function_tool()
async def visit_website(
    context: RunContext,  # type: ignore
    url: str,
    content_type: Optional[str] = "summary"
) -> str:
    """
    Visit a website and extract its content.
    
    Args:
        url: The website URL to visit
        content_type: Type of content to extract - 'summary', 'full', 'headlines', 'links'
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import re
        from urllib.parse import urljoin, urlparse
        
        logging.info(f"Visiting website: {url}")
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make request with timeout
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get page title
        title = soup.find('title')
        page_title = title.get_text().strip() if title else "No title found"
        
        if content_type == "headlines":
            # Extract headlines (h1, h2, h3 tags)
            headlines = []
            for tag in soup.find_all(['h1', 'h2', 'h3']):
                text = tag.get_text().strip()
                if text and len(text) > 3:  # Filter out very short text
                    headlines.append(f"• {text}")
            
            headlines_text = '\n'.join(headlines[:15])  # Limit to 15 headlines
            
            response = f"""📄 Headlines from "{page_title}":
URL: {url}

{headlines_text if headlines_text else "No clear headlines found on this page."}

Would you like me to get the full content or summary of this page?"""

        elif content_type == "links":
            # Extract links
            links = []
            from bs4 import Tag
            for link in soup.find_all('a', href=True):
                if isinstance(link, Tag):
                    href = link.get('href')
                    text = link.get_text().strip()
                    
                    # Convert relative URLs to absolute
                    full_url = urljoin(url, str(href))
                    
                    if text and len(text) > 3 and len(text) < 100:  # Filter reasonable link text
                        links.append(f"• {text}: {full_url}")
            
            links_text = '\n'.join(links[:20])  # Limit to 20 links
            
            response = f"""🔗 Links from "{page_title}":
URL: {url}

{links_text if links_text else "No clear links found on this page."}

I can visit any of these links for you if you'd like more information."""

        elif content_type == "full":
            # Get full text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit text length for readability
            if len(clean_text) > 2000:
                clean_text = clean_text[:2000] + "..."
            
            response = f"""📄 Full Content from "{page_title}":
URL: {url}

{clean_text}

This is the complete text content from the webpage. Would you like me to summarize this information or search for something specific?"""

        else:  # summary (default)
            # Get main content paragraphs
            paragraphs = []
            for p in soup.find_all('p'):
                text = p.get_text().strip()
                if len(text) > 50:  # Only include substantial paragraphs
                    paragraphs.append(text)
            
            # Take first few paragraphs for summary
            summary_text = '\n\n'.join(paragraphs[:5])
            
            if len(summary_text) > 1500:
                summary_text = summary_text[:1500] + "..."
            
            response = f"""📄 Summary from "{page_title}":
URL: {url}

{summary_text if summary_text else "Could not extract readable content from this page."}

💡 I can also get the full content, headlines, or links from this page. Just let me know what you need!"""

        logging.info(f"Successfully visited website: {url}")
        return response

    except requests.exceptions.Timeout:
        logging.error(f"Website visit timed out: {url}")
        return f"The website {url} took too long to respond. Please try again later or check if the URL is correct."
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error visiting website {url}: {e}")
        return f"I couldn't access the website {url}. Please check that the URL is correct and the website is available."
    
    except Exception as e:
        logging.error(f"Unexpected error visiting website {url}: {e}")
        return f"I encountered an error while trying to visit {url}. Please try again or provide a different website."

@function_tool()
async def read_article(
    context: RunContext,  # type: ignore
    url: str,
    reading_level: Optional[str] = "simple"
) -> str:
    """
    Read and simplify online articles for elderly users.
    
    Args:
        url: URL of the article to read
        reading_level: How to present the content - 'simple', 'detailed', 'bullet_points'
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        logging.info(f"Reading article: {url}")
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title
        title = soup.find('title')
        article_title = title.get_text().strip() if title else "Article"
        
        # Try to find article content (common article selectors)
        article_selectors = ['article', '.article-body', '.content', '.post-content', '.entry-content', 'main']
        article_content = None
        
        for selector in article_selectors:
            article_content = soup.select_one(selector)
            if article_content:
                break
        
        if not article_content:
            # Fallback to all paragraphs
            article_content = soup
        
        # Extract paragraphs
        paragraphs = []
        for p in article_content.find_all('p'):
            text = p.get_text().strip()
            if len(text) > 30:  # Only substantial paragraphs
                paragraphs.append(text)
        
        if not paragraphs:
            return f"I couldn't extract readable content from this article: {url}"
        
        # Format based on reading level
        if reading_level == "bullet_points":
            # Convert to bullet points
            bullet_points = []
            for para in paragraphs[:8]:  # Limit to 8 paragraphs
                # Split long paragraphs into sentences
                sentences = para.split('. ')
                for sentence in sentences[:2]:  # Max 2 sentences per paragraph
                    if len(sentence.strip()) > 20:
                        bullet_points.append(f"• {sentence.strip()}")
            
            content = '\n'.join(bullet_points)
            
        elif reading_level == "detailed":
            # Full detailed content
            content = '\n\n'.join(paragraphs)
            if len(content) > 2500:
                content = content[:2500] + "..."
                
        else:  # simple
            # Simplified version - first 3-4 paragraphs
            content = '\n\n'.join(paragraphs[:4])
            if len(content) > 1200:
                content = content[:1200] + "..."
        
        response = f"""📰 Article: "{article_title}"
Source: {url}

{content}

💡 I can read this article in different ways:
• Simple summary (current)
• Detailed full content
• Bullet point format

Would you like me to read it differently or explain any part of this article?"""

        logging.info(f"Successfully read article: {url}")
        return response

    except Exception as e:
        logging.error(f"Error reading article {url}: {e}")
        return f"I couldn't read the article from {url}. Please check the URL or try a different article."
    


@function_tool()
async def write_code_with_gemini(
    context: RunContext,  # type: ignore
    programming_request: str,
    language: Optional[str] = "python",
    complexity_level: Optional[str] = "beginner"
) -> str:
    """
    Use Google Gemini to write code based on user requirements.
    
    Args:
        programming_request: Description of what code to write
        language: Programming language (python, javascript, html, css, etc.)
        complexity_level: 'beginner', 'intermediate', 'advanced'
    """
    try:
        import os
        from google.generativeai.client import configure as genai_configure
        from google.generativeai.generative_models import GenerativeModel

        # Configure Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "Sorry, I need a Google API key to help with code writing. Please configure your GOOGLE_API_KEY environment variable."
        
        genai_configure(api_key=api_key)
        
        # Create the model
        model = GenerativeModel('gemini-pro')
        
        # Craft a detailed prompt for code generation
        prompt = f"""
You are a helpful coding assistant for elderly users who may be new to programming. 

Task: {programming_request}
Programming Language: {language}
Complexity Level: {complexity_level}

Please provide:
1. Clean, well-commented code that solves the request
2. Step-by-step explanation of how the code works
3. Simple instructions on how to run or use the code
4. Any necessary setup or installation steps

Make your explanation clear and beginner-friendly, avoiding technical jargon where possible.
If this is for an elderly user, focus on practical applications and provide extra context.

Code Request: {programming_request}
"""
        
        logging.info(f"Generating code with Gemini for: {programming_request}")
        
        # Generate code using Gemini
        response = model.generate_content(prompt)
        
        if response.text:
            formatted_response = f"""💻 **Code Generated for: "{programming_request}"**

**Language:** {(language.title() if language else "Unknown")}
**Complexity:** {(complexity_level.title() if complexity_level else "Unknown")}

{response.text}

---

💡 **Tips for using this code:**
• Copy the code into a text editor or IDE
• Save it with the appropriate file extension (.py for Python, .js for JavaScript, etc.)
• Follow the setup instructions provided above
• Don't hesitate to ask if you need clarification on any part!

🔧 **Need help?**
• Ask me to explain any specific part of the code
• Request modifications or improvements
• Ask for help with setting up your development environment
"""
            
            logging.info(f"Code successfully generated for: {programming_request}")
            return formatted_response
        else:
            return f"I couldn't generate code for '{programming_request}'. Please try rephrasing your request or being more specific about what you need."
    
    except ImportError:
        return "I need the Google Generative AI library to help with code writing. Please install it with: pip install google-generativeai"
    
    except Exception as e:
        logging.error(f"Error generating code with Gemini: {e}")
        return f"I encountered an error while trying to generate code for '{programming_request}'. Please try again or rephrase your request."

@function_tool()
async def explain_code_with_gemini(
    context: RunContext,  # type: ignore
    code_snippet: str,
    language: Optional[str] = "python"
) -> str:
    """
    Use Google Gemini to explain existing code in simple terms.
    
    Args:
        code_snippet: The code to explain
        language: Programming language of the code
    """
    try:
        import os
        from google.generativeai.client import configure as genai_configure
        from google.generativeai.generative_models import GenerativeModel

        # Configure Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "Sorry, I need a Google API key to help explain code. Please configure your GOOGLE_API_KEY environment variable."
        
        genai_configure(api_key=api_key)
        
        # Create the model
        model = GenerativeModel('gemini-pro')
        
        # Craft a prompt for code explanation
        prompt = f"""
You are explaining code to elderly users who may be new to programming. 

Please explain this {language} code in simple, clear terms:

```{language}
{code_snippet}
```

Your explanation should include:
1. What the code does overall (in simple terms)
2. Line-by-line explanation of each important part
3. What the expected output or result would be
4. Any practical applications or uses
5. Common terms explained in everyday language

Make it conversational and avoid technical jargon. Use analogies or real-world examples where helpful.
"""
        
        logging.info(f"Explaining code with Gemini for {language} code")
        
        # Generate explanation using Gemini
        response = model.generate_content(prompt)
        
        if response.text:
            formatted_response = f"""📖 **Code Explanation ({language.title()})**

**Your Code:**
```{language}
{code_snippet}
```

**Explanation:**
{response.text}

---

💡 **Want to learn more?**
• Ask me to explain any specific part in more detail
• Request examples of how to modify this code
• Ask about related programming concepts
• I can help you write similar code for different purposes
"""
            
            logging.info(f"Code explanation completed for {language} code")
            return formatted_response
        else:
            return f"I couldn't explain this code right now. Please try again or ask me to explain specific parts of the code."
    
    except ImportError:
        return "I need the Google Generative AI library to help explain code. Please install it with: pip install google-generativeai"
    
    except Exception as e:
        logging.error(f"Error explaining code with Gemini: {e}")
        return f"I encountered an error while trying to explain the code. Please try again."

@function_tool()
async def debug_code_with_gemini(
    context: RunContext,  # type: ignore
    code_with_error: str,
    error_message: Optional[str] = "",
    language: Optional[str] = "python"
) -> str:
    """
    Use Google Gemini to help debug code and fix errors.
    
    Args:
        code_with_error: The code that has problems
        error_message: Any error message received (optional)
        language: Programming language of the code
    """
    try:
        import os
        from google.generativeai.client import configure as genai_configure
        from google.generativeai.generative_models import GenerativeModel

        # Configure Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "Sorry, I need a Google API key to help debug code. Please configure your GOOGLE_API_KEY environment variable."
        
        genai_configure(api_key=api_key)
        
        # Create the model
        model = GenerativeModel('gemini-pro')
        
        # Craft a prompt for code debugging
        error_section = f"\n\nError Message: {error_message}" if error_message else ""
        
        prompt = f"""
You are helping elderly users debug their {language} code. Please be patient and explain things clearly.

Here's the code that's having problems:

```{language}
{code_with_error}
```{error_section}

Please provide:
1. Identification of what's wrong with the code
2. A corrected version of the code
3. Clear explanation of what was fixed and why
4. Tips to avoid similar errors in the future
5. Step-by-step instructions for testing the fix

Use simple language and be encouraging - debugging can be frustrating for beginners!
"""
        
        logging.info(f"Debugging code with Gemini for {language} code")
        
        # Generate debugging help using Gemini
        response = model.generate_content(prompt)
        
        if response.text:
            formatted_response = f"""🔧 **Code Debugging Help ({language.title()})**

**Your Original Code:**
```{language}
{code_with_error}
```

{f"**Error Message:** {error_message}" if error_message else ""}

**Debugging Analysis:**
{response.text}

---

💡 **Debugging Tips:**
• Save your original code before making changes
• Test small changes one at a time
• Don't get discouraged - even experienced programmers debug constantly!
• Ask me if you need clarification on any of the fixes

🎯 **Next Steps:**
• Try the corrected code
• Let me know if you encounter new errors
• Ask if you want me to explain any part of the solution
"""
            
            logging.info(f"Code debugging completed for {language} code")
            return formatted_response
        else:
            return f"I couldn't analyze the code issues right now. Please try again or describe the specific problem you're experiencing."
    
    except ImportError:
        return "I need the Google Generative AI library to help debug code. Please install it with: pip install google-generativeai"
    
    except Exception as e:
        logging.error(f"Error debugging code with Gemini: {e}")
        return f"I encountered an error while trying to debug the code. Please try again."

@function_tool()
async def learn_programming_with_gemini(
    context: RunContext,  # type: ignore
    topic: str,
    language: Optional[str] = "python",
    learning_style: Optional[str] = "beginner"
) -> str:
    """
    Use Google Gemini to create programming lessons and tutorials.
    
    Args:
        topic: Programming concept to learn (variables, loops, functions, etc.)
        language: Programming language to focus on
        learning_style: 'beginner', 'visual', 'hands-on', 'theoretical'
    """
    try:
        import google.generativeai as genai
        import os
        
        # Configure Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "Sorry, I need a Google API key to create programming lessons. Please configure your GOOGLE_API_KEY environment variable."
        
        genai.configure(api_key=api_key)
        
        # Create the model
        model = genai.GenerativeModel('gemini-pro')
        
        # Craft a prompt for programming education
        prompt = f"""
Create a programming lesson for elderly learners who are new to coding.

Topic: {topic}
Programming Language: {language}
Learning Style: {learning_style}

Please create a lesson that includes:
1. Simple introduction to the concept using everyday analogies
2. Why this concept is useful in real life
3. Basic example with clear explanations
4. A practical exercise they can try
5. Common mistakes to avoid
6. Next steps for learning more

Make it encouraging, patient, and assume no prior programming knowledge.
Use clear, simple language and provide plenty of context.
Include real-world examples that would be relevant to elderly users.
"""
        
        logging.info(f"Creating programming lesson with Gemini for: {topic}")
        
        # Generate lesson using Gemini
        response = model.generate_content(prompt)
        
        if response.text:
            formatted_response = f"""📚 **Programming Lesson: {topic.title()} in {language.title()}**

**Learning Style:** {learning_style.title()}

{response.text}

---

🎓 **Learning Resources:**
• Practice the examples provided above
• Don't rush - take your time to understand each concept
• Ask me questions about anything that's unclear
• Request more examples or different explanations if needed

🌟 **You're doing great!**
Learning to code at any age is an achievement. Take it one step at a time and celebrate small victories!

**What would you like to learn next?**
• Ask me about related programming concepts
• Request more practice exercises
• Get help with any errors you encounter
"""
            
            logging.info(f"Programming lesson created for: {topic}")
            return formatted_response
        else:
            return f"I couldn't create a lesson for '{topic}' right now. Please try asking about a different programming concept."
    
    except ImportError:
        return "I need the Google Generative AI library to create programming lessons. Please install it with: pip install google-generativeai"
    
    except Exception as e:
        logging.error(f"Error creating programming lesson with Gemini: {e}")
        return f"I encountered an error while creating the programming lesson. Please try again."   






@function_tool()
async def read_emails(
    context: RunContext,  # type: ignore
    num_emails: Optional[int] = 5,
    email_folder: Optional[str] = "INBOX",
    unread_only: Optional[bool] = True
) -> str:
    """
    Read emails from Gmail using IMAP.
    
    Args:
        num_emails: Number of recent emails to read (default 5)
        email_folder: Email folder to read from (INBOX, SENT, DRAFTS, etc.)
        unread_only: Whether to only show unread emails (default True)
    """
    try:
        import imaplib
        import email
        from email.header import decode_header
        import os
        from datetime import datetime
        
        # Get credentials from environment variables
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        
        if not gmail_user or not gmail_password:
            return """📧 Email reading failed: Gmail credentials not configured.

Please set up your credentials in the .env file:
• GMAIL_USER=your-email@gmail.com
• GMAIL_APP_PASSWORD=your-app-password

Note: You need a Gmail App Password, not your regular password."""
        
        logging.info(f"Connecting to Gmail for {gmail_user}")
        
        # Connect to Gmail IMAP server
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_user, gmail_password)
        
        # Select the mailbox folder
        mail.select(email_folder)
        
        # Search for emails
        if unread_only:
            status, messages = mail.search(None, 'UNSEEN')
            search_criteria = "unread"
        else:
            status, messages = mail.search(None, 'ALL')
            search_criteria = "all"
        
        if status != 'OK':
            return f"Failed to search emails in {email_folder} folder."
        
        # Get list of email IDs
        email_ids = messages[0].split()
        
        if not email_ids:
            return f"""📧 No {search_criteria} emails found in {email_folder}.

Your mailbox appears to be empty or all emails have been read."""
        
        # Limit number of emails to read
        if num_emails is None:
            num_emails = 5
        recent_emails = email_ids[-num_emails:]  # Get most recent emails
        
        email_summaries = []
        
        for email_id in reversed(recent_emails):  # Show newest first
            try:
                # Fetch the email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if status != 'OK':
                    continue
                
                # Parse the email
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                # Extract email details
                subject = decode_header(email_message["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                from_email = email_message.get("From")
                date_received = email_message.get("Date")
                
                # Get email body
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = email_message.get_payload(decode=True).decode()
                
                # Limit body length for readability
                if len(body) > 300:
                    body = body[:300] + "..."
                
                email_summary = f"""📩 **From:** {from_email}
**Subject:** {subject}
**Date:** {date_received}
**Preview:** {body.strip()[:200]}{"..." if len(body.strip()) > 200 else ""}

---"""
                
                email_summaries.append(email_summary)
                
            except Exception as e:
                logging.error(f"Error processing email ID {email_id}: {e}")
                continue
        
        # Close the connection
        mail.close()
        mail.logout()
        
        if email_summaries:
            response = f"""📬 **Your {search_criteria.title()} Emails ({len(email_summaries)} of {len(email_ids)} total):**

{chr(10).join(email_summaries)}

💡 **Email Management Tips:**
• Ask me to read more emails or check a different folder
• I can help you send replies to any of these emails
• Consider marking important emails for easy finding later
• Ask me to search for emails from specific people or with certain subjects"""
        else:
            response = f"I found {len(email_ids)} {search_criteria} emails but couldn't read their content. There might be formatting issues with these emails."
        
        logging.info(f"Successfully read {len(email_summaries)} emails")
        return response
        
    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP error: {e}")
        return """📧 Email reading failed: Authentication error.

Please check:
• Your Gmail App Password is correct
• You have enabled 2-factor authentication on your Google account
• You have generated an App Password specifically for this application"""
    
    except Exception as e:
        logging.error(f"Error reading emails: {e}")
        return f"I encountered an error while reading your emails: {str(e)}"

@function_tool()
async def search_emails(
    context: RunContext,  # type: ignore
    search_query: str,
    num_results: Optional[int] = 10,
    search_in: Optional[str] = "all"
) -> str:
    """
    Search for specific emails in Gmail.
    
    Args:
        search_query: What to search for (sender, subject, content, etc.)
        num_results: Maximum number of results to return
        search_in: Where to search - 'all', 'subject', 'from', 'body'
    """
    try:
        import imaplib
        import email
        from email.header import decode_header
        import os
        
        # Get credentials
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        
        if not gmail_user or not gmail_password:
            return "Email search failed: Gmail credentials not configured."
        
        logging.info(f"Searching emails for: {search_query}")
        
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_user, gmail_password)
        mail.select("INBOX")
        
        # Construct search criteria based on search_in parameter
        if search_in == "subject":
            search_criteria = f'SUBJECT "{search_query}"'
        elif search_in == "from":
            search_criteria = f'FROM "{search_query}"'
        elif search_in == "body":
            search_criteria = f'BODY "{search_query}"'
        else:  # all
            search_criteria = f'OR OR SUBJECT "{search_query}" FROM "{search_query}" BODY "{search_query}"'
        
        # Search for emails
        status, messages = mail.search(None, search_criteria)
        
        if status != 'OK':
            return f"Failed to search emails for '{search_query}'."
        
        email_ids = messages[0].split()
        
        if not email_ids:
            return f"""🔍 No emails found matching '{search_query}'.

Try searching for:
• A person's name or email address
• Keywords from the subject line
• Words from the email content
• Try broadening your search terms"""
        
        # Limit results
        if num_results is None:
            num_results = 10
        recent_matches = email_ids[-num_results:]  # Get most recent matches
        
        search_results = []
        
        for email_id in reversed(recent_matches):
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                # Extract email details
                subject = decode_header(email_message["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                from_email = email_message.get("From")
                date_received = email_message.get("Date")
                
                search_result = f"""📧 **From:** {from_email}
**Subject:** {subject}
**Date:** {date_received}

---"""
                
                search_results.append(search_result)
                
            except Exception as e:
                logging.error(f"Error processing search result {email_id}: {e}")
                continue
        
        mail.close()
        mail.logout()
        
        response = f"""🔍 **Search Results for '{search_query}' ({len(search_results)} found):**

{chr(10).join(search_results)}

💡 **Search Tips:**
• Try different keywords if you don't find what you're looking for
• Search by sender's name or email address
• Use specific words from the subject line
• Ask me to read any of these emails in full"""
        
        logging.info(f"Email search completed: found {len(search_results)} results")
        return response
        
    except Exception as e:
        logging.error(f"Error searching emails: {e}")
        return f"I encountered an error while searching your emails: {str(e)}"
