<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { Tool } from '$lib/types';

	export let selectedTool: Tool;
	const dispatch = createEventDispatcher();

	const tools = [
		{ id: 'road', label: 'Road', icon: '🛣️' },
		{ id: 'intersection', label: 'Intersection', icon: '🔄' },
		{ id: 'trafficLight', label: 'Traffic Light', icon: '🚦' }
	];
</script>

<div class="mb-4 flex gap-2">
	{#each tools as tool}
		<button
			class="flex items-center gap-2 rounded px-4 py-2 {selectedTool === tool.id
				? 'bg-blue-500 text-white'
				: 'bg-gray-200'}"
			on:click={() => dispatch('toolSelect', tool.id)}
		>
			<span>{tool.icon}</span>
			<span>{tool.label}</span>
		</button>
	{/each}
</div>
