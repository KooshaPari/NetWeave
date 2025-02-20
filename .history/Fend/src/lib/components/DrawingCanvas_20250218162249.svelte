<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';
	import type { Tool } from '$lib/types';

	interface CanvasEvents {
		update: string;
	}
	$: console.log('isLoading:', isLoading);
	export let selectedTool: Tool;
	const dispatch = createEventDispatcher<CanvasEvents>();
	let isLoading = true;
	let canvas: HTMLCanvasElement;
	let fabricCanvas: any = null;
	interface RoadType {
		name: string;
		color: string;
		width: number;
		lanes: number;
		speedLimit: number;
		capacity: number;
		type: 'one-way' | 'two-way';
		zoning: boolean;
		margin: number;
		style: {
			strokeWidth: number;
			strokeDashArray?: number[];
			stroke: string;
		};
	}

	const roadTypes = {
		highway: {
			name: 'Highway',
			color: '#505050',
			width: 40,
			lanes: 3,
			speedLimit: 100,
			capacity: 2000,
			type: 'one-way',
			zoning: false,
			margin: 15,
			style: {
				strokeWidth: 40,
				stroke: '#505050'
			}
		},
		arterial: {
			name: 'Six-Lane Road',
			color: '#454545',
			width: 35,
			lanes: 3,
			speedLimit: 60,
			capacity: 1500,
			type: 'two-way',
			zoning: true,
			margin: 10,
			style: {
				strokeWidth: 35,
				stroke: '#454545'
			}
		},
		collector: {
			name: 'Four-Lane Road',
			color: '#404040',
			width: 30,
			lanes: 2,
			speedLimit: 40,
			capacity: 1000,
			type: 'two-way',
			zoning: true,
			margin: 8,
			style: {
				strokeWidth: 30,
				stroke: '#404040'
			}
		},
		local: {
			name: 'Two-Lane Road',
			color: '#383838',
			width: 20,
			lanes: 1,
			speedLimit: 30,
			capacity: 500,
			type: 'two-way',
			zoning: true,
			margin: 5,
			style: {
				strokeWidth: 20,
				stroke: '#383838'
			}
		},
		oneWay: {
			name: 'One-Way Street',
			color: '#353535',
			width: 15,
			lanes: 1,
			speedLimit: 30,
			capacity: 400,
			type: 'one-way',
			zoning: true,
			margin: 5,
			style: {
				strokeWidth: 15,
				strokeDashArray: [10, 5],
				stroke: '#353535'
			}
		}
	} as const;
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
		console.log('Loading fabric');
		try {
			console.log('Importing fabric');
			const fabric = await import('fabric');
			console.log('Imported fabric');
			// Initialize canvas with proper configuration
			fabricCanvas = new fabric.Canvas(canvas, {
				backgroundColor: '#f8f9fa'
			});
			console.log('Creating fabric canvas');
			fabric.Object.prototype.noScaleCache = false;

			// Configure canvas settings
			console.log('Setting up canvas dimensions');
			fabricCanvas.setDimensions({
				width: 800,
				height: 600
			});
			console.log('Setting up canvas background color');
			//fabricCanvas.backgroundColor('#f8f9fa', fabricCanvas.renderAll.bind(fabricCanvas));
			console.log('Setting up canvas');
			// Set up initial drawing state
			initializeDrawingState(fabric);
			console.log('Initializing drawing state');
			addDefaultShapes(fabric);
			console.log('Adding default shapes');
			setupEventListeners();
			console.log('Canvas setup complete');
			isLoading = false;
		} catch (error) {
			console.error('Failed to initialize canvas:', error);
		}
	});

	function initializeDrawingState(fabric: any) {
		const currentRoad = roadTypes[selectedTool as keyof typeof roadTypes];

		fabricCanvas.isDrawingMode = true;
		const brush = new fabric.PencilBrush(fabricCanvas);
		brush.width = currentRoad.width;
		brush.color = currentRoad.color;
		brush.strokeDashArray = currentRoad.style.strokeDashArray;
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
			const roadType = roadTypes[selectedTool as keyof typeof roadTypes];

			// Add road metadata for simulation
			path.set({
				strokeUniform: true,
				hasControls: true,
				data: {
					type: selectedTool,
					lanes: roadType.lanes,
					speedLimit: roadType.speedLimit,
					capacity: roadType.capacity,
					isOneWay: roadType.type === 'one-way',
					margin: roadType.margin
				}
			});

			// Add lane markers
			if (roadType.type === 'two-way') {
				addLaneMarkers(path, roadType);
			}

			dispatch('update', {
				canvas: fabricCanvas.toDataURL(),
				roadData: path.data
			});
		});
	}

	function addLaneMarkers(path: any, roadType: RoadType) {
		const coords = path.path;
		if (!coords || coords.length < 2) return;

		// Create center line for two-way roads
		const centerLine = new fabric.Path(path.path, {
			stroke: '#FFFFFF',
			strokeWidth: 2,
			strokeDashArray: [10, 10],
			selectable: false
		});

		// Create lane dividers
		if (roadType.lanes > 1) {
			const laneWidth = roadType.width / roadType.lanes;
			for (let i = 1; i < roadType.lanes; i++) {
				const offset = i * laneWidth - roadType.width / 2;
				const laneDivider = new fabric.Path(path.path, {
					stroke: '#FFFFFF',
					strokeWidth: 1,
					strokeDashArray: [5, 5],
					selectable: false,
					objectCaching: false
				});
				fabricCanvas.add(laneDivider);
			}
		}

		fabricCanvas.add(centerLine);
		fabricCanvas.renderAll();
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
