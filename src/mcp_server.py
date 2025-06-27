import argparse
import logging
import os
import re
import sys
import time
import json
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastmcp import FastMCP
from instagrapi import Client
from pathlib import Path

# --- INITIAL SETUP & CONFIGURATION ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- KPI & PROMPT CONFIGURATION ---
# NEW: Your expanded, more insightful KPI list
CONFIGURABLE_KPIS = {
    "spending": "Score from 0.0 to 1.0 indicating purchase intent.",
    "price_focus": "Score from 0.0 to 1.0 indicating focus on price/discounts.",
    "trust": "Score from 0.0 to 1.0 indicating trust in the brand.",
    "sentiment": "Score from -1.0 (negative) to 1.0 (positive).",
    "curiosity": "Score from 0.0 to 1.0 indicating how many questions are asked.",
    "language": "The primary language of the user's messages (e.g., 'English', 'Spanish').",
    "personality": "A list of 5 single-word adjectives describing the user's personality.",
    "common_words": "A list of the 5 most common (non-filler) words the user uses."
}

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

PITCH_PROMPT_TEMPLATE = """
You are a master salesperson on Instagram. Your tone is super-human, casual, and brief.
**Your Goal:** Generate interest in a product.
**Product:** {product_name} ({product_description})
**Link:** {product_link}
**Rules:**
1. **DETECT LANGUAGE:** Analyze the user's conversation history and write your pitch in that SAME language.
2. **BE CONVERSATIONAL:** Your output MUST be a JSON array of 2-4 short strings. Each string is a separate message bubble.
3. **INCLUDE THE LINK:** Weave the `product_link` naturally into one of the messages.
**Target and their recent conversation history:**
```json
{target_brief_json}
```
**Required Output Format (JSON only):**
A single JSON object where the key is the username and the value is an array of strings.
Example: `{{"@{username}": ["Hey! 👋", "Check this out, thought you'd love it:", "{product_link}"]}}`
"""

# --- MCP SERVER & GLOBAL STATE ---
INSTRUCTIONS = "Insta Buyer is online. Use the provided command phrases."
client = Client()
mcp = FastMCP(name="Insta Buyer", instructions=INSTRUCTIONS)
MY_IG_USER_ID = None
SESSION_ANALYSIS = {} # In-memory cache for the current session

# --- HELPER FUNCTIONS ---
def _format_message_brief(messages: List[Dict], my_user_id: str) -> List[str]:
    brief = []
    for msg in messages:
        if str(msg.get('user_id')) == my_user_id: continue
        text = msg.get('text')
        if text: brief.append(text[:200])
        else: brief.append(f"[{msg.get('item_type', 'media')}]")
    return brief

# --- THE CEO'S COMMAND CONSOLE (PUBLIC TOOLS) ---

@mcp.tool()
def get_analysis_prompt() -> Dict[str, Any]:
    """
    STEP 1 for Analysis: Fetches chats, caches user data, and returns a prompt for Claude.
    """
    global MY_IG_USER_ID, SESSION_ANALYSIS
    if not MY_IG_USER_ID: MY_IG_USER_ID = str(client.user_id)
    
    try:
        chats_response = client.direct_threads(amount=20, thread_message_limit=20)
    except Exception as e:
        return {"success": False, "message": f"Failed to fetch chats: {e}"}

    # Clear previous analysis and cache new data
    SESSION_ANALYSIS = {}
    user_briefs_for_prompt = []

    for t in chats_response:
        if t.is_group: continue
        thread_data = t.model_dump(mode='json')
        other_user = next((u for u in thread_data.get('users', []) if str(u.get('pk')) != MY_IG_USER_ID), None)
        if not other_user: continue
        
        user_id = str(other_user.get('pk'))
        username = other_user.get('username')
        brief = _format_message_brief(thread_data.get('messages', []), MY_IG_USER_ID)

        # Cache the data needed for later steps
        SESSION_ANALYSIS[user_id] = {"username": username, "brief": brief, "kpis": {}}
        user_briefs_for_prompt.append({"user_id": user_id, "brief": brief})

    if not user_briefs_for_prompt:
        return {"success": True, "message": "No user conversations found to analyze."}

    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        kpi_list=json.dumps(list(CONFIGURABLE_KPIS.keys())),
        user_briefs_json=json.dumps(user_briefs_for_prompt, indent=2)
    )

    return {
        "success": True,
        "action": "Provide the 'prompt_for_analyst' to your analyst (Claude). Then, use the output to run `process_and_show_analysis`.",
        "prompt_for_analyst": prompt
    }

@mcp.tool()
def process_and_show_analysis(kpi_results: Dict[str, Dict]) -> Dict[str, Any]:
    """
    STEP 2 for Analysis: Merges KPI results with cached data and displays the table.
    """
    if not SESSION_ANALYSIS:
        return {"success": False, "message": "No analysis has been run. Please run `get_analysis_prompt` first."}
    if not kpi_results:
        return {"success": False, "message": "KPI results cannot be empty."}

    # Merge results into the cache
    for user_id, kpis in kpi_results.items():
        if user_id in SESSION_ANALYSIS:
            SESSION_ANALYSIS[user_id]["kpis"] = kpis

    kpi_names = list(CONFIGURABLE_KPIS.keys())
    header = f"| {'User':<20} |" + " | ".join([f" {kpi.title():<15} " for kpi in kpi_names]) + "|"
    separator = "|-" + "-"*20 + "-|" + ("-"*17 + "|") * len(kpi_names)
    rows = [header, separator]
    
    for user_id, data in SESSION_ANALYSIS.items():
        username = data.get('username', f'user_{user_id}')
        row_str = f"| @{username:<18} |"
        for kpi in kpi_names:
            score = data['kpis'].get(kpi)
            if isinstance(score, list):
                cell = ", ".join(score)[:15]
            elif isinstance(score, (int, float)):
                cell = f"{score:.2f}"
            else:
                cell = str(score)[:15]
            row_str += f" {cell:<15} |"
        rows.append(row_str)
        
    return {"success": True, "analysis_table": "\n".join(rows)}


@mcp.tool()
def generate_pitch_for_best_lead(product_name: str, product_link: str, product_description: str) -> Dict[str, Any]:
    """
    Finds the single best lead from the last analysis and generates a pitch prompt.
    """
    if not SESSION_ANALYSIS:
        return {"success": False, "message": "Please run an analysis first."}

    leads = [{'user_id': uid, **data} for uid, data in SESSION_ANALYSIS.items() if isinstance(data['kpis'].get('spending'), (int, float))]
    if not leads: return {"success": True, "message": "No potential leads found in the analysis."}
    
    top_lead = sorted(leads, key=lambda item: item['kpis']['spending'], reverse=True)[0]
    
    pitch_prompt = PITCH_PROMPT_TEMPLATE.format(
        product_name=product_name,
        product_link=product_link,
        product_description=product_description,
        target_brief_json=json.dumps({"username": top_lead['username'], "conversation_history": top_lead['brief']}, indent=2)
    )
    
    return {"success": True, "pitch_generation_prompt": pitch_prompt}

@mcp.tool()
def send_conversational_pitch(pitch_data: Dict[str, List[str]]) -> Dict[str, Any]:
    """Sends a sequence of messages from the analyst's pitch output."""
    sent_count = 0
    for username, messages in pitch_data.items():
        try:
            user_id = client.user_id_from_username(username.lstrip('@'))
            if not user_id: continue
            
            for msg_text in messages:
                client.direct_send(msg_text, user_ids=[user_id])
                time.sleep(2.5)
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to engage @{username}: {e}")
            
    if sent_count > 0:
        return {"success": True, "message": f"Pitch successfully sent to {sent_count} user(s)."}
    else:
        return {"success": False, "message": "Failed to send the pitch."}

# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument("--username", type=str, help="Instagram username")
   parser.add_argument("--password", type=str, help="Instagram password")
   args = parser.parse_args()
   username = args.username or os.getenv("INSTAGRAM_USERNAME")
   password = args.password or os.getenv("INSTAGRAM_PASSWORD")
   if not username or not password:
       sys.exit("FATAL: Instagram credentials not provided.")
   try:
       client.login(username, password)
       MY_IG_USER_ID = str(client.user_id)
       mcp.run(transport="stdio")
   except Exception as e:
       logger.error(f"FATAL ERROR DURING STARTUP: {e}", exc_info=True)
       sys.exit(1)