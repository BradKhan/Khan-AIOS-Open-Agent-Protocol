#!/usr/bin/env bash

set -e

mkdir -p ../ai-upstreams
cd ../ai-upstreams

git clone https://github.com/BradKhan/agents.md.git || true
git clone https://github.com/BradKhan/open-skills.git || true
git clone https://github.com/BradKhan/gemini-cli.git || true
git clone https://github.com/BradKhan/qwen-code.git || true
git clone https://github.com/BradKhan/trae-agent.git || true

echo "Upstream repositories cloned into ../ai-upstreams"
echo "Reference or fork as needed per project."
