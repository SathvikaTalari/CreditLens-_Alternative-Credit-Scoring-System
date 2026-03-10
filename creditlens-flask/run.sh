#!/bin/bash
echo "============================================"
echo "   CreditLens Pro — Setup & Launch"
echo "   National AI/ML Hackathon 2026"
echo "============================================"
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q
echo "✅ Dependencies installed!"
echo ""
echo "🚀 Starting CreditLens Pro..."
echo "   Open your browser at: http://localhost:5000"
echo ""
python app.py