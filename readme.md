
![Buyer Whisperer banner](assets/banner.jpg)

# The Instagram Buyer Whisperer

**Turn Your Instagram DMs into an AI-Powered Sales Engine.**

Buyer Whisperer is an intelligent command center that plugs directly into your Instagram DMs. Built on the revolutionary **Gala Labs MCP Server**, this tool uses AI to analyze conversations, surface your hottest leads, and help you craft perfect, human-like pitches to close more deals.

---

<p align="center">
  <video src="assets/demo.mp4" width="720" controls loop muted></video>
</p>

---
<div align="center">

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge) ![Python Version](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white) ![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg?style=for-the-badge)

</div>

> This project is a proud submission to the **Gala Labs MCP Hackathon**. Our mission was to take the powerful, open-source foundation they provided and forge it into a weapon for sales and marketing professionals. A massive thank you to the incredible team at **Gala Labs** for unlocking this new frontier in AI-powered communication.

---

## 💡 The Problem: Your DMs are a Goldmine You Can't See

Your Instagram DMs are filled with critical sales signals. Customers asking about price, showing trust, hinting at a purchase... but it's all buried in thousands of lines of text. You can't scale your intuition, and valuable leads slip through the cracks every day.

## ✨ The Solution: AI-Powered Sales Intelligence

Buyer Whisperer acts as your personal AI analyst. It reads your latest conversations and instantly tells you:

*   **WHO is ready to buy?** (`spending` score)
*   **WHO trusts your brand?** (`trust` score)
*   **WHO is a price-sensitive bargain hunter?** (`price_focus` score)
*   **WHAT is the mood of the conversation?** (`sentiment` score)
*   **WHO is genuinely curious and needs information?** (`curiosity` score)

It doesn't just give you data; it gives you a ranked list of leads and helps you talk to them like a real person.

---

## 🛠️ Installation & Setup Guide

Get up and running in under 5 minutes.

### Prerequisites

*   Python 3.11+
*   **The Claude Desktop App** (This is essential for the interactive workflow)
*   An active Instagram account

### Step 1: Clone the Repository
Open your terminal and run the following commands:
```bash
git clone https://github.com/trypeggy/instagram_dm_mcp.git
cd instagram_dm_mcp
```

### Step 2: Install Dependencies
This project uses standard Python packages.
```bash
pip install -r requirements.txt
```

### Step 3: Configure Your Instagram Credentials
Create a `.env` file to securely store your credentials. The easiest way is to copy the example file:
```bash
cp env.example .env
```
Now, open the `.env` file in your favorite text editor and add your Instagram username and password.

### Step 4: Connect to the Claude Desktop App
This is the magic step that links Buyer Whisperer to your AI.

*   Find your Claude configuration file:
    *   **On Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
    *   **On Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
*   Open the file and add the following server configuration.

> **IMPORTANT:** You **must** replace `FULL/PATH/TO/instagram_dm_mcp` with the actual, absolute path to the project folder on your computer.

```json
{
  "mcpServers": {
    "insta_buyer": {
       "command": "python",
       "args": [
         "FULL/PATH/TO/instagram_dm_mcp/main.py"
       ]
    }
  }
}
```

### Step 5: Restart Claude
Completely quit and restart the Claude Desktop app. If successful, **"Buyer Whisperer"** will now appear as an available tool in the tool-use panel.

---

## 🎤 The "60-Second CEO" Demo

This is how you go from zero to a ready-to-send, AI-generated pitch in under a minute.

**1. Get the Analysis Prompt**
> **Your Command:** `Get my analysis prompt.`
>
> **What Happens:** Buyer Whisperer fetches your latest DMs and gives you a single, optimized prompt to send to your AI analyst (Claude).

**2. Get the Analysis Results**
> **Your Action:** Copy the prompt from Step 1 and paste it into a new Claude chat. Claude will return a single, minified JSON object containing all the KPI scores.

**3. Display Your Intelligence Dashboard**
> **Your Command:** `Here are the results, show me the table: [paste the KPI JSON from Claude here]`
>
> **What Happens:** Buyer Whisperer instantly processes the scores and displays a full intelligence dashboard, showing you exactly who to focus on.

**4. Generate a Pitch for Your Top Lead**
> **Your Command:** `Now, generate a pitch for our new 'Avenger' sunglasses. Link is https://example.com/avenger.`
>
> **What Happens:** The system identifies your best lead from the analysis and gives you a *new* prompt, specifically designed for Claude to write a perfect, conversational pitch.

**5. Deploy the Pitch**
> **Your Action:** Give the pitch prompt to Claude. It will return a JSON object like `{"@username": ["message 1", "message 2"]}`.
>
> **Your Command:** `That pitch is perfect. Send it: [paste the pitch JSON here]`
>
> **What Happens:** Buyer Whisperer sends the messages one by one, with human-like delays, to close the deal.

---

## 🧰 Full Tool Reference

Buyer Whisperer includes a powerful suite of both high-level "Command" tools and low-level "Foundation" tools.

### ⭐ **Command & Analysis Tools** ⭐

| Tool Name | Description |
| :--- | :--- |
| `get_analysis_prompt` | **STEP 1:** Fetches chats and generates a prompt for AI analysis. |
| `process_and_show_table` | **STEP 2:** Takes AI results and displays the final KPI dashboard. |
| `generate_pitch_for_best_lead` | Identifies the top lead and generates a prompt to craft a perfect pitch. |
| `send_conversational_pitch` | Sends a multi-message, human-like pitch sequence. |

### 🔩 **Foundation Tools (The Original Gala Labs Suite)** 🔩

| Tool Name | Description |
| :--- | :--- |
| `send_message` | Send a simple text message to a user by username. |
| `send_photo_message` | Send a photo from a local file path. |
| `send_video_message` | Send a video from a local file path. |
| `list_chats` | Get a raw list of DM threads from your account. |
| `list_messages` | Get a raw list of messages from a specific thread ID. |
| `mark_message_seen` | Mark a specific message in a thread as "seen". |
| `list_pending_chats` | Get DM threads from your pending/requests inbox. |
| `search_threads` | Search your DM threads by username or keyword. |
| `get_thread_by_participants`| Get a DM thread by providing a list of participant user IDs. |
| `get_thread_details` | Get the full, raw details for a specific thread ID. |
| `get_user_id_from_username` | Get a user's numerical ID from their username. |
| `get_username_from_user_id` | Get a user's username from their numerical ID. |
| `get_user_info` | Get detailed public profile information about a user. |
| `check_user_online_status` | Check the real-time presence/online status of users. |
| `search_users` | Search for Instagram users by their name or username. |
| `get_user_stories` | Get recent, active stories from a user. |
| `like_media` | Like or unlike a specific media post. |
| `get_user_followers` | Get a list of followers for a specific user. |
| `get_user_following` | Get a list of users that a specific user is following. |
| `get_user_posts` | Get recent posts from a user's feed. |
| `list_media_messages` | List only the messages in a thread that contain photos or videos. |
| `download_media_from_message` | Download a photo/video sent directly in a DM. |
| `download_shared_post_from_message` | Download a post or reel that was shared in a DM. |
| `delete_message` | Delete a message you sent in a DM. |
| `mute_conversation` | Mute or unmute a DM conversation. |

---

## License

This project is licensed under the MIT License. 

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
