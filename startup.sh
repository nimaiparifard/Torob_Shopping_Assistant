#!/bin/bash

# Torob AI Assistant - Complete Startup Script
# This script runs all necessary steps to prepare and start the application

set -e  # Exit on any error

echo "🚀 Starting Torob AI Assistant setup..."

# Step 1: Download and extract data
echo "📥 Step 1: Downloading and extracting data..."
python export_project.py

# Step 2: Create database schema
echo "🗄️ Step 2: Creating database schema..."
python db/create_db.py

# Step 3: Load data into database
echo "📊 Step 3: Loading data into database..."
python db/load_db.py

# Step 4: Start the API server
echo "🌐 Step 4: Starting API server..."
python run_api.py
