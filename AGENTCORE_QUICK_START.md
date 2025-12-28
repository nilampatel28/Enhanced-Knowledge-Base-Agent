# AgentCore Agent - Quick Start Guide

**Created by:** Nilam Patel

---

## 🚀 Quick Commands

### Test Locally

```bash
# Start the agent locally
python3 agentcore/runtime/kb_agent_agentcore.py --port 8082

# In another terminal, test it
curl http://localhost:8082/ping

# Query the agent
curl -X POST http://localhost:8082/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the Enhanced Knowledge Base Agent?"}'
```

### Deploy to AgentCore

```bash
# Deploy to workshop account
uv run agentcore/deploy_to_agentcore.py \
    --agent_name enhanced-kb-agent \
    --local_build \
    --region us-west-2
```

### Invoke Deployed Agent

```bash
# Query the deployed agent
uv run agentcore/invoke_agent.py \
    --prompt "Your question here" \
    --agent_name enhanced-kb-agent \
    --region us-west-2
```

### Monitor Logs

```bash
# Watch logs in real-time
aws logs tail /aws/bedrock-agentcore/runtimes/enhanced-kb-agent --follow

# View last hour of logs
aws logs tail /aws/bedrock-agentcore/runtimes/enhanced-kb-agent --since 1h
```

### Cleanup

```bash
# Delete the deployed agent
uv run agentcore/cleanup_agents.py --region us-west-2
```

---

## 📊 Example Queries

```bash
# Query 1: Simple question
curl -X POST http://localhost:8082/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is machine learning?"}'

# Query 2: Complex question
curl -X POST http://localhost:8082/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain the difference between supervised and unsupervised learning"}'

# Query 3: With context
curl -X POST http://localhost:8082/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the main features?",
    "context": {"domain": "machine learning"}
  }'
```

---

## 🔍 Response Format

```json
{
  "status": "success",
  "data": {
    "original_query": "Your question",
    "answer": "The agent's response",
    "sources": ["source1", "source2"],
    "confidence": 0.95,
    "reasoning_steps": [
      {
        "step_number": 0,
        "query": {...},
        "results": [...],
        "execution_time_ms": 123.45,
        "success": true
      }
    ],
    "conflicts_detected": []
  },
  "prompt": "Your question",
  "session_id": null,
  "metadata": {
    "model": "enhanced-kb-agent",
    "version": "1.0.0",
    "framework": "strands-agents"
  }
}
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# AWS Configuration
export AWS_DEFAULT_REGION=us-west-2
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_SESSION_TOKEN=your_token  # For temporary credentials

# Agent Configuration
export AGENT_NAME=enhanced-kb-agent
export AGENT_PORT=8082
```

### Local Testing

```bash
# Start with custom port
python3 agentcore/runtime/kb_agent_agentcore.py --port 9000

# Force local mode (skip AgentCore)
python3 agentcore/runtime/kb_agent_agentcore.py --port 8082 --local
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | `lsof -i :8082` then `kill -9 <PID>` |
| Module not found | `uv pip install -r agentcore/runtime/requirements.txt` |
| AWS credentials error | `aws sts get-caller-identity` to verify |
| Agent not responding | Check logs: `aws logs tail /aws/bedrock-agentcore/runtimes/enhanced-kb-agent` |
| JSON serialization error | Ensure custom encoder is used (already fixed) |

---

## 📁 File Structure

```
agentcore/
├── runtime/
│   ├── kb_agent_agentcore.py          # Main agent wrapper
│   ├── requirements.txt                # Dependencies
│   └── .bedrock_agentcore.yaml        # Config (auto-generated)
├── deploy_to_agentcore.py             # Deployment script
├── invoke_agent.py                     # Invocation script
└── cleanup_agents.py                   # Cleanup script
```

---

## 📚 Documentation

- **Full Guide:** `AGENTCORE_DEPLOYMENT_GUIDE.md`
- **Step-by-Step:** `AGENTCORE_DEPLOYMENT_STEPS.md`
- **Technical Details:** `TECHNICAL_DOCUMENTATION.md`
- **Deployment Status:** `AGENTCORE_DEPLOYMENT_COMPLETE.md`

---

## ✅ Verification Checklist

- [ ] AWS credentials configured (`aws sts get-caller-identity`)
- [ ] Dependencies installed (`uv pip install -r agentcore/runtime/requirements.txt`)
- [ ] Local testing works (`curl http://localhost:8082/ping`)
- [ ] Agent responds to queries
- [ ] Logs are accessible (`aws logs tail /aws/bedrock-agentcore/runtimes/enhanced-kb-agent`)

---

**Created by:** Nilam Patel  
**Date:** December 27, 2025  
**Status:** ✅ Ready for Production
