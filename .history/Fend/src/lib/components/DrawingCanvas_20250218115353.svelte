<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';

	const dispatch = createEventDispatcher<{ update: (payload: string) => void }>();
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
			// Import fabric only on client side
			import('fabric').then(({ fabric }) => {
				fabricCanvas = new fabric.Canvas(canvas, {
					isDrawingMode: true,
					width: 800,
					height: 600,
					backgroundColor: '#f8f9fa'
				});

				// Rest of your canvas initialization code
				updateBrush();
				addGrid();

				fabricCanvas.on('path:created', () => {
					dispatch('update', fabricCanvas.toDataURL());
				});
			});
		}

		return () => {
			if (fabricCanvas) {
				fabricCanvas.dispose();
			}
		};
	});

	// Update brush when tool changes
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

<div class="canvas-container">
	<canvas id="drawing-canvas"></canvas>
</div>
