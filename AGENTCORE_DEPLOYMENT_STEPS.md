# Step-by-Step: Deploy Enhanced KB Agent to Bedrock AgentCore

**Complete execution guide with all commands**

---

## Prerequisites Checklist

Before starting, verify you have:

```bash
# Check Python version (need 3.12+)
python3 --version

# Check AWS CLI
aws --version

# Check Docker
docker --version

# Check uv package manager
uv --version

# Verify AWS credentials
aws sts get-caller-identity
```

If any are missing, install them first.

---

## Step 1: Setup Directory Structure

```bash
# Create agentcore directory structure
mkdir -p ~/workshop/agentcore/runtime
mkdir -p ~/workshop/agentcore/deployment

# Navigate to agentcore directory
cd ~/workshop/agentcore

# Verify structure
ls -la
```

Expected output:
```
drwxr-xr-x  runtime/
drwxr-xr-x  deployment/
```

---

## Step 2: Copy Enhanced KB Agent Files

```bash
# Copy the enhanced_kb_agent package
cp -r /path/to/enhanced_kb_agent ~/workshop/agentcore/runtime/

# Copy tests
cp -r /path/to/tests ~/workshop/agentcore/runtime/

# Copy configuration files
cp /path/to/requirements.txt ~/workshop/agentcore/runtime/base_requirements.txt
cp /path/to/pytest.ini ~/workshop/agentcore/runtime/

# Verify files
ls -la ~/workshop/agentcore/runtime/
```

Expected files:
```
enhanced_kb_agent/
tests/
kb_agent_agentcore.py
requirements.txt
pytest.ini
```

---

## Step 3: Install AgentCore Dependencies

```bash
# Navigate to runtime directory
cd ~/workshop/agentcore/runtime/

# Create requirements.txt for AgentCore
cat > requirements.txt << 'EOF'
strands-agents>=0.1.0
strands-agents-tools>=0.1.0
uv>=0.4.0
boto3>=1.26.0
bedrock-agentcore>=0.1.0
bedrock-agentcore-starter-toolkit>=0.1.0
flask>=2.3.0
pytest>=7.0.0
hypothesis>=6.0.0
EOF

# Install dependencies
uv pip install -r requirements.txt

# Verify installation
python3 -c "from bedrock_agentcore.runtime import BedrockAgentCoreApp; print('✅ AgentCore installed')"
python3 -c "from enhanced_kb_agent.agent import EnhancedKnowledgeBaseAgent; print('✅ Enhanced KB Agent available')"
```

Expected output:
```
✅ AgentCore installed
✅ Enhanced KB Agent available
```

---

## Step 4: Test Agent Locally (Optional)

```bash
# Navigate to runtime directory
cd ~/workshop/agentcore/runtime/

# Start the agent locally
uv run kb_agent_agentcore.py --port 8082

# Output should show:
# Starting local Flask server on port 8082...
```

In a separate terminal:

```bash
# Test the /ping endpoint
curl http://localhost:8082/ping

# Expected output:
# {"status":"Healthy"}

# Test the agent
curl -X POST http://localhost:8082/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the Enhanced Knowledge Base Agent?"}'

# Expected output:
# {"status":"success","data":{...},"prompt":"What is...","session_id":null,"metadata":{...}}
```

Back in first terminal:

```bash
# Stop the agent
Ctrl+C
```

---

## Step 5: Deploy to AgentCore

```bash
# Navigate to agentcore directory
cd ~/workshop/agentcore/

# Make deployment script executable
chmod +x deploy_to_agentcore.py

# Deploy with local build (faster on arm64)
uv run deploy_to_agentcore.py \
    --agent_name enhanced-kb-agent \
    --local_build \
    --entry_point agentcore/runtime/kb_agent_agentcore.py \
    --region us-west-2

# Expected output:
# ================================================================================
# ✅ DEPLOYMENT SUCCESSFUL
# ================================================================================
# Agent Name: enhanced-kb-agent
# Agent ARN: arn:aws:bedrock-agentcore:us-west-2:<account-id>:runtime/enhanced-kb-agent-xxxxx
# Agent ID: enhanced-kb-agent-xxxxx
# Region: us-west-2
# ...
```

**Note:** If you're on x86 architecture, remove `--local_build` flag:
```bash
uv run deploy_to_agentcore.py \
    --agent_name enhanced-kb-agent \
    --entry_point agentcore/runtime/kb_agent_agentcore.py \
    --region us-west-2
```

---

## Step 6: Monitor Deployment

```bash
# In a separate terminal, watch the deployment logs
aws logs tail /aws/bedrock-agentcore/runtimes/enhanced-kb-agent --follow

# Or view recent logs
aws logs tail /aws/bedrock-agentcore/runtimes/enhanced-kb-agent --since 1h

# List all log streams
aws logs describe-log-streams \
    --log-group-name /aws/bedrock-agentcore/runtimes/enhanced-kb-agent
```

---

## Step 7: Invoke the Deployed Agent

```bash
# Navigate to agentcore directory
cd ~/workshop/agentcore/

# Make invocation script executable
chmod +x invoke_agent.py

# Invoke with a query
uv run invoke_agent.py \
    --prompt "What is the Enhanced Knowledge Base Agent?" \
    --agent_name enhanced-kb-agent \
    --region us-west-2

# Expected output:
# ================================================================================
# ✅ AGENT RESPONSE
# ================================================================================
# {
#   "status": "success",
#   "data": {...},
#   "prompt": "What is the Enhanced Knowledge Base Agent?",
#   "session_id": null,
#   "metadata": {...}
# }
# ================================================================================
```

Try more queries:

```bash
# Query 1: About the system
uv run invoke_agent.py \
    --prompt "Describe the Enhanced Knowledge Base Agent architecture"

# Query 2: About features
uv run invoke_agent.py \
    --prompt "What are the main features of this system?"

# Query 3: About deployment
uv run invoke_agent.py \
    --prompt "How is this agent deployed on AWS?"
```

---

## Step 8: View Agent Metrics

```bash
# Get agent status
aws bedrock-agentcore describe-agent \
    --agent-name enhanced-kb-agent \
    --region us-west-2

# List all agents
aws bedrock-agentcore list-agents --region us-west-2

# Get CloudWatch metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/BedrockAgentCore \
    --metric-name Invocations \
    --dimensions Name=AgentName,Value=enhanced-kb-agent \
    --start-time 2025-01-01T00:00:00Z \
    --end-time 2025-01-02T00:00:00Z \
    --period 3600 \
    --statistics Sum
```

---

## Step 9: View Generated Configuration

```bash
# View the auto-generated .bedrock_agentcore.yaml
cat ~/workshop/agentcore/runtime/.bedrock_agentcore.yaml

# View the auto-generated Dockerfile
cat ~/workshop/agentcore/runtime/Dockerfile | sed '/^$/N;/^\n$/D'

# View the auto-generated .dockerignore
cat ~/workshop/agentcore/runtime/.dockerignore
```

---

## Step 10: Cleanup (When Done)

```bash
# Navigate to agentcore directory
cd ~/workshop/agentcore/

# Make cleanup script executable
chmod +x cleanup_agents.py

# Delete all deployed agents
uv run cleanup_agents.py --region us-west-2

# Expected output:
# ================================================================================
# ✅ CLEANUP COMPLETE
# ================================================================================
# Agents deleted: 1/1
# ================================================================================

# Remove configuration file
rm ~/workshop/agentcore/runtime/.bedrock_agentcore.yaml
```

---

## Troubleshooting

### Issue 1: "bedrock-agentcore not found"

```bash
# Solution: Install bedrock-agentcore
uv pip install --upgrade bedrock-agentcore bedrock-agentcore-starter-toolkit

# Verify
python3 -c "from bedrock_agentcore.runtime import BedrockAgentCoreApp; print('OK')"
```

### Issue 2: "AWS credentials not configured"

```bash
# Solution: Configure AWS credentials
aws configure

# Verify
aws sts get-caller-identity

# Should output your AWS account ID
```

### Issue 3: "Permission denied"

```bash
# Solution: Check IAM permissions
# You need permissions for:
# - bedrock:*
# - ecr:*
# - iam:*
# - codebuild:*
# - logs:*

# Check current permissions
aws iam get-user
```

### Issue 4: "Docker not found"

```bash
# Solution: Install Docker
# macOS:
brew install docker

# Linux:
sudo apt-get install docker.io

# Verify
docker --version
```

### Issue 5: "Port 8082 already in use"

```bash
# Solution: Use different port
uv run kb_agent_agentcore.py --port 8083

# Or kill process using port 8082
lsof -i :8082
kill -9 <PID>
```

---

## Complete Workflow Summary

```bash
# 1. Setup
mkdir -p ~/workshop/agentcore/runtime
cd ~/workshop/agentcore/runtime/

# 2. Install dependencies
uv pip install -r requirements.txt

# 3. Test locally (optional)
uv run kb_agent_agentcore.py --port 8082
# In another terminal: curl http://localhost:8082/ping

# 4. Deploy
cd ~/workshop/agentcore/
uv run deploy_to_agentcore.py --agent_name enhanced-kb-agent --local_build

# 5. Invoke
uv run invoke_agent.py --prompt "Your query here"

# 6. Monitor
aws logs tail /aws/bedrock-agentcore/runtimes/enhanced-kb-agent --follow

# 7. Cleanup
uv run cleanup_agents.py
```

---

## Success Indicators

✅ **Deployment Successful When:**
- Deployment script completes without errors
- Agent ARN is displayed
- Agent appears in `aws bedrock-agentcore list-agents`
- Logs are available in CloudWatch

✅ **Invocation Successful When:**
- Response contains "status": "success"
- Response includes agent output
- No errors in CloudWatch logs

✅ **Cleanup Successful When:**
- Cleanup script completes without errors
- Agent no longer appears in `aws bedrock-agentcore list-agents`
- Configuration file is removed

---

## Next Steps

1. ✅ Deploy agent to AgentCore
2. ✅ Test with sample queries
3. ✅ Monitor logs and metrics
4. ✅ Integrate with applications
5. ✅ Scale based on demand
6. ✅ Set up alarms and monitoring
7. ✅ Implement authentication
8. ✅ Enable response streaming

---

## Additional Resources

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Strands Agents Documentation](https://docs.strands.ai/)
- [AWS CLI Reference](https://docs.aws.amazon.com/cli/)
- [CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/)

---

**Created by:** Nilam Patel  
**Date:** December 27, 2025  
**Version:** 1.0.0

