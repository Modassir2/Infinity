import ai_tools.functions as functions

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time. Use this before scheduling reminders, timers, delayed opens, or WhatsApp messages.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a mathematical expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "weather",
            "description": "Get current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string",}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open an application by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The name of the application to open (e.g. 'Chrome', 'Spotify', 'Calculator')"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Open a website URL in the browser",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The website URL to open"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_battery_status",
            "description": "Get current battery percentage and Charging status",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "view_memory",
            "description": "View the current user's saved memory",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_memory",
            "description": "Add text to the current user's memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to remember"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_memory",
            "description": "Remove text from the current user's memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Exact text to forget"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_users",
            "description": "List all registered users",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "register_user",
            "description": "Register a new user",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the new user"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_user",
            "description": "Delete a user and all their memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the user to delete"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wiki_search",
            "description": "Search Wikipedia and get a summary on a topic. If the result says topic is ambiguous, search again with more specific term.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic to search on Wikipedia"
                    },
                    "sentences": {
                        "type": "integer",
                        "description": "Number of sentences to return (default 5, max 10)"
                    }
                },
                "required": ["query"]
            }
        }
    },
   {
        "type": "function",
        "function": {
            "name": "open_later",
            "description": "Silently open a URL in the browser after a delay with NO notification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to open"
                    },
                    "delay_minutes": {
                        "type": "integer",
                        "description": "Minutes to delay opening"
                    }
                },
                "required": ["url", "delay_minutes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notify",
            "description": "Send a notification to user. Use to set reminders/timers. Set on_click to set URL to open on clicking the notification. Use duration to schedule reminder/timer.",   
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title to be shown in notification"
                    },
                    "body": {
                        "type": "string",
                        "description": "Body of the notification"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Duration *in minutes* after which the notification will be sent, default 0 mins"
                    },
                    "on_click": {
                        "type": "string",
                        "description": "Link to open when clicked on notification"
                    }
                },
                "required": ['title']
            }
        }
    },
     {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Open Gmail in the browser with recipient, subject, and body pre-filled. Use this to draft email. Draft a subject and body yourself based on the user's context. Then call this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line — draft yourself based on context"
                    },
                    "body": {
                        "type": "string",
                        "description": "Full email body text — draft yourself based on what the user wants to say"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp",
            "description": "Send WhatsApp message to a phone number. Phone number must be in full international format. Draft the message yourself.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Recipient phone number in full international format, eg +919875380572"
                    },
                    "message": {
                        "type": "string",
                        "description": "The text to send"
                    }
                },
                "required": ["phone", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_contacts",
            "description": "Search contacts for phone number and email ID by name",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name search. Case-insensitive partial match."
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_contact",
            "description": "Save a new contact with a name, phone number, and email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full name of the contact"
                    },
                    "phone": {
                        "type": "string",
                        "description": "Phone number in full international format eg +919875380572"
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address to save"
                    }
                },
                "required": ["name", "phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_contact",
            "description": "Delete a contact by name from the contacts list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Exact name of the contact to delete"
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_unread_whatsapp_chats",
            "description": "Open WhatsApp, scan the inbox for all unread or new messages, read the actual chat messages for each unread conversation.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reply_whatsapp_by_name",
            "description": "Send a WhatsApp message to a contact by their display name (as it appears in WhatsApp). Use this after get_unread_whatsapp_chats when the user says 'reply to [name]' or 'tell [name] that...'. You already know the name from reading the chats — no phone number needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_name": {
                        "type": "string",
                        "description": "The contact's display name exactly as it appeared in the WhatsApp chat list"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message to send. Draft yourself based on context unless user gave you exact words."
                    }
                },
                "required": ["contact_name", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_whatsapp_chat",
            "description": "Read the last few messages of a WhatsApp chat with a contact, decide if a reply is suitable and send it using send_whatsapp tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Phone number in full international format eg +919875380572"
                    },
                    "count": {
                        "type": "integer",
                        "description": "The number of messages to view from the last, default 5, max 50"
                    }
                },
                "required": ["phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_open_windows",
            "description": "List all currently open windows on the user's computer by title.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "capture_screenshot",
            "description": "Step 1 of 2 for screenshots. Get window_title by asking user and using list_open_windows tool. After this succeeds, STOP and ask: where would you like to save it? (say Desktop, or give a folder path)",
            "parameters": {
                "type": "object",
                "properties": {
                    "window_title": {
                        "type": "string",
                        "description": "A keyword from the window title to match (e.g. 'Chrome', 'Adobe', 'Code'). Case-insensitive partial match."
                    }
                },
                "required": ["window_title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_screenshot",
            "description": "Step 2 of 2 for screenshots. Save the captured screenshot from Step 1 to disk. Only call this after the user has told you where to save it. If they say 'Desktop' or give no preference, pass an empty string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "save_path": {
                        "type": "string",
                        "description": "Where to save the PNG. Can be: empty string or 'desktop' for Desktop or a full file path like C:/Users/user/Documents/myshot.png"
                    }
                },
                "required": []
            }
        }
    }
]

TOOL_MAP = {
    "get_current_time": functions.get_current_time,
    "calculate": functions.calculate,
    "weather": functions.weather,
    "open_app": functions.open_app,
    "open_website": functions.open_website,
    "get_battery_status": functions.get_battery_status,
    "view_memory": functions.view_memory,
    "add_memory": functions.add_memory,
    "remove_memory": functions.remove_memory,
    "list_users": functions.list_users,
    "register_user": functions.register_user,
    "delete_user": functions.delete_user,
    "wiki_search": functions.wiki_search,
    "notify": functions.notify,
    "open_later": functions.open_later,
    "send_email": functions.send_email,
    "send_whatsapp": functions.send_whatsapp,
    "search_contacts": functions.search_contacts,
    "save_contact": functions.save_contact,
    "delete_contact": functions.delete_contact,
    "get_unread_whatsapp_chats": functions.get_unread_whatsapp_chats,
    "reply_whatsapp_by_name": functions.reply_whatsapp_by_name,
    "read_whatsapp_chat": functions.read_whatsapp_chat,
    "list_open_windows": functions.list_open_windows,
    "capture_screenshot": functions.capture_screenshot,   
    "save_screenshot": functions.save_screenshot,
}
