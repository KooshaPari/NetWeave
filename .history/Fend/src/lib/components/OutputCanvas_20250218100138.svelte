<script lang="ts">
    import { onMount } from 'svelte';
    import type { SimulationState } from '$lib/types';

    export let simulationState: SimulationState | null = null;
    export let isSimulating: boolean = false;

    let canvas: HTMLCanvasElement;
    let ctx: CanvasRenderingContext2D;
    let animationFrame: number;

    onMount(() => {
        ctx = canvas.getContext('2d')!;
        
        // Start animation loop if we're simulating
        if (isSimulating) {
            startSimulationLoop();
        }

        return () => {
            if (animationFrame) {
                cancelAnimationFrame(animationFrame);
            }
        };
    });

    // Start or stop simulation based on isSimulating prop
    $: if (ctx && isSimulating) {
        startSimulationLoop();
    } else if (ctx && !isSimulating) {
        stopSimulationLoop();
    }

    function startSimulationLoop() {
        const loop = () => {
            if (simulationState) {
                renderFrame(simulationState);
            }
            animationFrame = requestAnimationFrame(loop);
        };
        loop();
    }

    function stopSimulationLoop() {
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
        }
        // Show static network view
        if (simulationState) {
            renderNetwork(simulationState);
        }
    }

    function renderNetwork(state: SimulationState) {
        const img = new Image();
        img.onload = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
        };
        img.src = state.networkImage;
    }

    function renderFrame(state: SimulationState) {
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw base network
        const img = new Image();
        img.onload = () => {
            ctx.drawImage(img, 0, 0);
            
            // Draw vehicles
            state.vehicles.forEach(vehicle => {
                ctx.fillStyle = '#4CAF50';
                ctx.beginPath();
                ctx.arc(vehicle.x, vehicle.y, 4, 0, Math.PI * 2);
                ctx.fill();
            });

            // Draw traffic lights
            state.trafficLights.forEach(light => {
                ctx.fillStyle = light.state === 'red' ? '#FF0000' : '#00FF00';
                ctx.beginPath();
                ctx.arc(light.x, light.y, 6, 0, Math.PI * 2);
                ctx.fill();
            });
        };
        img.src = state.networkImage;
    }
</script>

<canvas
    bind:this={canvas}
    width={800}
    height={600}
    class="border rounded"
/> 