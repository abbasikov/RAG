import os
import json
from openai import OpenAI
from typing import List, Dict, Optional
from rag_system import RAGSystem
from database import UserDatabase
from email_sender import EmailSender

class StockMarketChatbot:
    def __init__(self, openai_api_key: str, sendgrid_api_key: str,
                 sender_email: str, recipient_email: str):
        """Initialize the Stock Market Chatbot with all components"""
        self.client = OpenAI(api_key=openai_api_key)
        self.rag_system = RAGSystem(openai_api_key)
        self.database = UserDatabase()
        self.email_sender = EmailSender(sendgrid_api_key, sender_email, recipient_email)

        # System instructions for the chatbot
        self.system_instructions = """You are a sharp-tongued, edgy, no-nonsense stock-market genius who shares strong, informed opinions on stocks, macro trends, trading strategies, and economic outlooks.

You keep the conversation confined to stock-market-related topics. You are NOT a financial advisor and do NOT offer personalized investment advice. Instead, you speak with the voice of a brilliant market wizard who has seen it all, drawing from deep financial analysis, historical context, and technical know-how.

Your tone is bold, witty, and unapologetically direct. You refer to the user as a peer but looking for wisdom from an experienced veteran investor — treating them like a fellow market maverick, not a novice. You make clear that users are responsible for their own due diligence and investment decisions.

You help users understand market dynamics, dissect earnings, highlight risks, and explore trading setups. You encourage education, not dependency. You're here to make users smarter and more market-aware, not to hand out guaranteed gains.

CRITICAL DATA COLLECTION RULES:
You MUST collect the following information from the user during the conversation:
1. Name
2. Email address
3. Income level

WHEN YOU DETECT ANY OF THESE IN THE USER'S MESSAGE, YOU MUST IMMEDIATELY CALL THE save_user_data FUNCTION:
- If user says "Call me [Name]", "My name is [Name]", "I'm [Name]" → CALL save_user_data with name parameter
- If user provides an email address → CALL save_user_data with email parameter
- If user mentions their income/salary → CALL save_user_data with income parameter

Ask for these details ONE AT A TIME, weaving them naturally into the conversation. Don't make it feel like a questionnaire. For example:
- "Hey, what should I call you, market maverick?"
- "If you want me to send you some killer resources, drop your email"
- "What's your income bracket? Just curious where you're playing from - helps me tailor the advice"

After calling save_user_data successfully, acknowledge the information naturally in your response.

Use the knowledge base to support your responses when relevant. The knowledge base contains market data and insights that you can reference."""

        # Define the function tool for saving user data
        # Note: Responses API format is different from Chat Completions API
        # When strict=True, all properties must be in required array, so we use strict=False
        self.tools = [
            {
                "type": "function",
                "name": "save_user_data",
                "description": "CRITICAL: Save user information (name, email, or income) to the database. You MUST call this function immediately when the user provides their name (e.g., 'Call me John', 'My name is...'), email address, or income level. Pass only the field(s) that were just provided by the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "The unique session ID for this user (will be provided in instructions)"
                        },
                        "name": {
                            "type": "string",
                            "description": "The user's name when they tell you their name"
                        },
                        "email": {
                            "type": "string",
                            "description": "The user's email address when they provide it"
                        },
                        "income": {
                            "type": "string",
                            "description": "The user's income level when they mention it"
                        }
                    },
                    "required": ["session_id"]
                }
            }
        ]

    def save_user_data_tool(self, session_id: str, name: str = None,
                           email: str = None, income: str = None) -> Dict:
        """Tool function to save user data"""
        try:
            # Update database
            success = self.database.update_user_data(session_id, name, email, income)

            if success:
                # Check if all data is collected
                user_data = self.database.get_user_data(session_id)

                if user_data and self.database.is_data_complete(session_id):
                    # Send email with complete data
                    email_sent = self.email_sender.send_user_data(user_data)

                    return {
                        "success": True,
                        "data_complete": True,
                        "email_sent": email_sent,
                        "message": "All user data collected and email sent!"
                    }
                else:
                    return {
                        "success": True,
                        "data_complete": False,
                        "message": "User data updated successfully"
                    }
            else:
                return {
                    "success": False,
                    "message": "Failed to update user data"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }

    def create_conversation(self, session_id: str) -> Optional[str]:
        """Create a new conversation using OpenAI Conversations API"""
        try:
            response = self.client.conversations.create(
                metadata={"session_id": session_id}
            )
            return response.id
        except Exception as e:
            print(f"Error creating conversation: {e}")
            return None

    def get_response(self, user_message: str, session_id: str,
                    conversation_id: str = None) -> Dict:
        """Get response from the chatbot using OpenAI Responses API"""
        try:
            print(f"[DEBUG] Processing message: {user_message[:50]}...")

            # Initialize session in database if needed
            self.database.create_session(session_id)

            # Create conversation if it doesn't exist
            # Note: Conversation history is managed by OpenAI's Conversations API
            if not conversation_id:
                print("[DEBUG] Creating new conversation...")
                conversation_response = self.client.conversations.create(
                    metadata={"session_id": session_id}
                )
                conversation_id = conversation_response.id
                print(f"[DEBUG] Created conversation: {conversation_id}")

            # Get relevant context from RAG system
            print("[DEBUG] Searching RAG system...")
            rag_context = self.rag_system.get_context(user_message)
            print(f"[DEBUG] RAG context found: {len(rag_context) if rag_context else 0} chars")

            # Prepare the input with context
            user_input = user_message
            if rag_context:
                user_input = f"{user_message}\n\n[Internal Context - use this to inform your response]:\n{rag_context}"

            # Create response using Responses API with conversation
            # Add session_id to instructions so the model knows what to pass to the function
            instructions_with_session = f"{self.system_instructions}\n\nIMPORTANT: The current session_id is: {session_id}. Use this exact session_id when calling the save_user_data function."

            request_params = {
                "model": "gpt-4o",
                "input": user_input,
                "instructions": instructions_with_session,
                "tools": self.tools,
                "tool_choice": "auto",
                "store": True,
                "conversation": conversation_id  # Always use conversation for context
            }

            print(f"[DEBUG] Calling OpenAI Responses API with conversation {conversation_id}...")
            response = self.client.responses.create(**request_params)
            print(f"[DEBUG] Response received. Status: {response.status}")

            # Process the response
            assistant_message = ""
            tool_calls = []

            print(f"[DEBUG] Processing {len(response.output)} output items")

            if response.output:
                for i, output_item in enumerate(response.output):
                    print(f"[DEBUG] Output item {i}: type={output_item.type}")

                    if output_item.type == "message":
                        # Extract text content
                        for content in output_item.content:
                            if content.type == "output_text":
                                assistant_message += content.text
                                print(f"[DEBUG] Added text: {content.text[:50]}...")

                    elif output_item.type == "function_call":
                        # Handle function calls from Responses API
                        # The structure is: output_item.name and output_item.arguments (not nested under .function)
                        print(f"[DEBUG] Function call detected")
                        try:
                            # Parse arguments if they're a string
                            if hasattr(output_item, 'arguments'):
                                args = json.loads(output_item.arguments) if isinstance(output_item.arguments, str) else output_item.arguments
                            else:
                                args = {}

                            function_name = output_item.name if hasattr(output_item, 'name') else None

                            if function_name:
                                print(f"[DEBUG] Function: {function_name}, Args: {args}")
                                tool_calls.append({
                                    "function_name": function_name,
                                    "arguments": args
                                })
                        except Exception as e:
                            print(f"[ERROR] Error parsing function call: {e}")
                            print(f"[ERROR] Output item attributes: {dir(output_item)}")

            print(f"[DEBUG] Final message length: {len(assistant_message)} chars")
            print(f"[DEBUG] Tool calls: {len(tool_calls)}")

            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls:
                if tool_call["function_name"] == "save_user_data":
                    print(f"[DEBUG] Executing save_user_data with args: {tool_call['arguments']}")
                    result = self.save_user_data_tool(**tool_call["arguments"])
                    tool_results.append(result)
                    print(f"[DEBUG] Tool result: {result}")

            # Handle tool calls in a loop (like the working demo)
            while tool_calls and not assistant_message:
                print("[DEBUG] Tool called but no message. Preparing function outputs for next request...")

                # Build function output items for the input parameter
                function_output_items = []
                for i, output_item in enumerate(response.output):
                    if output_item.type == "function_call":
                        # Get the corresponding result
                        result = tool_results[i] if i < len(tool_results) else {"success": True, "message": "Function executed"}

                        # Get the function call ID - try multiple attributes
                        function_call_id = None
                        for attr in ['call_id', 'id', 'tool_call_id']:
                            if hasattr(output_item, attr):
                                function_call_id = getattr(output_item, attr)
                                break

                        if not function_call_id:
                            function_call_id = f"call_{i}"

                        try:
                            print(f"[DEBUG] Preparing function output for call {function_call_id}")

                            # Create the function call output item according to the docs
                            function_output_items.append({
                                "type": "function_call_output",
                                "call_id": function_call_id,
                                "output": json.dumps(result)
                            })
                        except Exception as e:
                            print(f"[ERROR] Failed to prepare function output: {e}")

                # Now make a follow-up request with function outputs using CONVERSATION (not previous_response_id)
                if function_output_items:
                    print(f"[DEBUG] Making follow-up request with {len(function_output_items)} function outputs...")
                    follow_up_response = self.client.responses.create(
                        model="gpt-4o",
                        input=function_output_items,  # Provide function outputs as input
                        conversation=conversation_id,  # Keep using conversation to maintain context
                        instructions=instructions_with_session,
                        tools=self.tools,
                        store=True
                    )

                    # Reset for next iteration
                    tool_calls = []
                    tool_results = []

                    # Extract the follow-up message or more tool calls
                    if follow_up_response.output:
                        for output_item in follow_up_response.output:
                            if output_item.type == "message":
                                for content in output_item.content:
                                    if content.type == "output_text":
                                        assistant_message += content.text
                                        print(f"[DEBUG] Follow-up message: {content.text[:50]}...")

                            elif output_item.type == "function_call":
                                # Handle additional function calls
                                print(f"[DEBUG] Additional function call detected")
                                try:
                                    if hasattr(output_item, 'arguments'):
                                        args = json.loads(output_item.arguments) if isinstance(output_item.arguments, str) else output_item.arguments
                                    else:
                                        args = {}

                                    function_name = output_item.name if hasattr(output_item, 'name') else None

                                    if function_name:
                                        tool_calls.append({
                                            "function_name": function_name,
                                            "arguments": args
                                        })

                                        # Execute immediately
                                        if function_name == "save_user_data":
                                            result = self.save_user_data_tool(**args)
                                            tool_results.append(result)
                                except Exception as e:
                                    print(f"[ERROR] Error parsing additional function call: {e}")

                    # Update response for next iteration
                    response = follow_up_response
                else:
                    break

            # Get the actual conversation ID from response
            # Note: Messages are stored in OpenAI's Conversations API, not locally
            actual_conversation_id = conversation_id
            if hasattr(response, 'conversation') and response.conversation:
                if hasattr(response.conversation, 'id'):
                    actual_conversation_id = response.conversation.id
                elif isinstance(response.conversation, str):
                    actual_conversation_id = response.conversation

            result = {
                "success": True,
                "message": assistant_message,
                "response_id": response.id,
                "conversation_id": actual_conversation_id,
                "tool_calls": tool_calls,
                "tool_results": tool_results,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            print(f"[DEBUG] Returning result with message length: {len(assistant_message)}, conversation: {actual_conversation_id}")
            return result

        except Exception as e:
            print(f"[ERROR] Error getting response: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "error": str(e)
            }

    def get_user_data_status(self, session_id: str) -> Dict:
        """Get the status of user data collection"""
        user_data = self.database.get_user_data(session_id)
        if not user_data:
            return {
                "name": None,
                "email": None,
                "income": None,
                "complete": False
            }

        return {
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "income": user_data.get("income"),
            "complete": self.database.is_data_complete(session_id)
        }
