<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';
	import type { Tool } from '$lib/types';
	import type { Shadow } from 'fabric';

	interface CanvasEvents {
		update: string; // Base64 image data
		error: string; // Error message
	}
	interface ToolSetting {
		color: string;
		width: number;
		shadow?: Shadow;
	}
	}

	export let selectedTool: Tool;
	const dispatch = createEventDispatcher<CanvasEvents>();
	let isLoading = true;
	let canvas: HTMLCanvasElement;
	let fabricCanvas: fabric.Canvas;

	const toolSettings: Record<Tool, ToolSetting> = {
		road: {
			color: '#404040',
			width: 20,
			shadow: new fabric.Shadow({
				color: 'rgba(0,0,0,0.2)',
				blur: 4,
				offsetX: 2,
				offsetY: 2
			})
		},
		intersection: {
			color: '#666666',
			width: 30,
			shadow: new fabric.Shadow({
				color: 'rgba(0,0,0,0.3)',
				blur: 6,
				offsetX: 3,
				offsetY: 3
			})
		},
		trafficLight: {
			color: '#FF4444',
			width: 15,
			shadow: new fabric.Shadow({
				color: 'rgba(255,0,0,0.2)',
				blur: 4,
				offsetX: 1,
				offsetY: 1
			})
		}
	};

	const CANVAS_WIDTH = 800;
	const CANVAS_HEIGHT = 600;
	const GRID_SIZE = 20;
	const GRID_COLOR = '#e0e0e0';

	onMount(async () => {
		if (!browser) return;

		try {
			const { fabric } = await import('fabric');
			initializeCanvas(fabric);
		} catch (error) {
			dispatch('error', 'Failed to initialize canvas');
			console.error('Canvas initialization failed:', error);
		}

		return () => {
			if (fabricCanvas) {
				fabricCanvas.dispose();
			}
		};
	});

	function initializeCanvas(fabric: any) {
		fabricCanvas = new fabric.Canvas(canvas, {
			isDrawingMode: true,
			width: CANVAS_WIDTH,
			height: CANVAS_HEIGHT,
			backgroundColor: '#f8f9fa',
			preserveObjectStacking: true
		});

		setupCanvas();
		isLoading = false;
	}

	function setupCanvas() {
		updateBrush();
		addGrid();
		setupEventListeners();
	}

	function setupEventListeners() {
		fabricCanvas.on('path:created', () => {
			const imageData = fabricCanvas.toDataURL({
				format: 'png',
				quality: 0.8
			});
			dispatch('update', imageData);
		});

		fabricCanvas.on('object:added', () => {
			fabricCanvas.renderAll();
		});
	}

	function updateBrush() {
		if (!fabricCanvas || !selectedTool) return;

		const settings = toolSettings[selectedTool];
		const brush = new fabric.PencilBrush(fabricCanvas);
		brush.width = settings.width;
		brush.color = settings.color;
		brush.shadow = settings.shadow;
		fabricCanvas.freeDrawingBrush = brush;
	}

	function addGrid() {
		if (!fabricCanvas) return;

		const gridLines: fabric.Line[] = [];

		// Vertical lines
		for (let i = 0; i <= CANVAS_WIDTH; i += GRID_SIZE) {
			gridLines.push(
				new fabric.Line([i, 0, i, CANVAS_HEIGHT], {
					stroke: GRID_COLOR,
					selectable: false,
					evented: false,
					excludeFromExport: true
				})
			);
		}

		// Horizontal lines
		for (let i = 0; i <= CANVAS_HEIGHT; i += GRID_SIZE) {
			gridLines.push(
				new fabric.Line([0, i, CANVAS_WIDTH, i], {
					stroke: GRID_COLOR,
					selectable: false,
					evented: false,
					excludeFromExport: true
				})
			);
		}

		fabricCanvas.add(...gridLines);
		fabricCanvas.renderAll();
	}

	// Watch for tool changes
	$: if (fabricCanvas && selectedTool) {
		updateBrush();
	}
</script>

<div class="canvas-container relative">
	{#if isLoading}
		<div class="flex h-[600px] items-center justify-center rounded bg-gray-100">
			<span class="font-medium text-gray-600">Initializing canvas...</span>
		</div>
	{:else}
		<canvas
			bind:this={canvas}
			class="rounded border border-gray-200 shadow-sm"
			aria-label="Drawing canvas for road network design"
		></canvas>
	{/if}
</div>

<style>
	.canvas-container {
		width: 800px;
		height: 600px;
	}
</style>
