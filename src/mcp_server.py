import argparse
import logging
import os
import sys
import time
import json
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastmcp import FastMCP
from instagrapi import Client

# --- INITIAL SETUP & CONFIGURATION ---

# Load environment variables from a .env file
load_dotenv()

# Configure logging for clear, timed output
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# --- KPI & PROMPT CONFIGURATION ---

# Defines the key performance indicators (KPIs) the AI will analyze
CONFIGURABLE_KPIS = {
    "spending": "Flags hot leads already talking about buying.",
    "price_focus": "Tells you if a discount hook will seal the deal.",
    "trust": "No sale without belief in you, simple as that.",
    "sentiment": "Mood check, lets you match tone before pitching.",
    "curiosity": "High question count points to teach-then-sell copy.",
    "language": "The primary language of the user's messages (e.g., 'English', 'Spanish').",
    "personality": "A list of 5 single-word adjectives describing the user's personality.",
    "common_words": "A list of the 5 most common (non-filler) words the user uses.",
}

# The prompt template sent to the AI for conversation analysis
ANALYSIS_PROMPT_TEMPLATE = """
Analyze each user brief. For each user_id, return a minified JSON object with values for these KPIs: {kpi_list}.
For list-based KPIs, return a JSON array of strings. For score-based KPIs, return a float.
Respond with ONLY a single minified JSON object.
---
DATA:
```json
{user_briefs_json}
```
"""

# The prompt template for generating a sales pitch
PITCH_PROMPT_TEMPLATE = """
You are a master salesperson on Instagram. Your tone is super-human, casual, and brief.
**Your Goal:** Generate interest in a product.
**Product:** {product_name} ({product_description})
**Link:** {product_link}
**Rules:**
1.  **DETECT LANGUAGE:** Analyze the user's conversation history and write your pitch in that SAME language.
2.  **BE CONVERSATIONAL:** Your output MUST be a JSON array of 2-4 short strings. Each string is a separate message bubble.
3.  **INCLUDE THE LINK:** Weave the `product_link` naturally into one of the messages.
**Target and their recent conversation history:**
```json
{target_brief_json}
```
**Required Output Format (JSON only):**
A single JSON object where the key is the username and the value is an array of strings.
Example: `{{"@{username}": ["Hey! 👋", "Check this out, thought you'd love it:", "{product_link}"]}}`
"""


# --- MCP SERVER & GLOBAL STATE ---

INSTRUCTIONS = "Insta Buyer is online. Use simple, direct commands to analyze and pitch."
client = Client()
mcp = FastMCP(name="Insta Buyer", instructions=INSTRUCTIONS)

# Global variables to store session state
MY_IG_USER_ID = None
SESSION_ANALYSIS = {}


# --- THE APEX ENGINE (PRIVATE & IMPLICIT) ---

def _run_analysis_if_needed() -> bool:
    """
    Fetches Instagram DMs and sends them to the AI for analysis.
    This function only runs once per session to avoid redundant API calls.
    """
    global SESSION_ANALYSIS
    if SESSION_ANALYSIS:
        return True  # Analysis already completed in this session

    try:
        # Fetch the 20 most recent chats, with up to 20 messages each
        logger.info("Fetching recent conversations for analysis...")
        chats = client.direct_threads(amount=20, thread_message_limit=20)
        
        # Build a payload of user conversations, excluding groups
        for t in chats:
            if t.is_group:
                continue
            data = t.model_dump(mode="json")
            other_user = next((u for u in data.get("users", []) if str(u.get("pk")) != MY_IG_USER_ID), None)
            
            if not other_user:
                continue

            user_id = str(other_user.get("pk"))
            # Create a clean brief of the last 10 messages from the other user
            brief = [
                msg.get("text")
                for msg in data.get("messages", [])
                if msg.get("text") and str(msg.get("user_id")) != MY_IG_USER_ID
            ][:10]

            if brief: # Only include users who have sent messages
                SESSION_ANALYSIS[user_id] = {
                    "username": other_user.get("username"),
                    "brief": brief,
                }

        if not SESSION_ANALYSIS:
            logger.info("No user conversations found to analyze.")
            return True # Successful, but nothing to do

        # Prepare the data and prompt for the AI
        briefs_for_prompt = [{"user_id": uid, "brief": data["brief"]} for uid, data in SESSION_ANALYSIS.items()]
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            kpi_list=json.dumps(list(CONFIGURABLE_KPIS.keys())),
            user_briefs_json=json.dumps(briefs_for_prompt, indent=2),
        )

        print(prompt)  # This sends the prompt to the Claude app
        claude_response_str = input()  # This receives the AI's JSON response
        kpi_results = json.loads(claude_response_str)

        # Merge the AI's KPI results back into our session data
        for user_id, kpis in kpi_results.items():
            if user_id in SESSION_ANALYSIS:
                SESSION_ANALYSIS[user_id]["kpis"] = kpis
        
        logger.info(f"Analysis complete for {len(kpi_results)} users.")
        return True

    except Exception as e:
        logger.error(f"Analysis engine failed: {e}", exc_info=True)
        return False


# --- THE CEO'S COMMAND CONSOLE (PUBLIC TOOLS) ---

@mcp.tool()
def show_analysis_dashboard() -> Dict[str, Any]:
    """COMMAND: Get a full KPI analysis table of recent chats."""
    if not _run_analysis_if_needed():
        return {"success": False, "message": "Analysis failed."}
    if not SESSION_ANALYSIS:
        return {"success": True, "message": "No user conversations found."}

    kpi_names = list(CONFIGURABLE_KPIS.keys())
    header = f"| {'User':<20} |" + " | ".join([f" {kpi.title():<15} " for kpi in kpi_names]) + "|"
    separator = "|-" + "-" * 20 + "-|" + ("-" * 17 + "|") * len(kpi_names)
    rows = [header, separator]

    for data in SESSION_ANALYSIS.values():
        row_str = f"| @{data.get('username', 'N/A'):<18} |"
        kpis = data.get("kpis", {})
        for kpi in kpi_names:
            value = kpis.get(kpi, "N/A")
            # Format cell content for concise display in the table
            if isinstance(value, list):
                cell = ", ".join(value)[:15]
            elif isinstance(value, (int, float)):
                cell = f"{value:.2f}"
            else:
                cell = str(value)[:15]
            row_str += f" {cell:<15} |"
        rows.append(row_str)

    return {"success": True, "analysis_table": "\n".join(rows)}


@mcp.tool()
def show_top_users(kpi: str, count: int = 5, ascending: bool = False) -> Dict[str, Any]:
    """COMMAND: Ranks users by a specific KPI and requests an infographic artifact."""
    if not _run_analysis_if_needed():
        return {"success": False, "message": "Analysis failed."}
    if kpi not in CONFIGURABLE_KPIS:
        return {"success": False, "message": f"Invalid KPI. Use one of: {list(CONFIGURABLE_KPIS.keys())}"}

    # Filter for users that have a numeric score for the chosen KPI
    scored_users = [
        d for d in SESSION_ANALYSIS.values() if isinstance(d.get("kpis", {}).get(kpi), (int, float))
    ]
    if not scored_users:
        return {"success": True, "message": f"No users had a valid score for '{kpi}'."}

    # Sort users and select the top N
    sorted_users = sorted(scored_users, key=lambda item: item["kpis"][kpi], reverse=not ascending)
    top_users = sorted_users[:count]

    # Prepare data for the infographic
    infographic_data = [
        {"username": f"@{user['username']}", "score": user["kpis"][kpi]} for user in top_users
    ]

    # Instead of generating HTML, ask the AI to create a visual artifact
    return {
        "success": True,
        "infographic_request": {
            "prompt": f"Please create a visually stunning, jaw-dropping infographic showing the top {len(top_users)} users for the '{kpi.replace('_', ' ').title()}' KPI. Use the provided data to build a leaderboard.",
            "data": infographic_data,
            "ranking_direction": "Ascending" if ascending else "Descending"
        }
    }


@mcp.tool()
def pitch_best_lead(product_name: str, product_link: str, product_description: str) -> Dict[str, Any]:
    """COMMAND: Finds the single best lead, generates a pitch, and asks for confirmation to send."""
    if not _run_analysis_if_needed():
        return {"success": False, "message": "Analysis failed."}

    leads = [
        d for d in SESSION_ANALYSIS.values() if isinstance(d.get("kpis", {}).get("spending"), (int, float))
    ]
    
    # *** BUG FIX: Check if leads exist BEFORE trying to access the list ***
    if not leads:
        return {"success": True, "message": "No potential leads with a 'spending' score were found."}

    # Identify the single best lead based on the 'spending' KPI
    top_lead = sorted(leads, key=lambda item: item["kpis"]["spending"], reverse=True)[0]

    # Format the prompt to generate the pitch
    pitch_prompt = PITCH_PROMPT_TEMPLATE.format(
        product_name=product_name,
        product_link=product_link,
        product_description=product_description,
        target_brief_json=json.dumps(
            {"username": top_lead["username"], "conversation_history": top_lead["brief"]},
            indent=2,
        ),
    )

    print(pitch_prompt)
    claude_response_str = input()

    try:
        pitch_data = json.loads(claude_response_str)
        username = list(pitch_data.keys())[0]
        messages = pitch_data[username]

        # Return the drafted pitch and ask for final confirmation to send
        return {
            "success": True,
            "confirmation_request": f"I have drafted a {len(messages)}-part message for {username}. Shall I send it?",
            "pitch_to_send": pitch_data,
        }
    except Exception as e:
        return {"success": False, "message": f"Could not process pitch response: {e}"}


@mcp.tool()
def send_confirmed_pitch(pitch_data: Dict[str, List[str]]) -> Dict[str, Any]:
    """(Private Action) Sends the pitch after user confirms in the chat."""
    sent_count = 0
    for username, messages in pitch_data.items():
        try:
            # Remove "@" and get user ID
            clean_username = username.lstrip("@")
            user_id = client.user_id_from_username(clean_username)
            if not user_id:
                logger.warning(f"Could not find user ID for {username}. Skipping.")
                continue

            # Send each message with a realistic delay
            for msg_text in messages:
                client.direct_send(msg_text, user_ids=[user_id])
                time.sleep(2.5)
            
            logger.info(f"Successfully sent pitch to {username}.")
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to engage {username}: {e}")

    return {"success": True, "message": f"Pitch sent to {sent_count} user(s)."}


# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    # Setup command-line argument parsing
    parser = argparse.ArgumentParser(description="Insta Buyer: AI-Powered Instagram DM Sales Engine")
    parser.add_argument("--username", type=str, help="Instagram username")
    parser.add_argument("--password", type=str, help="Instagram password")
    args = parser.parse_args()

    # Get credentials from arguments or environment variables
    username = args.username or os.getenv("INSTAGRAM_USERNAME")
    password = args.password or os.getenv("INSTAGRAM_PASSWORD")

    if not username or not password:
        sys.exit("FATAL: Instagram credentials were not provided via arguments or .env file.")

    # Main application loop
    try:
        logger.info(f"Attempting to log in as {username}...")
        client.login(username, password)
        MY_IG_USER_ID = str(client.user_id)
        logger.info("Login successful. Starting MCP server...")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"FATAL ERROR DURING STARTUP: {e}", exc_info=True)
        sys.exit(1)