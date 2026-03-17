# docs/project_goals.md


## General Goals

### High Level Goals
1. Create a program which is equally convenient/efficient for humans and agents
2. Create a GUI which is responsive to underlying state set by the CLI and GUI alike
3. Program is one of many Proof-Of-Concept Utilities using a new User-Context-DB made for Agent-Interop 

### Core Philosophy
1. Fully Client-Side, User Owned, User Controlled Data
2. Agent-Agnostic API
3. Module-Driven, Clean & DRY Coding Style

### User Experience (GUI)
1. Simple Interface with Keyboard-Driven Controls for Casual Users & Power-Users Alike
2. Fast & Responsive GUI with little to no Latency
3. Avoid using AI for anything other than completely necessary

### Program Details
This Program is a Video Ingest System with multiple Automated Workflow Steps
1. Download (using YT-DLP, with room for more methods in the future)
2. Transcribe (using WhisperAI, with room for more methods in the future)
3. Summarize (using Ollama, with room for other methods in the future)
4. Catalogue (using SQLite, with room for other methods in the future)


## Immediate Goals

### DAEMON
1. All functionality  runs independant of GUI
2. GUI is controlled by underlying state

### CLI
1. Create a terse API that Agents understand with the lowest token cost possible

### GUI
1. Create a solid, well organized project with room to expand
2. Create a clean, simple to use user interface
