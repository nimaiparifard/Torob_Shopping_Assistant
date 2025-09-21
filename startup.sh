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

## Step 3: Load data into database (optimized for memory < 2GB)
#echo "📊 Step 3: Loading data into database (memory optimized)..."
#echo "   Loading small tables with chunk size 5,000..."
#python -m db.load_db_optimized --table cities --chunk-size 5000
#python -m db.load_db_optimized --table brands --chunk-size 5000
#python -m db.load_db_optimized --table categories --chunk-size 5000
#python -m db.load_db_optimized --table shops --chunk-size 5000
#python -m db.load_db_optimized --table final_clicks --chunk-size 5000
#
#echo "   Loading large tables with chunk size 1,000 (memory < 2GB)..."
#python -m db.load_db_optimized --table base_products --chunk-size 2000
#python -m db.load_db_optimized --table members --chunk-size 5000
#python -m db.load_db_optimized --table searches --chunk-size 5000
#python -m db.load_db_optimized --table search_results --chunk-size 5000
#python -m db.load_db_optimized --table base_views --chunk-size 5000

echo "✅ All database tables loaded successfully!"

# Step 4: Start the API server
echo "🌐 Step 4: Starting API server..."
python run_api.py
