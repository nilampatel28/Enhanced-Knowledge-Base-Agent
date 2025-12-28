# Amazon Bedrock AgentCore Deployment Guide

**Enhanced Knowledge Base Agent on AWS Bedrock AgentCore Runtime**

---

## Overview

This guide walks you through deploying the Enhanced Knowledge Base Agent to Amazon Bedrock AgentCore Runtime, a serverless runtime purpose-built for deploying and scaling dynamic AI agents.

### AgentCore Features
- ✅ Framework agnostic (Strands, LangGraph, CrewAI)
- ✅ Model flexibility (Bedrock, Claude, Gemini, OpenAI)
- ✅ Extended execution time (up to 8 hours)
- ✅ 100MB payload support (multi-modal)
- ✅ Session isolation
- ✅ Built-in authentication
- ✅ Agent-specific observability

---

## Prerequisites

### 1. AWS Account Setup
- [ ] AWS Account with appropriate permissions
- [ ] AWS CLI configured
- [ ] IAM permissions for Bedrock, ECR, CodeBuild, CloudWatch

### 2. Local Environment
- [ ] Python 3.12+
- [ ] Docker installed
- [ ] `uv` package manager installed
- [ ] Git configured

### 3. AWS Credentials
```bash
# Configure AWS credentials
aws configure

# Verify configuration
aws sts get-caller-identity
```

---

## Step 1: Create AgentCore Project Structure

### 1.1 Create Directory Structure

```bash
mkdir -p ~/workshop/agentcore/runtime
mkdir -p ~/workshop/agentcore/deployment
cd ~/workshop/agentcore
```

### 1.2 Copy Enhanced KB Agent to AgentCore

```bash
# Copy the enhanced_kb_agent package
cp -r /path/to/enhanced_kb_agent ~/workshop/agentcore/runtime/

# Copy tests
cp -r /path/to/tests ~/workshop/agentcore/runtime/

# Copy configuration files
cp /path/to/requirements.txt ~/workshop/agentcore/runtime/
cp /path/to/pytest.ini ~/workshop/agentcore/runtime/
```

---

## Step 2: Create AgentCore-Compatible Agent

### 2.1 Create `kb_agent_agentcore.py`

This file wraps the Enhanced KB Agent for AgentCore deployment:

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from enhanced_kb_agent.agent import EnhancedKnowledgeBaseAgent
from enhanced_kb_agent.config import KnowledgeBaseConfig
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AgentCore app
app = BedrockAgentCoreApp()

# Initialize the Enhanced KB Agent
config = KnowledgeBaseConfig()
kb_agent = EnhancedKnowledgeBaseAgent(config)

@app.entrypoint
async def invoke_agent(payload):
    """
    Main entry point for AgentCore runtime.
    
    Args:
        payload: Dictionary containing:
            - prompt: User query
            - context: Optional context
            - session_id: Optional session ID
    
    Returns:
        Agent response with results and metadata
    """
    try:
        # Extract parameters from payload
        prompt = payload.get("prompt")
        context = payload.get("context", {})
        session_id = payload.get("session_id")
        
        logger.info(f"Processing query: {prompt}")
        
        # Execute agent
        response = kb_agent.query(prompt)
        
        # Format response
        result = {
            "status": "success",
            "prompt": prompt,
            "response": response,
            "session_id": session_id,
            "metadata": {
                "model": "enhanced-kb-agent",
                "version": "1.0.0"
            }
        }
        
        logger.info(f"Query completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "prompt": prompt
        }

@app.entrypoint
async def invoke_agent_streaming(payload):
    """
    Streaming version of agent invocation.
    
    Args:
        payload: Dictionary containing prompt and optional context
    
    Yields:
        Streaming response events
    """
    try:
        prompt = payload.get("prompt")
        logger.info(f"Processing streaming query: {prompt}")
        
        # Stream response
        stream = kb_agent.stream(prompt)
        
        for event in stream:
            yield {
                "status": "streaming",
                "event": event,
                "prompt": prompt
            }
            
        logger.info(f"Streaming query completed")
        
    except Exception as e:
        logger.error(f"Error in streaming: {str(e)}")
        yield {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    app.run()
```

### 2.2 Create `requirements.txt` for AgentCore

```
strands-agents>=0.1.0
strands-agents-tools>=0.1.0
uv>=0.4.0
boto3>=1.26.0
bedrock-agentcore>=0.1.0
bedrock-agentcore-starter-toolkit>=0.1.0
flask>=2.3.0
pytest>=7.0.0
hypothesis>=6.0.0
```

---

## Step 3: Environment Setup

### 3.1 Install AgentCore Dependencies

```bash
cd ~/workshop/agentcore/runtime/

# Create requirements.txt
cat > requirements.txt << 'EOF'
strands-agents
strands-agents-tools
uv
boto3
bedrock-agentcore
bedrock-agentcore-starter-toolkit
flask
pytest
hypothesis
EOF

# Install dependencies
uv pip install -r requirements.txt
```

### 3.2 Verify Installation

```bash
# Verify bedrock-agentcore is installed
python3 -c "from bedrock_agentcore.runtime import BedrockAgentCoreApp; print('✅ AgentCore installed')"

# Verify enhanced_kb_agent is available
python3 -c "from enhanced_kb_agent.agent import EnhancedKnowledgeBaseAgent; print('✅ Enhanced KB Agent available')"
```

---

## Step 4: Local Testing (Optional)

### 4.1 Test Agent Locally

```bash
# Start the agent locally
uv run kb_agent_agentcore.py --port 8082
```

### 4.2 Test in Separate Terminal

```bash
# Test the /ping endpoint
curl http://localhost:8082/ping

# Test the agent
curl -X POST http://localhost:8082/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the Enhanced Knowledge Base Agent?"}'

# Stop the agent (Ctrl+C in first terminal)
```

---

## Step 5: Create Deployment Script

### 5.1 Create `deploy_to_agentcore.py`

```python
#!/usr/bin/env python3
"""
Deploy Enhanced Knowledge Base Agent to Amazon Bedrock AgentCore Runtime.
"""

import argparse
import logging
import os
from pathlib import Path
from bedrock_agentcore.runtime import BedrockAgentCoreRuntime

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
        logger.info(f"Deploying agent: {agent_name}")
        logger.info(f"Entry point: {entry_point}")
        logger.info(f"Region: {region}")
        
        # Initialize AgentCore runtime
        agentcore_runtime = BedrockAgentCoreRuntime(region=region)
        
        # Configure the agent
        logger.info("Configuring agent...")
        response = agentcore_runtime.configure(
            entrypoint=entry_point,
            auto_create_execution_role=True,
            auto_create_ecr=True,
            requirements_file=requirements_file,
            region=region,
            agent_name=agent_name
        )
        
        logger.info(f"Configuration response: {response}")
        
        # Launch the agent
        logger.info("Launching agent...")
        launch_result = agentcore_runtime.launch(
            local_build=local_build
        )
        
        logger.info(f"Launch successful!")
        logger.info(f"Agent ARN: {launch_result.get('agent_arn')}")
        logger.info(f"Agent ID: {launch_result.get('agent_id')}")
        
        # Print deployment information
        print("\n" + "="*80)
        print("DEPLOYMENT SUCCESSFUL")
        print("="*80)
        print(f"Agent Name: {agent_name}")
        print(f"Agent ARN: {launch_result.get('agent_arn')}")
        print(f"Agent ID: {launch_result.get('agent_id')}")
        print(f"Region: {region}")
        print("\nAgent logs available at:")
        print(f"  /aws/bedrock-agentcore/runtimes/{agent_name}")
        print("\nTail logs with:")
        print(f"  aws logs tail /aws/bedrock-agentcore/runtimes/{agent_name} --follow")
        print("="*80 + "\n")
        
        return launch_result
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description='Deploy Enhanced KB Agent to Bedrock AgentCore'
    )
    parser.add_argument(
        '--agent_name',
        default='enhanced-kb-agent',
        help='Name of the agent'
    )
    parser.add_argument(
        '--entry_point',
        default='kb_agent_agentcore.py',
        help='Entry point file'
    )
    parser.add_argument(
        '--requirements_file',
        default='requirements.txt',
        help='Requirements file'
    )
    parser.add_argument(
        '--local_build',
        action='store_true',
        help='Build container locally'
    )
    parser.add_argument(
        '--region',
        default='us-west-2',
        help='AWS region'
    )
    
    args = parser.parse_args()
    
    # Deploy
    deploy_agentcore(
        agent_name=args.agent_name,
        entry_point=args.entry_point,
        requirements_file=args.requirements_file,
        local_build=args.local_build,
        region=args.region
    )

if __name__ == '__main__':
    main()
```

---

## Step 6: Deploy to AgentCore

### 6.1 Deploy the Agent

```bash
cd ~/workshop/agentcore/runtime/

# Deploy with local build (faster on arm64)
uv run ~/workshop/agentcore/deploy_to_agentcore.py \
    --agent_name enhanced-kb-agent \
    --local_build \
    --entry_point kb_agent_agentcore.py \
    --region us-west-2
```

### 6.2 Monitor Deployment

```bash
# Watch the deployment progress
aws logs tail /aws/bedrock-agentcore/runtimes/enhanced-kb-agent --follow
```

---

## Step 7: Invoke the Deployed Agent

### 7.1 Create `invoke_agent.py`

```python
#!/usr/bin/env python3
"""
Invoke the deployed Enhanced KB Agent on Bedrock AgentCore.
"""

import argparse
import json
import logging
from bedrock_agentcore.runtime import BedrockAgentCoreRuntime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def invoke_agent(prompt: str, agent_name: str = 'enhanced-kb-agent', region: str = 'us-west-2'):
    """
    Invoke the deployed agent.
    
    Args:
        prompt: User query
        agent_name: Name of deployed agent
        region: AWS region
    """
    try:
        logger.info(f"Invoking agent: {agent_name}")
        logger.info(f"Prompt: {prompt}")
        
        # Initialize runtime
        runtime = BedrockAgentCoreRuntime(region=region)
        
        # Prepare payload
        payload = {
            "prompt": prompt,
            "context": {},
            "session_id": None
        }
        
        # Invoke agent
        response = runtime.invoke(
            agent_name=agent_name,
            payload=payload
        )
        
        logger.info("Agent response received")
        
        # Print response
        print("\n" + "="*80)
        print("AGENT RESPONSE")
        print("="*80)
        print(json.dumps(response, indent=2))
        print("="*80 + "\n")
        
        return response
        
    except Exception as e:
        logger.error(f"Invocation failed: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Invoke Enhanced KB Agent')
    parser.add_argument('--prompt', required=True, help='Query prompt')
    parser.add_argument('--agent_name', default='enhanced-kb-agent', help='Agent name')
    parser.add_argument('--region', default='us-west-2', help='AWS region')
    
    args = parser.parse_args()
    
    invoke_agent(
        prompt=args.prompt,
        agent_name=args.agent_name,
        region=args.region
    )

if __name__ == '__main__':
    main()
```

### 7.2 Invoke the Agent

```bash
cd ~/workshop/agentcore/runtime/

# Invoke with a query
uv run invoke_agent.py \
    --prompt "What is the Enhanced Knowledge Base Agent?" \
    --agent_name enhanced-kb-agent \
    --region us-west-2
```

---

## Step 8: Cleanup

### 8.1 Create `cleanup_agents.py`

```python
#!/usr/bin/env python3
"""
Clean up deployed AgentCore agents.
"""

import logging
from bedrock_agentcore.runtime import BedrockAgentCoreRuntime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_agents(region: str = 'us-west-2'):
    """
    Delete all deployed agents.
    
    Args:
        region: AWS region
    """
    try:
        logger.info(f"Cleaning up agents in region: {region}")
        
        runtime = BedrockAgentCoreRuntime(region=region)
        
        # List and delete agents
        agents = runtime.list_agents()
        
        for agent in agents:
            logger.info(f"Deleting agent: {agent['name']}")
            runtime.delete_agent(agent['name'])
            logger.info(f"Agent deleted: {agent['name']}")
        
        logger.info("Cleanup complete")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise

if __name__ == '__main__':
    cleanup_agents()
```

### 8.2 Run Cleanup

```bash
cd ~/workshop/agentcore/

# Clean up deployed agents
uv run cleanup_agents.py

# Remove configuration file
rm ~/workshop/agentcore/runtime/.bedrock_agentcore.yaml
```

---

## Troubleshooting

### Issue: "bedrock-agentcore not found"
```bash
# Reinstall dependencies
uv pip install --upgrade bedrock-agentcore bedrock-agentcore-starter-toolkit
```

### Issue: "AWS credentials not configured"
```bash
# Configure AWS credentials
aws configure

# Verify
aws sts get-caller-identity
```

### Issue: "Docker not found"
```bash
# Install Docker
# macOS: brew install docker
# Linux: sudo apt-get install docker.io
```

### Issue: "Permission denied"
```bash
# Check IAM permissions for:
# - bedrock:*
# - ecr:*
# - iam:*
# - codebuild:*
# - logs:*
```

---

## Monitoring and Logs

### View Agent Logs

```bash
# Tail logs in real-time
aws logs tail /aws/bedrock-agentcore/runtimes/enhanced-kb-agent --follow

# View recent logs
aws logs tail /aws/bedrock-agentcore/runtimes/enhanced-kb-agent --since 1h

# Get specific log stream
aws logs describe-log-streams \
    --log-group-name /aws/bedrock-agentcore/runtimes/enhanced-kb-agent
```

### View Agent Metrics

```bash
# Get agent status
aws bedrock-agentcore describe-agent \
    --agent-name enhanced-kb-agent \
    --region us-west-2

# List all agents
aws bedrock-agentcore list-agents --region us-west-2
```

---

## Configuration Files

### .bedrock_agentcore.yaml

This file is auto-generated and contains:
- Agent configuration
- AWS settings
- ECR repository details
- Execution role ARN
- Network configuration
- Observability settings

### Dockerfile

Auto-generated Dockerfile includes:
- Python 3.12 base image
- UV package manager
- AWS OpenTelemetry instrumentation
- Non-root user for security
- Port exposure (8080, 8000)

---

## Best Practices

1. **Security**
   - Use IAM roles with least privilege
   - Enable VPC endpoints for private access
   - Rotate credentials regularly

2. **Performance**
   - Use local builds for faster deployment
   - Monitor cold start times
   - Optimize payload sizes

3. **Monitoring**
   - Enable CloudWatch logs
   - Set up alarms for errors
   - Track invocation metrics

4. **Cost Optimization**
   - Use consumption-based pricing
   - Monitor execution time
   - Clean up unused agents

---

## Next Steps

1. ✅ Deploy agent to AgentCore
2. ✅ Test with sample queries
3. ✅ Monitor logs and metrics
4. ✅ Integrate with applications
5. ✅ Scale based on demand

---

**Created by:** Nilam Patel  
**Date:** December 27, 2025  
**Version:** 1.0.0

