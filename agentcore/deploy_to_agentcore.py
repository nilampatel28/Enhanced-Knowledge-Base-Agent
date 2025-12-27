#!/usr/bin/env python3
"""
Deploy Enhanced Knowledge Base Agent to Amazon Bedrock AgentCore Runtime.

Usage:
    python deploy_to_agentcore.py --agent_name enhanced-kb-agent --local_build
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def deploy_agentcore(
    agent_name: str,
    entry_point: str,
    requirements_file: str = 'requirements.txt',
    local_build: bool = False,
    region: str = 'us-west-2'
):
    """
    Deploy an Amazon Bedrock AgentCore runtime.
    
    Args:
        agent_name: Name of the agent
        entry_point: Path to entry point file
        requirements_file: Path to requirements.txt
        local_build: Whether to build locally
        region: AWS region
    """
    try:
        logger.info("="*80)
        logger.info("BEDROCK AGENTCORE DEPLOYMENT")
        logger.info("="*80)
        logger.info(f"Agent Name: {agent_name}")
        logger.info(f"Entry Point: {entry_point}")
        logger.info(f"Requirements: {requirements_file}")
        logger.info(f"Local Build: {local_build}")
        logger.info(f"Region: {region}")
        logger.info("="*80)
        
        # Try to import AgentCore operations
        try:
            from bedrock_agentcore_starter_toolkit.operations.runtime import (
                configure_bedrock_agentcore,
                launch_bedrock_agentcore
            )
            logger.info("✅ bedrock_agentcore_starter_toolkit imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import bedrock_agentcore: {str(e)}")
            logger.error("Please install: pip install bedrock-agentcore bedrock-agentcore-starter-toolkit")
            return False
        
        # Verify entry point exists
        if not os.path.exists(entry_point):
            logger.error(f"❌ Entry point not found: {entry_point}")
            return False
        logger.info(f"✅ Entry point found: {entry_point}")
        
        # Verify requirements file exists
        if not os.path.exists(requirements_file):
            logger.error(f"❌ Requirements file not found: {requirements_file}")
            return False
        logger.info(f"✅ Requirements file found: {requirements_file}")
        
        # Configure the agent
        logger.info("Configuring agent...")
        from pathlib import Path
        config_result = configure_bedrock_agentcore(
            agent_name=agent_name,
            entrypoint_path=Path(entry_point),
            requirements_file=requirements_file,
            region=region,
            non_interactive=True,
            auto_create_execution_role=True,
            auto_create_ecr=True
        )
        logger.info("✅ Agent configured")
        logger.info(f"   Config: {config_result}")
        
        # Launch the agent
        logger.info("Launching agent...")
        config_path = Path('.bedrock_agentcore.yaml')
        launch_result = launch_bedrock_agentcore(
            config_path=config_path,
            agent_name=agent_name,
            local=local_build,
            use_codebuild=not local_build
        )
        logger.info("✅ Agent launched successfully")
        
        # Print deployment information
        print("\n" + "="*80)
        print("✅ DEPLOYMENT SUCCESSFUL")
        print("="*80)
        print(f"Agent Name: {agent_name}")
        print(f"Launch Result: {launch_result}")
        print(f"Region: {region}")
        print("\n📊 Agent logs available at:")
        print(f"  /aws/bedrock-agentcore/runtimes/{agent_name}")
        print("\n📝 Tail logs with:")
        print(f"  aws logs tail /aws/bedrock-agentcore/runtimes/{agent_name} --follow")
        print("\n📝 Or view recent logs:")
        print(f"  aws logs tail /aws/bedrock-agentcore/runtimes/{agent_name} --since 1h")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Deploy Enhanced KB Agent to Bedrock AgentCore',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy with local build (faster on arm64)
  python deploy_to_agentcore.py --agent_name enhanced-kb-agent --local_build
  
  # Deploy with CodeBuild (default, slower but works on x86)
  python deploy_to_agentcore.py --agent_name enhanced-kb-agent
  
  # Deploy to specific region
  python deploy_to_agentcore.py --agent_name enhanced-kb-agent --region us-east-1
        """
    )
    
    parser.add_argument(
        '--agent_name',
        default='enhanced-kb-agent',
        help='Name of the agent (default: enhanced-kb-agent)'
    )
    parser.add_argument(
        '--entry_point',
        default='agentcore/runtime/kb_agent_agentcore.py',
        help='Entry point file (default: agentcore/runtime/kb_agent_agentcore.py)'
    )
    parser.add_argument(
        '--requirements_file',
        default='agentcore/runtime/requirements.txt',
        help='Requirements file (default: agentcore/runtime/requirements.txt)'
    )
    parser.add_argument(
        '--local_build',
        action='store_true',
        help='Build container locally (faster on arm64, not available on x86)'
    )
    parser.add_argument(
        '--region',
        default='us-west-2',
        help='AWS region (default: us-west-2)'
    )
    
    args = parser.parse_args()
    
    # Deploy
    success = deploy_agentcore(
        agent_name=args.agent_name,
        entry_point=args.entry_point,
        requirements_file=args.requirements_file,
        local_build=args.local_build,
        region=args.region
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
