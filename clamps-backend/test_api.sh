#!/bin/bash

# Define video paths - update these to your actual video paths
VIDEO1="./videos/1.mp4"
VIDEO2="./videos/2.mov"

echo "Upserting first video..."
curl -X POST http://localhost:5002/upsert \
  -H "Content-Type: application/json" \
  -d "{\"video_path\": \"$VIDEO1\"}"
echo -e "\n"

echo "Processing first video..."
curl -X POST http://localhost:5002/process \
  -H "Content-Type: application/json" \
  -d "{
    \"video_path\": \"$VIDEO1\",
    \"query\": \"Describe what is happening in this video\"
  }"
echo -e "\n"

echo "Upserting second video..."
curl -X POST http://localhost:5002/upsert \
  -H "Content-Type: application/json" \
  -d "{\"video_path\": \"$VIDEO2\"}"
echo -e "\n"


echo "Processing second video..."
curl -X POST http://localhost:5002/process \
  -H "Content-Type: application/json" \
  -d "{
    \"video_path\": \"$VIDEO2\",
    \"query\": \"Describe what is happening in this video\"
  }"
echo -e "\n"
