# NetWeave
*An AI-Powered City Planning and Traffic Simulation Platform*

## Progress:
Basic Frontend 2-pane canvas interface is ready, modal pipeine for I2I generation is ready but the modal itself needs more training on better data + better validation. Nothing else exists as of yet.

## Overview
NetWeave is an experimental simulation platform that bridges generative AI with traffic and city-planning simulations. Inspired by tools like NVIDIA Canvas and Cities: Skylines, NetWeave allows users to sketch semantic "road networks" and automatically converts them into realistic city maps—complete with buildings and properties. The platform then feeds this synthesized map into a cellular automata–based traffic simulator or agent-based simulator.

## Highlights
- Generative AI + ControlNet for transforming user sketches into realistic map imagery
- OSMnx for road-network retrieval and property generation (buildings, roads, intersections, etc.)
- Graph-based simulation for traffic flow analysis and agent-based movement
- Go & Python interplay for performance and flexibility

## Project Motivation
Modern city-building games and real-world urban planning often rely on extensive manual modeling. NetWeave showcases how to automate much of that design through a three-step process:

1. User Sketch → Semantic Road Layers
   - Different road types, lane counts, roundabouts, traffic signals, etc.

2. Deep Learning Transformation
   - A trained ControlNet model transforms the "semantic sketch" into a richly detailed, stylized map

3. Graph Extraction & Simulation
   - We use the resulting map to extract a road network (nodes & edges) and simulate traffic or agent flow

## Key Features

### Sketch-to-City Conversion
Users can draw color-coded lines to indicate road hierarchies, speed limits, and directions. NetWeave's ControlNet integration transforms these lines into a realistic top-down city map.

### Dynamic Road & Building Generation
The system leverages OSMnx to fetch real-world building footprint styles or add synthetic buildings in random distributions. It includes intersection detection, roundabout flags, and property generation on roads.

### Simulation Capabilities
The platform supports two simulation approaches:
- Cellular Automata simulation using Nagel–Schreckenberg or custom CA rules to simulate traffic flows
- Agent-based simulation with start/end points among the generated properties (residential, commercial, industrial)

### Modular Architecture
- Python handles the deep learning (GAN/ControlNet) and road-network data generation
- Go (with frameworks like Gin) serves the final application and manages concurrency for real-time or batch simulations

### Scalability
The system allows generating multiple bounding boxes, caching OSM data, or using local .pbf files for massive coverage.

## Architecture Overview
```
┌─────────────┐        ┌────────────────────┐        ┌───────────────┐
│ User Sketch  │  --->  │  ControlNet Module │  --->  │  Generated Map│
└─────────────┘        └────────────────────┘        └───────────────┘
           (1)                  (2)                            (3)
                         (Python, PyTorch)

┌──────────────────────────────┐
│  Road Network Extraction     │ <--- OSMnx + Shapely
└──────────────────────────────┘
           (4)

┌──────────────────────────────┐
│ Simulation (Go + CA Model)   │ <--- Graph-based traffic or agent-based movement
└──────────────────────────────┘
           (5)
```

## How It Works

### Data Generation
- Python script with OSMnx gathers training pairs:
  - Control (semantic sketches)
  - Target (realistic styled maps)
- These pairs train a specialized ControlNet model

### User Interaction
- Users draw or upload semantic road sketches
- ControlNet inference service transforms sketches into styled maps

### Graph Extraction
- Skeletonization or direct bounding box approach extracts roads, intersections, and building data
- Produces a final road graph for simulation

### Traffic Simulation
- Go-based cellular automata or agent-based model simulates movement
- Results visualized for analysis (e.g., congestion hotspots)
## !TODO
## Getting Started

### Prerequisites
- Python 3.9+
- Go 1.19+

### Installation
```bash
git clone https://github.com/username/netweave.git
pip install -r requirements.txt
go mod tidy
```

### Setup Steps
1. Train or Load ControlNet
   ```bash
   # Using pretrained weights
   # Place in trained_model/controlnet/
   
   # Or train new model
   python train_controlnet.py --dataset my_map_dataset
   ```

2. Generate Data
   ```bash
   python ds.py --output-dir my_data --samples 5 --size 512
   ```

3. Run the Application
   ```bash
   # Start Python Inference Server
   python inference_server.py
   
   # Start Go Simulation Server
   go run main.go
   ```

Access the UI at http://localhost:8080 to begin creating your city networks.
