#!/bin/bash
echo "========================================="
echo "       UNICAFE - Campus Food Portal"
echo "========================================="
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install flask flask-cors bcrypt --quiet --break-system-packages 2>/dev/null || pip install flask flask-cors bcrypt --quiet

echo ""
echo "Starting UNICAFE server..."
echo ""
echo "========================================="
echo " Open your browser at: http://localhost:5000"
echo ""
echo " Demo Accounts:"
echo " Red Cafe Owner:  redcafe@unicafe.com / redcafe123"
echo " Blue Cafe Owner: bluecafe@unicafe.com / bluecafe123"
echo " (Sign up as Student or Delivery Boy)"
echo "========================================="
echo ""

python3 app.py
