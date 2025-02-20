<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';
	import type { Tool } from '$lib/types';

	interface CanvasEvents {
		update: string;
	}

	export let selectedTool: Tool;
	const dispatch = createEventDispatcher<CanvasEvents>();
	let isLoading = true;
	let canvas: HTMLCanvasElement;
	let fabricCanvas: any = null;

	const toolSettings = {
		road: {
			color: '#404040',
			width: 20
		},
		intersection: {
			color: '#666666',
			width: 30
		},
		trafficLight: {
			color: '#FF4444',
			width: 15
		}
	} as const;

	onMount(async () => {
		if (!browser) return;

		try {
			const { StaticCanvas } = await import('fabric');

			fabricCanvas = new fabric.Canvas(canvas, {
				isDrawingMode: true,
				width: 800,
				height: 600,
				backgroundColor: '#f8f9fa'
			});

			const settings = toolSettings[selectedTool];
			const brush = new fabric.PencilBrush(fabricCanvas);
			brush.width = settings.width;
			brush.color = settings.color;
			fabricCanvas.freeDrawingBrush = brush;

			addGrid(fabricCanvas, fabricModule.Line);

			fabricCanvas.on('path:created', () => {
				if (fabricCanvas) {
					dispatch('update', fabricCanvas.toDataURL());
				}
			});

			isLoading = false;
		} catch (error) {
			console.error('Failed to initialize canvas:', error);
		}
	});

	async function updateBrush() {
		if (!fabricCanvas) return;

		const settings = toolSettings[selectedTool];
		const { StaticCanvas } = await import('fabric');
		const brush = new fabric.PencilBrush(fabricCanvas);
		brush.width = settings.width;
		brush.color = settings.color;
		fabricCanvas.freeDrawingBrush = brush;
	}

	function addGrid(canvas: any, Line: any) {
		const gridSize = 20;
		const gridColor = '#e0e0e0';

		for (let i = 0; i < canvas.getWidth() / gridSize; i++) {
			canvas.add(
				new Line([i * gridSize, 0, i * gridSize, canvas.getHeight()], {
					stroke: gridColor,
					selectable: false
				})
			);
		}

		for (let i = 0; i < canvas.getHeight() / gridSize; i++) {
			canvas.add(
				new Line([0, i * gridSize, canvas.getWidth(), i * gridSize], {
					stroke: gridColor,
					selectable: false
				})
			);
		}

		canvas.renderAll();
	}

	$: if (fabricCanvas && selectedTool) {
		updateBrush();
	}
</script>

<div class="canvas-container">
	{#if isLoading}
		<div class="flex h-[600px] items-center justify-center rounded bg-gray-100">
			<span class="text-gray-600">Loading canvas...</span>
		</div>
	{:else}
		<canvas bind:this={canvas} class="rounded border border-gray-200 shadow-sm"></canvas>
	{/if}
</div>

<style>
	.canvas-container {
		width: 800px;
		height: 600px;
	}
</style>
