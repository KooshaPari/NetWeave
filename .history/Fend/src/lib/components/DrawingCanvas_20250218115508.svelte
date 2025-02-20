<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';

	const dispatch = createEventDispatcher();
	let isLoading = true;
	let canvas: any;
	let fabricCanvas: any;

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
	};

	onMount(() => {
		if (browser) {
			
			import('fabric').then(({ fabric }) => {
				fabricCanvas = new fabric.Canvas(canvas, {
					isDrawingMode: true,
					width: 800,
					height: 600,
					backgroundColor: '#f8f9fa'
				});

				
				updateBrush();
				addGrid();

				fabricCanvas.on('path:created', () => {
					dispatch('update', fabricCanvas.toDataURL());
				});
				isLoading = false;
			});
		}

		return () => {
			if (fabricCanvas) {
				fabricCanvas.dispose();
			}
		};
	});

	
	$: if (canvas && selectedTool) {
		updateBrush();
	}

	function updateBrush() {
		const settings = toolSettings[selectedTool];
		const brush = new fabric.PencilBrush(canvas);
		brush.width = settings.width;
		brush.color = settings.color;
		canvas.freeDrawingBrush = brush;
	}

	function addGrid() {
		const gridSize = 20;
		const gridColor = '#e0e0e0';

		for (let i = 0; i < canvas.width / gridSize; i++) {
			canvas.add(
				new fabric.Line([i * gridSize, 0, i * gridSize, canvas.height], {
					stroke: gridColor,
					selectable: false
				})
			);
		}

		for (let i = 0; i < canvas.height / gridSize; i++) {
			canvas.add(
				new fabric.Line([0, i * gridSize, canvas.width, i * gridSize], {
					stroke: gridColor,
					selectable: false
				})
			);
		}
	}
</script>

{#if isLoading}
	<div class="flex h-[600px] items-center justify-center rounded bg-gray-100">
		<span class="text-gray-600">Loading canvas...</span>
	</div>
{:else}
	<canvas bind:this={canvas}></canvas>
{/if}
