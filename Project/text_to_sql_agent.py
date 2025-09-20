#!/usr/bin/env python3
"""
A CLI agent for CloudTrail SQL queries with async and streaming support
"""

import asyncio
import boto3
import json
import argparse
import time
import os
import sys
from datetime import datetime
from strands import Agent, tool
from strands.models import BedrockModel
from botocore.config import Config
from strands.telemetry import StrandsTelemetry

# Initialize telemetry (only if explicitly enabled)
if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
    StrandsTelemetry().setup_otlp_exporter()
if os.environ.get("OTEL_CONSOLE"):
    StrandsTelemetry().setup_console_exporter()

AWS_REGION = os.getenv('AWS_DEFAULT_REGION')
DATABASE_NAME = os.getenv('DATABASE_NAME')
TABLE_NAME = os.getenv('TABLE_NAME')
ATHENA_RESULTS_BUCKET = os.getenv('ATHENA_RESULTS_BUCKET')

@tool
def get_current_date() -> str:
    """Get current date values for today/this month queries."""
    print("🗓️  Getting current date...")
    now = datetime.now()
    return f"Today: year={now.year}, month={now.month}, day={now.day}"

@tool
def get_table_schema() -> str:
    """Get the schema of the CloudTrail table from Glue catalog."""
    print("📋 Fetching table schema from Glue catalog...")
    glue = boto3.client('glue', region_name=AWS_REGION)
    
    try:
        response = glue.get_table(
            DatabaseName=DATABASE_NAME,
            Name=TABLE_NAME
        )
        
        columns = response['Table']['StorageDescriptor']['Columns']
        schema_info = []
        for col in columns:
            schema_info.append(f"{col['Name']}: {col['Type']}")
        
        schema_result = "Available columns: " + ", ".join(schema_info)

        return schema_result
    except Exception as e:
        error_msg = f"Failed to get table schema: {str(e)}"

        return error_msg

@tool
def get_query_details(query_id: str) -> str:
    """Get detailed error information for a failed Athena query."""
    print(f"🔍 Getting query details for: {query_id}")
    athena = boto3.client('athena', region_name=AWS_REGION)
    
    try:
        result = athena.get_query_execution(QueryExecutionId=query_id)
        status_info = result['QueryExecution']['Status']
        
        details = f"Query ID: {query_id}\n"
        details += f"Status: {status_info['State']}\n"
        
        if 'StateChangeReason' in status_info:
            details += f"Reason: {status_info['StateChangeReason']}\n"
        
        if 'AthenaError' in status_info:
            error = status_info['AthenaError']
            details += f"Error Category: {error.get('ErrorCategory', 'Unknown')}\n"
            details += f"Error Type: {error.get('ErrorType', 'Unknown')}\n"
            details += f"Error Message: {error.get('ErrorMessage', 'No message')}\n"
        
        return details
    except Exception as e:
        return f"Failed to get query details: {str(e)}"

@tool
def run_athena_query(sql: str) -> str:
    """Execute SQL on Athena and get results."""
    print(f"⚡ Executing SQL: {sql}")
    athena = boto3.client('athena', region_name=AWS_REGION)
    
    response = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={'Database': DATABASE_NAME},
        ResultConfiguration={'OutputLocation': f's3://{ATHENA_RESULTS_BUCKET}/temp/athena/results/'}
    )
    
    query_id = response['QueryExecutionId']
    print(f"🆔 Query ID: {query_id}")
    
    # Wait for completion
    while True:
        result = athena.get_query_execution(QueryExecutionId=query_id)
        status = result['QueryExecution']['Status']['State']
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)
    
    if status == 'SUCCEEDED':
        results = athena.get_query_results(QueryExecutionId=query_id)
        rows = results['ResultSet']['Rows']
        
        if len(rows) > 1:
            total_rows = len(rows) - 1  # Exclude header
            
            # Check if result is too large for model context
            if total_rows > 50:
                return f"Query successful. Found {total_rows} results. Dataset is too large for AI analysis. Please review the results manually in Athena console using Query ID: {query_id}"
            
            # Small result - return data for AI analysis
            data_rows = []
            for row in rows[1:]:  # Skip header
                row_data = []
                for col in row['Data']:
                    row_data.append(col.get('VarCharValue', 'NULL'))
                data_rows.append(row_data)
            return f"Query successful. Results ({total_rows} rows): {data_rows}"
        else:
            return "Query successful but no data returned."
    else:
        # Get error details immediately
        error_details = ""
        if 'StateChangeReason' in result['QueryExecution']['Status']:
            error_details = result['QueryExecution']['Status']['StateChangeReason']
        print(f"❌ Query Error: {error_details}")
        return f"Query failed with status: {status}. Error: {error_details}. Query ID: {query_id}"

async def process_agent_stream(agent: Agent, query: str, show_reasoning: bool = False) -> None:
    """Process agent stream with prefixed output."""
    async for event in agent.stream_async(query):
        if "message" in event and isinstance(event["message"], dict):
            for item in event["message"].get("content", []):
                if "reasoningContent" in item and show_reasoning:
                    text = item["reasoningContent"]["reasoningText"]["text"]
                    print(f"\n🤔 Reasoning:\n{text}\n")
                elif "text" in item and item["text"].strip():
                    print(f"\n💬 Response:\n{item['text']}\n")
                elif "toolUse" in item:
                    print(f"\n🔧 Tool: {item['toolUse']['name']}")
                    print(f"\n🔧 Parameters:\n{item['toolUse']['input']}\n")
                elif "toolResult" in item:
                    content = item["toolResult"].get("content", [{}])[0].get("text", "")
                    status = item["toolResult"].get("status", "unknown")
                    print(f"\n⚙️ Result ({status}):\n\n{content}\n")

async def interactive_mode(agent: Agent, show_reasoning: bool = False) -> None:
    """Handle interactive mode."""
    print("\n🧬 CloudTrail SQL Agent 🧬 - Interactive Mode\nType 'exit' or 'quit' to end.\n")
    
    while True:
        try:
            query = input("\n> ").strip()
            if query.lower() in {"exit", "quit", "/quit", "bye"}:
                print("👋 Goodbye!")
                break
            elif query:
                await process_agent_stream(agent, query, show_reasoning)
                print("\n")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

def create_agent():
    """Create and return the CloudTrail agent."""
    model_id = os.getenv("STRANDS_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
    max_tokens = int(os.getenv("STRANDS_MAX_TOKENS", "4000"))
    temperature = float(os.getenv("STRANDS_TEMPERATURE", "1.0"))
    
    return Agent(
        model=BedrockModel(
            model_id=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            streaming=True,
            boto_client_config=Config(read_timeout=900, connect_timeout=900, retries={"max_attempts": 3})
        ),
        system_prompt=f"""You're a CloudTrail SQL assistant. Convert natural language to SQL queries.
        
        CRITICAL: NEVER change the table name. ALWAYS use exactly "awsdatacatalog"."{DATABASE_NAME}"."{TABLE_NAME}".
        DO NOT create date-specific table names like cloudtrail_logs_pp_2025_9_15.
        The table is partitioned by year, month, day columns - use WHERE clauses to filter dates.
        
        Always filter by year, month, day columns without quotes.
        Use CloudTrail-specific filters like eventname, eventsource, errorcode, username, sourceipaddress, awsregion.
        Use get_current_date for today/this month queries.
        Use get_table_schema to understand available columns before writing queries.
        
        IMPORTANT: After getting schema and analyzing user request, SELECT ONLY the specific columns needed to answer the question.
        Do NOT use SELECT * unless user explicitly asks for all data.
        Choose relevant columns based on what the user is asking for.
        
        Execute queries with run_athena_query.
        If query fails, use get_query_details with the query ID for error details.
        
        CloudTrail Query Guidelines:
        - For EC2 instances: eventname='RunInstances'
        - For S3 operations: eventsource='s3.amazonaws.com' or eventname IN ('GetObject', 'PutObject', 'DeleteObject', 'ListBucket')
        - For failed events: errorcode IS NOT NULL
        - For specific users: username='user@example.com'
        - For IP addresses: sourceipaddress='1.2.3.4'
        - For regions: awsregion='us-east-1'
        
        CORRECT: SELECT * FROM "awsdatacatalog"."{DATABASE_NAME}"."{TABLE_NAME}" WHERE year=2025 AND month=9 AND day=15;
        WRONG: SELECT * FROM "awsdatacatalog"."{DATABASE_NAME}"."cloudtrail_logs_pp_2025_9_15";
        """,
        tools=[get_current_date, get_table_schema, run_athena_query, get_query_details],
        callback_handler=None
    )

async def query_agent(agent: Agent, query: str) -> str:
    """Query the agent and return the complete response."""
    response_parts = []
    
    async for event in agent.stream_async(query):
        if "message" in event and isinstance(event["message"], dict):
            for item in event["message"].get("content", []):
                if "text" in item and item["text"].strip():
                    response_parts.append(item["text"])
    
    return "".join(response_parts)

def main() -> None:
    """Main entry point for CLI usage."""
    agent = create_agent()
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print("🚀 Starting CloudTrail SQL Agent...")
        response = asyncio.run(query_agent(agent, query))
        print(response)
    else:
        asyncio.run(interactive_mode(agent, False))

if __name__ == "__main__":
    main()
