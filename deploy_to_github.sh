#!/bin/bash

# Replace 'YOUR_USERNAME' with your actual GitHub username
# Replace 'nba-clutch-analytics' with your actual repository name

# Add the remote repository
git remote add origin https://github.com/YOUR_USERNAME/nba-clutch-analytics.git

# Push the code to GitHub
git branch -M main
git push -u origin main

echo "Repository successfully pushed to GitHub!"
echo "Now you can deploy to Streamlit Community Cloud."
