NetWeave
(O3 Whitepaper for now sorry)
The core goal is to provide users the ability to create "cities' with similar control over just road networks as you see in Cities Skylines 2 through a semantic color interface, 
in which the gaps can be filled then through our ControlNet + StableDiffusion 1.5 Image2Image Modal, creating a more understandable map visualization and generating building footprints that can be used to create more realisitic and agentic CA routes and simulations.
The generated render view will then be processed and generated into a graph on which a cellular automata powered GOL-like algorithm will simulate traffic and relay results to the user through both data and visual representations on the render view.

NetWeave is an experimental simulation platform that bridges generative AI with traffic and city-planning simulations. Inspired by tools like NVIDIA Canvas and Cities: Skylines, NetWeave allows users to sketch semantic “road networks” and automatically converts them into realistic city maps—complete with buildings and properties. The platform then feeds this synthesized map into a cellular automata–based traffic simulator or agent-based simulator.

	Highlights
	•	Generative AI + ControlNet for transforming user sketches into realistic map imagery.
	•	OSMnx for road-network retrieval and property generation (buildings, roads, intersections, etc.).
	•	Graph-based simulation for traffic flow analysis and agent-based movement.
	•	Go & Python interplay for performance and flexibility.

Project Motivation (Extra Credit and maybe a nice LOR)

Modern city-building games and real-world urban planning often rely on extensive manual modeling. NetWeave showcases how to automate much of that design:
	1.	User Sketch → Semantic Road Layers
	•	Different road types, lane counts, roundabouts, traffic signals, etc.
	2.	Deep Learning Transformation
	•	A trained ControlNet model transforms the “semantic sketch” into a richly detailed, stylized map.
	3.	Graph Extraction & Simulation
	•	We use the resulting map to extract a road network (nodes & edges) and simulate traffic or agent flow.

This platform demonstrates how a user’s creative sketches can become actionable data for simulations—helpful both in urban planning prototypes and for procedural city generation in gaming.

Key Features
	1.	Sketch-to-City Conversion
	•	Users can draw color-coded lines to indicate road hierarchies, speed limits, and directions.
	•	NetWeave’s ControlNet integration transforms these lines into a realistic top-down city map.
	2.	Dynamic Road & Building Generation
	•	OSMnx is leveraged to fetch real-world building footprint styles, or to add synthetic buildings in random distributions.
	•	Intersection detection, roundabout flags, and property generation on roads.
	3.	Cellular Automata or Agent-Based Simulation
	•	The extracted road graph can be used with Nagel–Schreckenberg or custom CA rules to simulate traffic flows.
	•	Or, an agent-based approach with start/end points among the generated properties (residential, commercial, industrial).
	4.	Modular Architecture
	•	Python handles the deep learning (GAN/ControlNet) and road-network data generation.
	•	Go (with frameworks like Gin) can serve the final application and manage concurrency for real-time or batch simulations.
	5.	Scalable to Large Areas
	•	Allows generating multiple bounding boxes, caching OSM data, or even using local .pbf files for massive coverage.

Architecture Overview

    ┌─────────────┐        ┌────────────────────┐        ┌───────────────┐
    │ User Sketch  │  --->  │  ControlNet Module │  --->  │  Generated Map │
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

	1.	User Sketch: A color-coded or conceptual drawing that indicates road types, lanes, etc.
	2.	ControlNet Module: Uses a Stable Diffusion + ControlNet pipeline to turn the user sketch into a realistic map image.
	3.	Generated Map: The styled city map output from the deep learning pipeline.
	4.	Road Network Extraction: The map or bounding boxes are converted into a graph structure, plus random property generation (residential, commercial, industrial).
	5.	Simulation: A discrete traffic flow or agent simulation is run on the extracted graph data, potentially visualized back to the user.

How It Works
	1.	Data Generation
	•	We use a Python script with OSMnx to gather training pairs:
	•	Control (semantic sketches)
	•	Target (realistic styled maps)
	•	These pairs are used to train a specialized ControlNet model.
	2.	User Interaction
	•	At runtime, the user draws or uploads a semantic road sketch.
	•	The ControlNet inference service (Python) transforms this into a styled map.
	3.	Graph Extraction
	•	A skeletonization or direct bounding box approach extracts roads, intersections, and building data from the map or from OSMnx queries.
	•	This produces a final road graph used for simulation.
	4.	Traffic Simulation
	•	In Go, a cellular automata or agent-based model simulates movement across the nodes and edges.
	•	Results can be visualized or further analyzed (e.g., congestion hotspots).

Getting Started
	1.	Clone the Repository

git clone https://github.com/username/netweave.git


	2.	Install Dependencies
	•	Python (3.9+) for OSMnx, PyTorch, etc.
	•	Go (1.19+) for the backend server and simulation engine.

pip install -r requirements.txt
go mod tidy


	3.	Train or Load a Pretrained ControlNet
	•	If you have pretrained weights, place them in trained_model/controlnet/.
	•	Otherwise, run python train_controlnet.py --dataset my_map_dataset to train.
	4.	Generate Data
	•	python ds.py --output-dir my_data --samples 5 --size 512
	•	Produces control/target image pairs, plus metadata about roads and buildings.
	5.	Run the App
	•	Python Inference Server: python inference_server.py
	•	Go Simulation Server: go run main.go
	•	Access the UI at http://localhost:8080 and upload your sketches.

Demo

Sketch (Control)	Generated Map (Target)
	

	In this example, a color-coded sketch for roads is transformed into a more realistic city layout with building footprints and properly styled roads.

