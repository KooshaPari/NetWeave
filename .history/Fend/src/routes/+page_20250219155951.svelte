<script lang="ts">
	import { onMount } from 'svelte';
	import paper from 'paper';

	let inputCanvas: HTMLCanvasElement;
	let outputCanvas: HTMLCanvasElement;
	let isSimulating = false;

	let roadNetwork: paper.Project;
	let simulationView: paper.Project;
	let updateOutputTimeout: number | null = null;
	let drawingLayer: paper.Layer;
	let guideLayer: paper.Layer;
	let currentPath: paper.Path | null = null;
	let pathPoints: paper.Point[] = [];

	function initializeLayers() {
		// Guide layer for grid
		guideLayer = new paper.Layer();
		createGuideGrid();
		guideLayer.opacity = 0.3;

		// Drawing layer for roads and intersections
		drawingLayer = new paper.Layer();
		drawingLayer.activate();
	}

	function setupTools() {
		// Tool state
		let isDrawing = false;
		const POINT_DISTANCE_THRESHOLD = 10;
		let lastPoint: paper.Point | null = null;

		// Road drawing tool with optimized performance
		const roadTool = new paper.Tool();

		roadTool.onMouseDown = (event: paper.ToolEvent) => {
			if ($toolSettings.currentTool === 'road') {
				isDrawing = true;
				const snappedPoint = snapToGrid(event.point);
				pathPoints = [snappedPoint];
				lastPoint = snappedPoint;

				currentPath = new paper.Path({
					segments: [snappedPoint],
					strokeColor: 'black',
					strokeWidth: $toolSettings.roadType.lanes * 10,
					strokeCap: 'round',
					strokeJoin: 'round'
				});

				// Add lane markings efficiently
				if (!$toolSettings.roadType.isOneWay && $toolSettings.roadType.lanes > 1) {
					const centerLine = new paper.Path({
						segments: [snappedPoint],
						strokeColor: 'yellow',
						strokeWidth: 2,
						dashArray: [10, 10]
					});
					currentPath.centerLine = centerLine;
				}
			}
		};

		roadTool.onMouseDrag = (event: paper.ToolEvent) => {
			if (isDrawing && currentPath && lastPoint) {
				const snappedPoint = snapToGrid(event.point);

				// Only add points if we've moved far enough
				if (lastPoint.getDistance(snappedPoint) > POINT_DISTANCE_THRESHOLD) {
					pathPoints.push(snappedPoint);
					currentPath.add(snappedPoint);

					// Update center line if it exists
					if (currentPath.centerLine) {
						currentPath.centerLine.add(snappedPoint);
					}

					// Smooth only the last few segments for performance
					if (pathPoints.length > 2) {
						smoothLastSegments(currentPath, 3);
						if (currentPath.centerLine) {
							smoothLastSegments(currentPath.centerLine, 3);
						}
					}

					lastPoint = snappedPoint;
					roadNetwork.view.update();
				}
			}
		};

		roadTool.onMouseUp = () => {
			if (isDrawing && currentPath) {
				if (pathPoints.length > 2) {
					// Final smoothing of the path
					currentPath.simplify(10);
					if (currentPath.centerLine) {
						currentPath.centerLine.simplify(10);
					}

					// Add to road segments
					const roadSegment: RoadSegment = {
						path: currentPath,
						lanes: $toolSettings.roadType.lanes,
						speedLimit: $toolSettings.roadType.speedLimit,
						isOneWay: $toolSettings.roadType.isOneWay,
						type: 'normal'
					};

					roadSegments.push(roadSegment);
				} else {
					// Remove too-short paths
					currentPath.remove();
					if (currentPath.centerLine) {
						currentPath.centerLine.remove();
					}
				}

				isDrawing = false;
				currentPath = null;
				pathPoints = [];
				lastPoint = null;

				roadNetwork.view.update();
				throttledUpdateOutput();
			}
		};

		// Helper function to smooth only the last few segments
		function smoothLastSegments(path: paper.Path, count: number) {
			const segments = path.segments;
			const len = segments.length;

			if (len < 2) return;

			const start = Math.max(0, len - count);
			for (let i = start; i < len - 1; i++) {
				const curr = segments[i];
				const next = segments[i + 1];
				const vector = next.point.subtract(curr.point);
				const handleLen = vector.length / 4;
				curr.handleOut = vector.normalize().multiply(handleLen);
				next.handleIn = vector.normalize().multiply(-handleLen);
			}
		}

		// Set as active tool
		roadTool.activate();
	}
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
		isOneWay: false,
		type: 'signal' as 'signal' | 'roundabout'
	};

	const gridSize = 40;
	const snapToGrid = (point: paper.Point): paper.Point => {
		return new paper.Point(
			Math.round(point.x / gridSize) * gridSize,
			Math.round(point.y / gridSize) * gridSize
		);
	};

	function setupTools() {
		const toolLayer = new paper.Layer();
		let currentPath: paper.Path;
		let intersectionPreview: paper.Group;
		let pathPoints: paper.Point[] = [];
		const POINT_DISTANCE_THRESHOLD = 10;

		// Road drawing tool
		const roadTool = new paper.Tool();
		roadTool.onMouseDown = (event: paper.ToolEvent) => {
			if (currentTool === 'road') {
				const snappedPoint = snapToGrid(event.point);
				pathPoints = [snappedPoint];
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

		roadTool.onMouseDrag = (event: paper.ToolEvent) => {
			if (currentTool === 'road' && currentPath) {
				const snappedPoint = snapToGrid(event.point);
				const lastPoint = pathPoints[pathPoints.length - 1];

				if (lastPoint.getDistance(snappedPoint) > POINT_DISTANCE_THRESHOLD) {
					pathPoints.push(snappedPoint);
					currentPath.add(snappedPoint);

					// Basic smoothing during drawing
					if (pathPoints.length > 2) {
						const segments = currentPath.segments;
						const last = segments[segments.length - 1];
						const secondLast = segments[segments.length - 2];
						if (last && secondLast) {
							const vector = last.point.subtract(secondLast.point);
							const normal = vector.normalize().rotate(90, new paper.Point(0, 0));
							secondLast.handleOut = vector.divide(4);
							secondLast.handleIn = vector.divide(4).multiply(-1);
						}
					}

					roadNetwork.view.update();

					if (updateOutputTimeout) {
						clearTimeout(updateOutputTimeout);
					}
					updateOutputTimeout = setTimeout(updateOutputView, 100) as unknown as number;
				}
			}
		};

		roadTool.onMouseUp = () => {
			if (currentTool === 'road' && currentPath && pathPoints.length > 2) {
				currentPath.simplify(10);
				// Fix the smooth call to use the correct arguments
				currentPath.smooth();
				roadNetwork.view.update();
				updateOutputView();
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

		// Set road tool as active by default
		roadTool.activate();
	}

	// Use only one grid function
	function createGuideGrid() {
		const guideLayer = new paper.Layer();
		const gridColor = new paper.Color(0, 0, 0, 0.1);

		// Create grid points
		for (let x = 0; x < paper.view.bounds.width; x += gridSize) {
			for (let y = 0; y < paper.view.bounds.height; y += gridSize) {
				new paper.Path.Circle({
					center: [x, y],
					radius: 2,
					fillColor: gridColor
				});
			}
		}

		guideLayer.opacity = 0.3;
		guideLayer.sendToBack();
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
		intersection.dashArray = [];
		return intersection;
	}

	// Cellular Automata Traffic Simulation
	class TrafficSimulation {
		private cells: TrafficCell[][][] = []; // 3D array: [x][y][lane]
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

		// Create guide grid first
		createGuideGrid();

		// Setup tools after grid
		setupTools();

		// Setup output canvas
		const outputScope = new paper.PaperScope();
		outputScope.setup(outputCanvas);
		simulationView = outputScope.project;
		simulationView.view.autoUpdate = false;

		// Initial render
		roadNetwork.view.update();
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
