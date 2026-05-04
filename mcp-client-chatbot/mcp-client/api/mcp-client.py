from typing import Optional
from contextlib import AsyncExitStack
import traceback
from utils import logger
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from datetime import datetime
import json 
import os
import ollama

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()   #dynamically manages and combines multiple context managers and cleanup functions
        self.llm = ollama
        self.tools = [] #to get all the tools from MCP server
        self.messages = [] #chain of thought of LLM
        self.logger = logger
    
    #connect to MCP server
    async def connect_mcp(self, server_script_path:str):
        try:
            is_python = server_script_path.endswith(".py")
            is_js = server_script_path.endswith(".js")
            if not (is_python or is_js):
                raise ValueError("Server Script must be .py or .js file")
            
            command = "python" if is_python else "node"
            server_params = StdioServerParameters(
                command=command, args=[server_script_path], env=None
            )
            
            #stdio client helps connect Anthropic with MCP server (custom)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(     
                ClientSession(self.stdio, self.write)
            )

            #initialise the session
            await self.session.initialize()
            self.logger.info("Connected to MCP Server")

            #tool call 
            mcp_tools = await self.get_mcp_tools()
            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }for tool in mcp_tools
            ]

            self.logger.info(f"Available tools:{self.tools}")

        except Exception as e:
            self.logger.info(f"Error connecting to MCP server: {e}")
            traceback.print_exc()
            raise
            
        
    #call MCP tools

    #get MCP tools
    async def get_mcp_tools(self):
        #alreay initilaised server with awaiting feature so that we wait for the repsonse
        try:
            response = await self.session.list_tools()
            return response.tools
        
        except Exception as e:
            self.logger.info(f"Error in getting MCP tools: {e}")
            raise

    # process query 
    def process_query(query:str) -> str:
        pass

    #call LLM - helper function

    #clean up - delete all the MCP server connection to avoid errors
    async def cleanup(self):
        try:
            await self.exit_stack.aclose()
            self.logger.info("Disconnected from MCP server")
        except Exception as e:
            self.logger.info(f"Error during cleanup: {e}")
            traceback.print_exc()
            raise



    #log conversation



