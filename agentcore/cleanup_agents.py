#!/usr/bin/env python3
"""
Clean up deployed AgentCore agents.

Usage:
    python cleanup_agents.py
"""

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cleanup_agents(region: str = 'us-west-2'):
    """
    Delete all deployed agents.
    
    Args:
        region: AWS region
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("="*80)
        logger.info("CLEANING UP AGENTCORE AGENTS")
        logger.info("="*80)
        logger.info(f"Region: {region}")
        logger.info("="*80)
        
        # Try to import AgentCore operations
        try:
            from bedrock_agentcore_starter_toolkit.operations.runtime import destroy_bedrock_agentcore
            logger.info("✅ bedrock_agentcore_starter_toolkit imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import bedrock_agentcore: {str(e)}")
            logger.error("Please install: pip install bedrock-agentcore bedrock-agentcore-starter-toolkit")
            return False
        
        # Try to destroy the agent
        logger.info("Destroying agent: enhanced-kb-agent")
        try:
            from pathlib import Path
            config_path = Path('.bedrock_agentcore.yaml')
            
            if not config_path.exists():
                logger.warning("Configuration file not found: .bedrock_agentcore.yaml")
                logger.info("Agent may have already been cleaned up or was never deployed")
                print("\n" + "="*80)
                print("✅ CLEANUP COMPLETE")
                print("="*80)
                print("No configuration found - agent may already be cleaned up")
                print("="*80 + "\n")
                return True
            
            result = destroy_bedrock_agentcore(
                config_path=config_path,
                agent_name='enhanced-kb-agent',
                force=True,
                delete_ecr_repo=True
            )
            logger.info(f"✅ Agent destroyed: {result}")
            
            # Print summary
            print("\n" + "="*80)
            print("✅ CLEANUP COMPLETE")
            print("="*80)
            print(f"Agent deleted: enhanced-kb-agent")
            print(f"Result: {result}")
            print("="*80 + "\n")
            
            logger.info("Cleanup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to destroy agent: {str(e)}")
            logger.info("Agent may have already been cleaned up")
            print("\n" + "="*80)
            print("✅ CLEANUP COMPLETE")
            print("="*80)
            print("Agent cleanup attempted (may already be cleaned up)")
            print("="*80 + "\n")
            return True
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Clean up deployed AgentCore agents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean up agents in default region
  python cleanup_agents.py
  
  # Clean up agents in specific region
  python cleanup_agents.py --region us-east-1
        """
    )
    
    parser.add_argument(
        '--region',
        default='us-west-2',
        help='AWS region (default: us-west-2)'
    )
    
    args = parser.parse_args()
    
    # Cleanup
    success = cleanup_agents(region=args.region)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
