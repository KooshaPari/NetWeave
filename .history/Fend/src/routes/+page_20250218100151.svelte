<script lang="ts">
	import { onMount } from 'svelte';
	import DrawingCanvas from '$lib/components/DrawingCanvas.svelte';
	import OutputCanvas from '$lib/components/OutputCanvas.svelte';
	import ToolPanel from '$lib/components/ToolPanel.svelte';
	import type { Tool, SimulationState } from '$lib/types';

	let selectedTool: Tool = 'road';
	let isSimulating = false;
	let simulationState: SimulationState | null = null;

	// Toggle between pre-sim render and simulation view
	function toggleSimulation() {
		isSimulating = !isSimulating;
	}

	// Handle new drawing data
	function handleDrawingUpdate(event: CustomEvent<ImageData>) {
		// This would normally go to your backend for processing
		// For MVP, we'll just pass it to the output canvas
		simulationState = {
			networkImage: event.detail,
			vehicles: [],
			trafficLights: [],
			timestamp: Date.now()
		};
	}
</script>

<div class="min-h-screen bg-gray-100">
	<main class="container mx-auto p-4">
		<!-- Header with controls -->
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

		<!-- Main content area -->
		<div class="flex gap-6">
			<!-- Left panel: Drawing tools and input canvas -->
			<div class="flex-1 rounded-lg bg-white p-4 shadow-lg">
				<div class="mb-4">
					<h2 class="mb-2 text-lg font-semibold">Network Design</h2>
					<ToolPanel {selectedTool} on:toolSelect={(e) => (selectedTool = e.detail)} />
				</div>
				<DrawingCanvas {selectedTool} on:update={handleDrawingUpdate} />
			</div>

			<!-- Right panel: Output canvas (pre-sim render or simulation) -->
			<div class="flex-1 rounded-lg bg-white p-4 shadow-lg">
				<h2 class="mb-4 text-lg font-semibold">
					{isSimulating ? 'Traffic Simulation' : 'Network Preview'}
				</h2>
				<OutputCanvas {simulationState} {isSimulating} />
			</div>
		</div>
	</main>
</div>
