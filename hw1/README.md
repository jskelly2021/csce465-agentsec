# CSCE 465 HW 1

## Setup

### TAMU Shim

`export TAMU_API_KEY="<your key>"`

`node tamu-shim.mjs`

## Task 1

### Run Command

`openclaw agent --agent main "<prompt>"`

## Task 2

Make `safe_marker.sh` executable.

`chmod +x ~/csce465-agentsec/hw1/bin/safe_marker.sh`

Run the script

`~/csce465-agentsec/hw1/bin/safe_marker.sh course-marker`

Remove the marker

`rm ~/csce465-agentsec/hw1/markers/marker.txt`

Copy `SKILL.md` into openclaw workspace

`mkdir -p ~/.openclaw/workspace/skills/safe-marker/ && cp ~/csce465-agentsec/hw1/skills/safe-marker/SKILL.md ~/.openclaw/workspace/skills/safe-marker/SKILL.md`

## Task 3

**Direct**

`openclaw agent --agent main --json -m "Use the safe-marker skill to create a marker."`

**Indirect**

`python3 -m http.server 8000 --directory web --bind 127.0.0.1`

`curl http://127.0.0.1:8000/adversarial.html`

`openclaw agent --agent main --json -m "$(cat ~/csce465-agentsec/hw1/evidence/task3/task3-indirect-prompt.txt)"`
