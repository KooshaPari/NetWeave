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

	onMount(() => {
		// Setup input canvas with view bounds optimization
		paper.setup(inputCanvas);
		roadNetwork = paper.project;
		roadNetwork.view.autoUpdate = false; // Prevent automatic updates

		setupDrawingTools();

		// Setup output canvas
		const outputScope = new paper.PaperScope();
		outputScope.setup(outputCanvas);
		simulationView = outputScope.project;
		simulationView.view.autoUpdate = false; // Prevent automatic updates

		drawGrid();
		roadNetwork.view.update(); // Initial render
	});

	function setupDrawingTools() {
		const roadTool = new paper.Tool();
		let currentPath: paper.Path;
		let pathPoints: paper.Point[] = [];
		const POINT_DISTANCE_THRESHOLD = 10; // Minimum distance between points

		roadTool.onMouseDown = (event: paper.ToolEvent) => {
			pathPoints = [event.point];
			currentPath = new paper.Path({
				segments: [event.point],
				strokeColor: 'black',
				strokeWidth: 20,
				strokeCap: 'round',
				strokeJoin: 'round'
			});
		};

		roadTool.onMouseDrag = (event: paper.ToolEvent) => {
			// Only add points if they're far enough from the last point
			const lastPoint = pathPoints[pathPoints.length - 1];
			if (lastPoint.getDistance(event.point) > POINT_DISTANCE_THRESHOLD) {
				pathPoints.push(event.point);
				currentPath.add(event.point);

				// Basic smoothing during drawing
				if (pathPoints.length > 2) {
					const segments = currentPath.segments;
					const last = segments[segments.length - 1];
					const secondLast = segments[segments.length - 2];
					if (last && secondLast) {
						const vector = last.point.subtract(secondLast.point);
						const normal = vector.normalize().rotate(90,);
						secondLast.handleOut = vector.divide(4);
						secondLast.handleIn = vector.divide(4).multiply(-1);
					}
				}

				roadNetwork.view.update(); // Update only the input canvas

				// Debounce output view updates
				if (updateOutputTimeout) {
					clearTimeout(updateOutputTimeout);
				}
				updateOutputTimeout = setTimeout(updateOutputView, 100) as unknown as number;
			}
		};

		roadTool.onMouseUp = () => {
			if (pathPoints.length > 2) {
				// Optimized path simplification
				currentPath.simplify(10);
				currentPath.smooth({ type: 'continuous' });
			}
			roadNetwork.view.update();
			updateOutputView();
		};
	}

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
