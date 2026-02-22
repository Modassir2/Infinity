import ai_tools.functions as functions

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "current_time",
            "description": "Get the current date and time",
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
            "description": "Get the current weather for a city",
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
            "description": "Open an application or program on the user's computer by name",
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
            "description": "Open a website or URL in the default browser",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The website URL to open (e.g. 'youtube.com', 'https://github.com')"
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
            "description": "Get the current battery percentage and Charging status",
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
            "description": "Search Wikipedia and get a summary on a topic. If the result says the topic is ambiguous, search again with a more specific term.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic to search for on Wikipedia"
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
            "description": "Silently open a URL in the browser after a delay with NO notification. Use ONLY when user says things like 'open X in Y minutes' with no mention of reminder or notification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to open"
                    },
                    "delay_minutes": {
                        "type": "integer",
                        "description": "How many minutes to wait before opening"
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
            "description": "Show a toast notification to the user. Use when user wants to be REMINDED of something. If on_click is a URL, clicking opens it. Use duration to schedule it in the future. Do NOT use this just to open a link silently — use open_later for that.",   
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
                        "description": "Duration *in minutes* after which the notification will be sent. Leave empty to send notification immediatly"
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
            "description": "Open Gmail in the browser with recipient, subject, and body pre-filled. Use this when the user wants to write or send an email. First ask the user for the recipient email if not given. Then draft a subject and body yourself based on the user's context. Then call this tool.",
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
                        "description": "Full email body text — draft this yourself based on what the user wants to say"
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
            "description": "Send a WhatsApp message to a phone number. Ask for the recipient's phone number (full international format) if not provided. ALWAYS draft the message yourself.",
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
]

TOOL_MAP = {
    "current_time": functions.current_time,
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
}

if __name__=="__main__":
    print(f"Tools count: {len(TOOL_MAP)}")
    chrs=len(str(TOOLS))
    print(f"Tokens count: {chrs/4}")