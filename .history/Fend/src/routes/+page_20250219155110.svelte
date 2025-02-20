<script lang="ts">
	import { onMount } from 'svelte';
	import paper from 'paper';

	let inputCanvas: HTMLCanvasElement;
	let outputCanvas: HTMLCanvasElement;
	let isSimulating = false;

	let roadNetwork: paper.Project;
	let simulationView: paper.Project;
	let updateOutputTimeout: number | null = null;

	interface Vehicle extends paper.Path.Circle {
		route?: paper.Path;
		progress?: number;
	}
	interface RoadSegment {
		path: paper.Path;
		lanes: number;
		speedLimit: number;
		isOneWay: boolean;
		type: 'normal' | 'slip' | 'roundabout';
		signalTiming?: number; // for intersections
	}

	interface TrafficCell {
		occupied: boolean;
		speed: number;
		direction: paper.Point;
		nextCell?: TrafficCell;
	}

	interface IntersectionNode {
		position: paper.Point;
		type: 'signal' | 'roundabout' | 'priority';
		connections: RoadSegment[];
		cells: TrafficCell[][]; // 2D grid for cellular automata
	}

	let currentTool: 'road' | 'intersection' | 'slip' | 'edit' = 'road';
	let selectedRoadType = {
		lanes: 2,
		speedLimit: 50,
		isOneWay: false
	};

	const gridSize = 40;
	function createGuideGrid() {
		const guideLayer = new paper.Layer();
		for (let x = 0; x < paper.view.bounds.width; x += gridSize) {
			for (let y = 0; y < paper.view.bounds.height; y += gridSize) {
				new paper.Path.Circle({
					center: [x, y],
					radius: 2,
					fillColor: new paper.Color(0, 0, 0, 0.1)
				});
			}
		}
		guideLayer.opacity = 0.3;
	}

	function setupTools() {
		const toolLayer = new paper.Layer();
		let currentPath: paper.Path;
		let intersectionPreview: paper.Group;

		// Snapping function
		const snapToGrid = (point: paper.Point): paper.Point => {
			return new paper.Point(
				Math.round(point.x / gridSize) * gridSize,
				Math.round(point.y / gridSize) * gridSize
			);
		};

		// Road drawing tool
		const roadTool = new paper.Tool();
		roadTool.onMouseDown = (event: paper.ToolEvent) => {
			if (currentTool === 'road') {
				const snappedPoint = snapToGrid(event.point);
				currentPath = new paper.Path({
					segments: [snappedPoint],
					strokeColor: 'black',
					strokeWidth: selectedRoadType.lanes * 10,
					strokeCap: 'round',
					strokeJoin: 'round'
				});

				// Add lane markings based on road type
				if (!selectedRoadType.isOneWay && selectedRoadType.lanes > 1) {
					const centerLine = currentPath.clone();
					centerLine.strokeColor = new paper.Color('yellow');
					centerLine.strokeWidth = 2;
					centerLine.dashArray = [10, 10];
				}
			}
		};

		// Intersection tool
		const intersectionTool = new paper.Tool();
		intersectionTool.onMouseMove = (event: paper.ToolEvent) => {
			if (currentTool === 'intersection') {
				const snappedPoint = snapToGrid(event.point);
				if (intersectionPreview) intersectionPreview.remove();

				intersectionPreview = createIntersectionPreview(snappedPoint);
			}
		};

		intersectionTool.onMouseDown = (event: paper.ToolEvent) => {
			if (currentTool === 'intersection') {
				const snappedPoint = snapToGrid(event.point);
				createIntersection(snappedPoint);
			}
		};
	}

	function createIntersectionPreview(center: paper.Point): paper.Group {
		const group = new paper.Group();

		switch (selectedRoadType.type) {
			case 'roundabout':
				const circle = new paper.Path.Circle({
					center: center,
					radius: gridSize,
					strokeColor: 'black',
					strokeWidth: 2,
					dashArray: [5, 5]
				});
				group.addChild(circle);
				break;

			case 'signal':
				const box = new paper.Path.Rectangle({
					center: center,
					size: [gridSize, gridSize],
					strokeColor: 'red',
					strokeWidth: 2,
					dashArray: [5, 5]
				});
				group.addChild(box);
				break;
		}

		return group;
	}

	function createIntersection(center: paper.Point): paper.Group {
		const intersection = createIntersectionPreview(center);
		intersection.strokeColor = new paper.Color('black');
		intersection.strokeWidth = 2;
		intersection.dashArray = []null;
		return intersection;
	}

	// Cellular Automata Traffic Simulation
	class TrafficSimulation {
		private cells: TrafficCell[][][]; // 3D array: [x][y][lane]
		private timeStep: number = 0;

		constructor(roadNetwork: RoadSegment[]) {
			this.initializeCells(roadNetwork);
		}

		private initializeCells(roadNetwork: RoadSegment[]) {
			// Convert road network to cellular grid
			roadNetwork.forEach((segment) => {
				const path = segment.path;
				const length = Math.ceil(path.length / gridSize);

				for (let i = 0; i < length; i++) {
					const point = path.getPointAt(i * gridSize);
					const direction = path.getTangentAt(i * gridSize);

					for (let lane = 0; lane < segment.lanes; lane++) {
						this.cells[Math.floor(point.x / gridSize)][Math.floor(point.y / gridSize)][lane] = {
							occupied: false,
							speed: 0,
							direction: direction
						};
					}
				}
			});
		}

		public update() {
			// Basic NaSch model implementation
			// 1. Acceleration
			this.cells.forEach((row, x) => {
				row.forEach((col, y) => {
					col.forEach((cell) => {
						if (cell.occupied && cell.speed < 5) {
							cell.speed++;
						}
					});
				});
			});

			// 2. Slowing (due to cars ahead)
			// 3. Randomization
			// 4. Movement
			this.timeStep++;
		}
	}
	onMount(() => {
		// Setup input canvas with view bounds optimization
		paper.setup(inputCanvas);
		roadNetwork = paper.project;
		roadNetwork.view.autoUpdate = false; // Prevent automatic updates

		setupTools();
		createGuideGrid();

		// Setup output canvas
		const outputScope = new paper.PaperScope();
		outputScope.setup(outputCanvas);
		simulationView = outputScope.project;
		simulationView.view.autoUpdate = false; // Prevent automatic updates

		drawGrid();
		roadNetwork.view.update(); // Initial render
	});

	function updateOutputView() {
		simulationView.activate();
		simulationView.clear();

		// Batch copy operations
		const networkCopy = roadNetwork.exportJSON();
		simulationView.importJSON(networkCopy);

		// Pre-simulation render
		renderPreSimulation();

		if (isSimulating) {
			renderSimulation();
		}

		simulationView.view.update();
		updateOutputTimeout = null;
	}

	// ... rest of the code remains the same ...

	// Optimized grid drawing
	function drawGrid() {
		const gridSize = 20;
		const gridColor = new paper.Color('#e0e0e0');
		const gridGroup = new paper.Group();

		// Draw vertical lines
		for (let x = 0; x < inputCanvas.width; x += gridSize) {
			gridGroup.addChild(
				new paper.Path.Line({
					from: [x, 0],
					to: [x, inputCanvas.height],
					strokeColor: gridColor,
					strokeWidth: 1
				})
			);
		}

		// Draw horizontal lines
		for (let y = 0; y < inputCanvas.height; y += gridSize) {
			gridGroup.addChild(
				new paper.Path.Line({
					from: [0, y],
					to: [inputCanvas.width, y],
					strokeColor: gridColor,
					strokeWidth: 1
				})
			);
		}

		// Send grid to back and reduce its opacity
		gridGroup.opacity = 0.5;
		gridGroup.sendToBack();
	}

	function renderPreSimulation() {
		// Enhance the road network with realistic styling
		const paths = simulationView.activeLayer.children as paper.Path[];
		paths.forEach((path: paper.Path) => {
			if (path.strokeColor) {
				// Add shadow effect
				path.shadowColor = new paper.Color(0, 0, 0, 0.2);
				path.shadowBlur = 10;
				path.shadowOffset = new paper.Point(5, 5);

				// Add road markings
				const roadMarking = path.clone();
				roadMarking.strokeColor = new paper.Color('white');
				roadMarking.strokeWidth = 2;
				roadMarking.dashArray = [20, 20];
			}
		});
	}

	function renderSimulation() {
		// Add vehicles
		const vehicles = createVehicles();

		// Animate vehicles
		paper.view.onFrame = (event: paper.Event) => {
			vehicles.forEach((vehicle: Vehicle) => {
				// Simple vehicle movement
				vehicle.position.x += 1;
				if (vehicle.position.x > outputCanvas.width) {
					vehicle.position.x = 0;
				}
			});
		};
	}

	function createVehicles(): Vehicle[] {
		const vehicles: Vehicle[] = [];
		const paths = simulationView.activeLayer.children as paper.Path[];

		paths.forEach((road: paper.Path) => {
			if (road.strokeColor) {
				// Create vehicle
				const vehicle = new paper.Path.Circle({
					center: road.firstSegment.point,
					radius: 5,
					fillColor: 'red'
				}) as Vehicle;

				vehicle.route = road;
				vehicle.progress = 0;
				vehicles.push(vehicle);
			}
		});

		return vehicles;
	}

	function toggleSimulation() {
		isSimulating = !isSimulating;
		updateOutputView();
	}

	function clearCanvas() {
		roadNetwork.activate();
		roadNetwork.clear();
		drawGrid();
		updateOutputView();
	}
</script>

<main class="min-h-screen bg-gray-100 p-4">
	<div class="container mx-auto">
		<div class="flex gap-4">
			<!-- Input Panel -->
			<div class="flex-1 rounded-lg bg-white p-4 shadow-lg">
				<div class="mb-4">
					<h2 class="text-lg font-semibold">Draw Road Network</h2>
					<div class="mt-2 flex gap-2">
						<button class="rounded bg-red-500 px-4 py-2 text-white" on:click={clearCanvas}>
							Clear
						</button>
					</div>
				</div>
				<canvas bind:this={inputCanvas} width={600} height={400} class="rounded border"></canvas>
			</div>

			<!-- Output Panel -->
			<div class="flex-1 rounded-lg bg-white p-4 shadow-lg">
				<div class="mb-4">
					<h2 class="text-lg font-semibold">Network Visualization</h2>
					<div class="mt-2 flex gap-2">
						<button class="rounded bg-blue-500 px-4 py-2 text-white" on:click={toggleSimulation}>
							{isSimulating ? 'Stop' : 'Start'} Simulation
						</button>
					</div>
				</div>
				<canvas bind:this={outputCanvas} width={600} height={400} class="rounded border"></canvas>
			</div>
		</div>
	</div>
</main>

<style>
	canvas {
		touch-action: none;
	}
</style>
