# 🚀 Run the UI Now - Step by Step

## ⚠️ You Got a 403 Error

This means the server wasn't running. Let's fix it!

---

## ✅ Solution: Start the Server Properly

### **Option 1: Using Python Directly (Recommended)**

Open a terminal and run:

```bash
python enhanced_kb_agent/web/server.py --host 127.0.0.1 --port 5000 --debug
```

**Expected Output:**
```
Starting Enhanced Knowledge Base Agent Web Server
Access the web UI at http://localhost:5000
API endpoints available at http://localhost:5000/api
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### **Option 2: Using the Startup Script**

```bash
chmod +x start_ui.sh
./start_ui.sh
```

### **Option 3: Using Flask Directly**

```bash
export FLASK_APP=enhanced_kb_agent/web/server.py
export FLASK_ENV=development
flask run --host=127.0.0.1 --port=5000
```

---

## 🌐 Access the UI

Once you see the "Running on" message, open your browser:

```
http://localhost:5000
```

---

## ✅ Verification Checklist

Before starting, verify:

- [ ] You're in the project root directory
- [ ] Python 3.8+ is installed: `python --version`
- [ ] Dependencies are installed: `pip install -r requirements.txt`
- [ ] Port 5000 is available: `lsof -i :5000`
- [ ] You have read/write permissions

---

## 🐛 Troubleshooting

### Issue: "Module not found"
```bash
pip install -r requirements.txt
```

### Issue: "Port 5000 already in use"
```bash
# Use a different port
python enhanced_kb_agent/web/server.py --host 127.0.0.1 --port 8000
# Then access: http://localhost:8000
```

### Issue: "Permission denied"
```bash
chmod +x start_ui.sh
```

### Issue: "Connection refused"
- Make sure the server is running
- Check the terminal for error messages
- Try a different port

---

## 📋 What to Do After Starting

1. **Wait for the server to start** (should say "Running on...")
2. **Open browser** to http://localhost:5000
3. **You should see** the Enhanced Knowledge Base Agent UI
4. **Explore** the 5 tabs:
   - Query
   - Store
   - Search
   - Organize
   - Info

---

## 🎯 Quick Test

Once the UI loads:

1. Click **Store** tab
2. Enter: "Python is a programming language"
3. Title: "Python"
4. Click **Store Content**
5. You should see a success message ✅

---

## 📞 Still Having Issues?

### Check These:

1. **Is the server running?**
   ```bash
   curl http://localhost:5000/api/health
   ```
   Should return: `{"status": "ok"}`

2. **Are dependencies installed?**
   ```bash
   pip list | grep flask
   ```
   Should show Flask version

3. **Is the port available?**
   ```bash
   lsof -i :5000
   ```
   Should be empty or show only your server

4. **Check the logs**
   Look at the terminal where you started the server for error messages

---

## 🎊 Success!

Once you see the UI, you're all set! 

**Enjoy exploring the Enhanced Knowledge Base Agent!** 🚀

---

## 📚 Next Steps

1. Store some information
2. Execute queries
3. Search your knowledge base
4. Organize with categories and tags
5. Monitor with the Info tab

---

**Status**: ✅ Ready to Run  
**Version**: 1.0.0  
**Last Updated**: December 27, 2025
