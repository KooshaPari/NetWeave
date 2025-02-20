// src/routes/+page.svelte
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
        <header class="mb-6 flex justify-between items-center">
            <h1 class="text-2xl font-bold text-gray-800">Traffic Network Simulator</h1>
            <div class="flex gap-4 items-center">
                <button
                    class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    on:click={toggleSimulation}
                >
                    {isSimulating ? 'View Network' : 'Start Simulation'}
                </button>
            </div>
        </header>

        <!-- Main content area -->
        <div class="flex gap-6">
            <!-- Left panel: Drawing tools and input canvas -->
            <div class="flex-1 bg-white rounded-lg shadow-lg p-4">
                <div class="mb-4">
                    <h2 class="text-lg font-semibold mb-2">Network Design</h2>
                    <ToolPanel 
                        {selectedTool}
                        on:toolSelect={e => selectedTool = e.detail}
                    />
                </div>
                <DrawingCanvas
                    {selectedTool}
                    on:update={handleDrawingUpdate}
                />
            </div>

            <!-- Right panel: Output canvas (pre-sim render or simulation) -->
            <div class="flex-1 bg-white rounded-lg shadow-lg p-4">
                <h2 class="text-lg font-semibold mb-4">
                    {isSimulating ? 'Traffic Simulation' : 'Network Preview'}
                </h2>
                <OutputCanvas
                    {simulationState}
                    {isSimulating}
                />
            </div>
        </div>
    </main>
</div>

// src/lib/components/DrawingCanvas.svelte
<script lang="ts">
    import { onMount, createEventDispatcher } from 'svelte';
    import { fabric } from 'fabric';
    import type { Tool } from '$lib/types';

    export let selectedTool: Tool;
    const dispatch = createEventDispatcher();

    let canvas: fabric.Canvas;
    
    const toolSettings = {
        road: {
            color: '#404040',
            width: 20,
        },
        intersection: {
            color: '#666666',
            width: 30,
        },
        trafficLight: {
            color: '#FF4444',
            width: 15,
        }
    };

    onMount(() => {
        // Initialize Fabric.js canvas
        canvas = new fabric.Canvas('drawing-canvas', {
            isDrawingMode: true,
            width: 800,
            height: 600,
            backgroundColor: '#f8f9fa'
        });

        // Set up initial brush
        updateBrush();

        // Add grid for better visualization
        addGrid();

        // Handle drawing updates
        canvas.on('path:created', () => {
            dispatch('update', canvas.toDataURL());
        });

        return () => {
            canvas.dispose();
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
            canvas.add(new fabric.Line(
                [i * gridSize, 0, i * gridSize, canvas.height],
                { stroke: gridColor, selectable: false }
            ));
        }

        for (let i = 0; i < canvas.height / gridSize; i++) {
            canvas.add(new fabric.Line(
                [0, i * gridSize, canvas.width, i * gridSize],
                { stroke: gridColor, selectable: false }
            ));
        }
    }
</script>

<div class="canvas-container">
    <canvas id="drawing-canvas"></canvas>
</div>
 