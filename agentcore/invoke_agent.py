#!/usr/bin/env python3
"""
Invoke the deployed Enhanced KB Agent on Bedrock AgentCore.

Usage:
    python invoke_agent.py --prompt "What is the Enhanced Knowledge Base Agent?"
"""

import argparse
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def invoke_agent(
    prompt: str,
    agent_name: str = 'enhanced-kb-agent',
    region: str = 'us-west-2'
):
    """
    Invoke the deployed agent.
    
    Args:
        prompt: User query
        agent_name: Name of deployed agent
        region: AWS region
    
    Returns:
        Agent response
    """
    try:
        logger.info("="*80)
        logger.info("INVOKING BEDROCK AGENTCORE AGENT")
        logger.info("="*80)
        logger.info(f"Agent Name: {agent_name}")
        logger.info(f"Region: {region}")
        logger.info(f"Prompt: {prompt}")
        logger.info("="*80)
        
        # Try to import AgentCore
        try:
            from bedrock_agentcore.runtime import BedrockAgentCoreRuntime
            logger.info("✅ bedrock_agentcore imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import bedrock_agentcore: {str(e)}")
            logger.error("Please install: pip install bedrock-agentcore")
            return False
        
        # Initialize runtime
        logger.info("Initializing AgentCore runtime...")
        runtime = BedrockAgentCoreRuntime(region=region)
        logger.info("✅ Runtime initialized")
        
        # Prepare payload
        payload = {
            "prompt": prompt,
            "context": {},
            "session_id": None
        }
        
        # Invoke agent
        logger.info("Invoking agent...")
        response = runtime.invoke(
            agent_name=agent_name,
            payload=payload
        )
        logger.info("✅ Agent response received")
        
        # Print response
        print("\n" + "="*80)
        print("✅ AGENT RESPONSE")
        print("="*80)
        print(json.dumps(response, indent=2))
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Invocation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Invoke Enhanced KB Agent on Bedrock AgentCore',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic invocation
  python invoke_agent.py --prompt "What is the Enhanced Knowledge Base Agent?"
  
  # Invoke specific agent
  python invoke_agent.py --prompt "Tell me about AI" --agent_name my-agent
  
  # Invoke in specific region
  python invoke_agent.py --prompt "Hello" --region us-east-1
        """
    )
    
    parser.add_argument(
        '--prompt',
        required=True,
        help='Query prompt'
    )
    parser.add_argument(
        '--agent_name',
        default='enhanced-kb-agent',
        help='Agent name (default: enhanced-kb-agent)'
    )
    parser.add_argument(
        '--region',
        default='us-west-2',
        help='AWS region (default: us-west-2)'
    )
    
    args = parser.parse_args()
    
    # Invoke
    success = invoke_agent(
        prompt=args.prompt,
        agent_name=args.agent_name,
        region=args.region
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
