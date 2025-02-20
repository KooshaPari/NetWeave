<script lang="ts">
	import { onMount } from 'svelte';
	import DrawingCanvas from '$lib/components/DrawingCanvas.svelte';
	import OutputCanvas from '$lib/components/OutputCanvas.svelte';
	import ToolPanel from '$lib/components/ToolPanel.svelte';
	import type { SimulationState } from '$lib/types';

	// Define tool types
	type RoadToolType = 'highway' | 'mainRoad' | 'localRoad';
	type IntersectionToolType = 'roundabout' | 'signalizedIntersection' | 'slipRoad';
	type Tool = RoadToolType | IntersectionToolType;
	type ToolCategory = 'road' | 'intersection' | 'trafficLight';

	// Initialize both the specific tool and category
	let selectedTool: Tool = 'localRoad';
	let selectedCategory: ToolCategory = 'road';
	let isSimulating = false;
	let simulationState: SimulationState | null = null;

	function toggleSimulation() {
		isSimulating = !isSimulating;
	}

	function handleToolSelect(event: CustomEvent<ToolCategory>) {
		selectedCategory = event.detail;
		// Set appropriate default tool for each category
		if (event.detail === 'road') {
			selectedTool = 'localRoad';
		} else if (event.detail === 'intersection') {
			selectedTool = 'roundabout';
		}
	}

	function handleDrawingUpdate(event: CustomEvent<{ canvas: string; roadData: any }>) {
		simulationState = {
			networkImage: event.detail.canvas,
			vehicles: [],
			trafficLights: [],
			timestamp: Date.now()
		};
	}
</script>

<div class="min-h-screen bg-gray-100">
	<main class="container mx-auto p-4">
		<header class="mb-6 flex items-center justify-between">
			<h1 class="text-2xl font-bold text-gray-800">Traffic Network Simulator</h1>
			<div class="flex items-center gap-4">
				<button
					class="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
					on:click={toggleSimulation}
				>
					{isSimulating ? 'View Network' : 'Start Simulation'}
				</button>
			</div>
		</header>

		<div class="flex gap-6">
			<div class="flex-1 rounded-lg bg-white p-4 shadow-lg">
				<div class="mb-4">
					<h2 class="mb-2 text-lg font-semibold">Network Design</h2>
					<ToolPanel selectedTool={selectedCategory} on:toolSelect={handleToolSelect} />
				</div>
				<DrawingCanvas {selectedTool} {selectedCategory} on:update={handleDrawingUpdate} />
			</div>

			<div class="flex-1 rounded-lg bg-white p-4 shadow-lg">
				<h2 class="mb-4 text-lg font-semibold">
					{isSimulating ? 'Traffic Simulation' : 'Network Preview'}
				</h2>
				<OutputCanvas {simulationState} {isSimulating} />
			</div>
		</div>
	</main>
</div>
