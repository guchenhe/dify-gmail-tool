import base64
import html
import urllib.parse
from collections.abc import Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class ReadEmailsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        try:
            # Get parameters
            query = tool_parameters.get("query", "is:unread")
            max_results = min(max(tool_parameters.get("max_results", 10), 1), 50)
            include_body = tool_parameters.get("include_body", True)
            
            # Get credentials from tool provider
            access_token = self.runtime.credentials.get("access_token")
            
            if not access_token:
                yield self.create_text_message("Error: No access token available. Please authorize the Gmail integration.")
                return
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            # Search for messages
            search_params = {
                "q": query,
                "maxResults": max_results
            }
            
            search_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?{urllib.parse.urlencode(search_params)}"
            
            yield self.create_text_message(f"Searching Gmail for: '{query}' (max {max_results} results)")
            
            search_response = requests.get(search_url, headers=headers, timeout=10)
            
            if search_response.status_code == 401:
                yield self.create_text_message("Error: Access token expired. Please re-authorize the Gmail integration.")
                return
            elif search_response.status_code != 200:
                yield self.create_text_message(f"Error: Gmail API returned status {search_response.status_code}")
                return
            
            search_data = search_response.json()
            messages = search_data.get("messages", [])
            
            if not messages:
                yield self.create_text_message("No emails found matching your query.")
                return
            
            yield self.create_text_message(f"Found {len(messages)} email(s). Fetching details...")
            
            emails = []
            for i, message in enumerate(messages):
                try:
                    message_id = message["id"]
                    
                    # Get message details
                    format_param = "full" if include_body else "metadata"
                    message_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}?format={format_param}"
                    
                    message_response = requests.get(message_url, headers=headers, timeout=10)
                    
                    if message_response.status_code != 200:
                        continue
                    
                    message_data = message_response.json()
                    email_info = self._parse_email(message_data, include_body)
                    emails.append(email_info)
                    
                    # Show progress for every 3 emails
                    if (i + 1) % 3 == 0:
                        yield self.create_text_message(f"Processed {i + 1}/{len(messages)} emails...")
                        
                except Exception as e:
                    continue  # Skip failed messages
            
            if not emails:
                yield self.create_text_message("Error: Could not retrieve email details.")
                return
            
            # Return results
            yield self.create_json_message({
                "emails": emails,
                "total_found": len(emails),
                "query_used": query
            })
            
        except requests.RequestException as e:
            yield self.create_text_message(f"Network error: {str(e)}")
        except Exception as e:
            yield self.create_text_message(f"Error reading emails: {str(e)}")
    
    def _parse_email(self, message_data: dict, include_body: bool = True) -> dict:
        """Parse Gmail message data into a clean format"""
        try:
            payload = message_data.get("payload", {})
            headers = payload.get("headers", [])
            
            # Extract headers
            email_info = {
                "id": message_data.get("id"),
                "thread_id": message_data.get("threadId"),
                "labels": message_data.get("labelIds", []),
                "snippet": message_data.get("snippet", ""),
                "subject": "",
                "from": "",
                "to": "",
                "date": "",
                "body": ""
            }
            
            # Parse headers
            for header in headers:
                name = header.get("name", "").lower()
                value = header.get("value", "")
                
                if name == "subject":
                    email_info["subject"] = value
                elif name == "from":
                    email_info["from"] = value
                elif name == "to":
                    email_info["to"] = value
                elif name == "date":
                    email_info["date"] = value
            
            # Extract body if requested
            if include_body:
                email_info["body"] = self._extract_body(payload)
            
            return email_info
            
        except Exception:
            return {
                "id": message_data.get("id", "unknown"),
                "error": "Failed to parse email"
            }
    
    def _extract_body(self, payload: dict) -> str:
        """Extract email body from Gmail message payload"""
        try:
            # Handle different payload structures
            if "parts" in payload:
                # Multipart message
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain":
                        body_data = part.get("body", {}).get("data")
                        if body_data:
                            return self._decode_base64(body_data)
                    elif part.get("mimeType") == "text/html":
                        body_data = part.get("body", {}).get("data")
                        if body_data:
                            html_content = self._decode_base64(body_data)
                            return self._html_to_text(html_content)
            else:
                # Single part message
                body_data = payload.get("body", {}).get("data")
                if body_data:
                    content = self._decode_base64(body_data)
                    if payload.get("mimeType") == "text/html":
                        return self._html_to_text(content)
                    return content
            
            return "No readable content found"
            
        except Exception:
            return "Error extracting email body"
    
    def _decode_base64(self, data: str) -> str:
        """Decode base64url encoded string"""
        try:
            # Gmail uses base64url encoding, replace characters
            data = data.replace("-", "+").replace("_", "/")
            while len(data) % 4:
                data += "="
            return base64.b64decode(data).decode("utf-8", errors="ignore")
        except Exception:
            return "Error decoding content"
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text"""
        try:
            # Remove HTML tags and decode entities
            import re
            text = re.sub(r"<[^>]+>", "", html_content)
            text = html.unescape(text)
            return text.strip()
        except Exception:
            return html_content
