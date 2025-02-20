<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	type ToolType = 'road' | 'intersection' | 'trafficLight';
	export let selectedTool: ToolType;

	const dispatch = createEventDispatcher<{
		toolSelect: ToolType;
	}>();

	function handleToolSelect(tool: ToolType) {
		dispatch('toolSelect', tool);
	}
</script>

<div class="flex gap-2">
	<button
		class="flex items-center gap-2 rounded px-4 py-2 {selectedTool === 'road'
			? 'bg-blue-100'
			: 'bg-gray-100'}"
		on:click={() => handleToolSelect('road')}
	>
		🚗 Road
	</button>
	<button
		class="flex items-center gap-2 rounded px-4 py-2 {selectedTool === 'intersection'
			? 'bg-blue-100'
			: 'bg-gray-100'}"
		on:click={() => handleToolSelect('intersection')}
	>
		🚦 Intersection
	</button>
	<button
		class="flex items-center gap-2 rounded px-4 py-2 {selectedTool === 'trafficLight'
			? 'bg-blue-100'
			: 'bg-gray-100'}"
		on:click={() => handleToolSelect('trafficLight')}
	>
		🚥 Traffic Light
	</button>
</div>
