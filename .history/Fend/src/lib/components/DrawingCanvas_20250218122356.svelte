<script lang="ts">
    import { onMount } from 'svelte';
    import { browser } from '$app/environment';
    // ...other code remains unchanged

    let isLoading = true;
    let canvas: HTMLCanvasElement;
    let fabricCanvas: any = null;

    onMount(async () => {
        if (!browser) return;
        // Wait for the next tick to ensure the canvas is in the DOM
        // Alternatively, if everything is restructured, the canvas is already available.
        try {
            const fabric = await import('fabric');
            fabricCanvas = new fabric.Canvas(canvas, {
                backgroundColor: '#f8f9fa'
            });
            // ...rest of your initialization code
            isLoading = false;
        } catch (error) {
            console.error('Failed to initialize canvas:', error);
        }
    });
</script>

<div class="canvas-container">
    <canvas bind:this={canvas} class="rounded border border-gray-200 shadow-sm"></canvas>
    {#if isLoading}
        <div class="loading-overlay">
            <span>Loading canvas...</span>
        </div>
    {/if}
</div>

<style>
    .canvas-container {
        width: 800px;
        height: 600px;
        position: relative;
    }
    .loading-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(248, 249, 250, 0.7);
    }
</style>
