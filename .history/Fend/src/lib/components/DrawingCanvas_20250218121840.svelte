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
			width: 20,
			rx: 0,
			ry: 0
		},
		intersection: {
			color: '#666666',
			width: 30,
			rx: 10,
			ry: 10
		},
		trafficLight: {
			color: '#FF4444',
			width: 15,
			rx: 5,
			ry: 5
		}
	} as const;

	onMount(async () => {
		if (!browser) return;

		try {
			const fabric = await import('fabric');

			// Initialize canvas with proper configuration
			fabricCanvas = new fabric.Canvas(canvas);
			fabric.Object.prototype.noScaleCache = false;

			// Configure canvas settings
			fabricCanvas.setDimensions({
				width: 800,
				height: 600
			});
			fabricCanvas.backgroundColor('#f8f9fa', fabricCanvas.renderAll.bind(fabricCanvas));
            console.log("")
			// Set up initial drawing state
			initializeDrawingState(fabric);
			addDefaultShapes(fabric);
			setupEventListeners();

			isLoading = false;
		} catch (error) {
			console.error('Failed to initialize canvas:', error);
		}
	});

	function initializeDrawingState(fabric: any) {
		const settings = toolSettings[selectedTool];

		// Create default drawing configuration
		fabricCanvas.isDrawingMode = true;
		const brush = new fabric.PencilBrush(fabricCanvas);
		brush.width = settings.width;
		brush.color = settings.color;
		fabricCanvas.freeDrawingBrush = brush;
	}

	function addDefaultShapes(fabric: any) {
		// Add grid
		const gridSize = 20;
		const gridColor = '#e0e0e0';

		for (let i = 0; i <= fabricCanvas.width; i += gridSize) {
			const line = new fabric.Line([i, 0, i, fabricCanvas.height], {
				stroke: gridColor,
				selectable: false,
				strokeUniform: true,
				strokeWidth: 1
			});
			fabricCanvas.add(line);
		}

		for (let i = 0; i <= fabricCanvas.height; i += gridSize) {
			const line = new fabric.Line([0, i, fabricCanvas.width, i], {
				stroke: gridColor,
				selectable: false,
				strokeUniform: true,
				strokeWidth: 1
			});
			fabricCanvas.add(line);
		}

		// Example: Add intersection placeholder
		const intersection = new fabric.Rect({
			left: 100,
			top: 100,
			fill: toolSettings.intersection.color,
			width: toolSettings.intersection.width,
			height: toolSettings.intersection.width,
			strokeWidth: 2,
			stroke: '#4a4a4a',
			rx: toolSettings.intersection.rx,
			ry: toolSettings.intersection.ry,
			hasControls: true,
			strokeUniform: true
		});
		fabricCanvas.add(intersection);
	}

	function setupEventListeners() {
		fabricCanvas.on('path:created', (e: any) => {
			const path = e.path;
			path.set({
				strokeUniform: true,
				hasControls: true
			});

			dispatch('update', fabricCanvas.toDataURL());
		});

		fabricCanvas.on('object:modified', () => {
			dispatch('update', fabricCanvas.toDataURL());
		});
	}

	async function updateBrush() {
		if (!fabricCanvas) return;

		const settings = toolSettings[selectedTool];
		const fabric = await import('fabric');
		const brush = new fabric.PencilBrush(fabricCanvas);
		brush.width = settings.width;
		brush.color = settings.color;
		fabricCanvas.freeDrawingBrush = brush;
	}

	function toggleUniform() {
		const activeObject = fabricCanvas.getActiveObject();
		if (!activeObject) return;

		if (activeObject.type === 'activeSelection') {
			activeObject.getObjects().forEach((obj: any) => {
				obj.set('strokeUniform', !obj.strokeUniform);
			});
		} else {
			activeObject.set('strokeUniform', !activeObject.strokeUniform);
		}
		fabricCanvas.requestRenderAll();
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
