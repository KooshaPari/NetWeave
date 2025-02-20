<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';
	import type { fabric } from 'fabric';
	import type { Tool } from '$lib/types';

	interface CanvasEvents {
		update: string;
	}

	export let selectedTool: Tool;
	const dispatch = createEventDispatcher<CanvasEvents>();
	let isLoading = true;
	let canvas: HTMLCanvasElement;
	let fabricCanvas: fabric.Canvas | null = null;

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
			const fabricModule = await import('fabric');
			const { Canvas, Line, PencilBrush } = fabricModule.fabric;

			fabricCanvas = new Canvas(canvas, {
				isDrawingMode: true,
				width: 800,
				height: 600,
				backgroundColor: '#f8f9fa'
			});

			if (fabricCanvas) {
				const settings = toolSettings[selectedTool];
				const brush = new PencilBrush(fabricCanvas);
				brush.width = settings.width;
				brush.color = settings.color;
				fabricCanvas.freeDrawingBrush = brush;

				addGrid(fabricCanvas, Line);

				fabricCanvas.on('path:created', () => {
					if (fabricCanvas) {
						dispatch('update', fabricCanvas.toDataURL());
					}
				});
			}

			isLoading = false;
		} catch (error) {
			console.error('Failed to initialize canvas:', error);
		}

		return () => {
			if (fabricCanvas) {
				fabricCanvas.dispose();
			}
		};
	});

	$: if (fabricCanvas && selectedTool) {
		updateBrush(fabricCanvas);
	}

	async function updateBrush(canvas: fabric.Canvas) {
		const settings = toolSettings[selectedTool];
		const fabricModule = await import('fabric');
		const brush = new fabricModule.fabric.PencilBrush(canvas);
		brush.width = settings.width;
		brush.color = settings.color;
		canvas.freeDrawingBrush = brush;
	}

	function addGrid(canvas: fabric.Canvas, Line: typeof fabric.Line) {
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
