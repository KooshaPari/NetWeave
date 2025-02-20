<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';
	import type { Tool } from '$lib/types';

	$: console.log('isLoading:', isLoading);
	export let selectedTool: Tool;
	const dispatch = createEventDispatcher<CanvasEvents>();
	let isLoading = true;
	let canvas: HTMLCanvasElement;
	let fabricCanvas: any = null;
	interface IntersectionType {
		name: string;
		radius: number;
		capacity: number;
		entries: number;
		type: 'roundabout' | 'signalized' | 'grade_separated' | 'slip_road';
		style: {
			fill: string;
			stroke: string;
			strokeWidth: number;
		};
		trafficRules: {
			yieldBehavior: 'yield' | 'stop' | 'signal';
			mergeAngle: number;
			priorityRoads: boolean;
		};
	}
	interface CanvasEvents {
		update: {
			canvas: string;
			roadData: any;
		};
	}
	interface RoadType {
		name: string;
		color: string;
		width: number;
		lanes: number;
		speedLimit: number;
		capacity: number;
		type: 'one-way' | 'two-way';
		highway: {
			name: 'Highway';
			color: '#505050';
			width: 40;
			lanes: 3;
			speedLimit: 100;
			capacity: 2000;
			type: 'one-way';
			zoning: false;
			margin: 15;
			style: {
				strokeWidth: 40;
				stroke: '#505050';
				strokeDashArray: [20, 10];
			};
		};
		arterial: {
			name: 'Six-Lane Road';
			color: '#454545';
			width: 35;
			lanes: 3;
			speedLimit: 60;
			capacity: 1500;
			type: 'two-way';
			zoning: true;
			margin: 10;
			style: {
				strokeWidth: 35;
				stroke: '#454545';
				strokeDashArray: [15, 10];
			};
		};
		collector: {
			name: 'Four-Lane Road';
			color: '#404040';
			width: 30;
			lanes: 2;
			speedLimit: 40;
			capacity: 1000;
			type: 'two-way';
			zoning: true;
			margin: 8;
			style: {
				strokeWidth: 30;
				stroke: '#404040';
				strokeDashArray: [10, 5];
			};
		};
		local: {
			name: 'Two-Lane Road';
			color: '#383838';
			width: 20;
			lanes: 1;
			speedLimit: 30;
			capacity: 500;
			type: 'two-way';
			zoning: true;
			margin: 5;
			style: {
				strokeWidth: 20;
				stroke: '#383838';
				strokeDashArray: [5, 5];
			};
		};
		oneWay: {
			name: 'One-Way Street';
			color: '#353535';
			width: 15;
			lanes: 1;
			speedLimit: 30;
			capacity: 400;
			type: 'one-way';
			zoning: true;
			margin: 5;
			style: {
				strokeWidth: 15;
				strokeDashArray: [10, 5];
				stroke: '#353535';
			};
		};
	}
	const roadTypes = {
		highway: {
			name: 'Highway',
			color: '#505050',
			width: 40,
			style: {
				strokeWidth: 40,
				stroke: '#505050'
			}
		},
		mainRoad: {
			name: 'Main Road',
			color: '#454545',
			width: 30,
			style: {
				strokeWidth: 30,
				stroke: '#454545'
			}
		},
		localRoad: {
			name: 'Local Road',
			color: '#383838',
			width: 20,
			style: {
				strokeWidth: 20,
				stroke: '#383838'
			}
		}
	};
	const intersectionTypes = {
		roundabout: {
			name: 'Roundabout',
			radius: 40,
			capacity: 2000,
			entries: 4,
			type: 'roundabout',
			style: {
				fill: '#454545',
				stroke: '#FFFFFF',
				strokeWidth: 2
			},
			trafficRules: {
				yieldBehavior: 'yield',
				mergeAngle: 30,
				priorityRoads: false
			}
		},
		signalizedIntersection: {
			name: 'Signalized Intersection',
			radius: 30,
			capacity: 1500,
			entries: 4,
			type: 'signalized',
			style: {
				fill: '#404040',
				stroke: '#FFFFFF',
				strokeWidth: 2
			},
			trafficRules: {
				yieldBehavior: 'signal',
				mergeAngle: 90,
				priorityRoads: true
			}
		},
		slipRoad: {
			name: 'Slip Road',
			radius: 25,
			capacity: 800,
			entries: 2,
			type: 'slip_road',
			style: {
				fill: '#383838',
				stroke: '#FFFFFF',
				strokeWidth: 1
			},
			trafficRules: {
				yieldBehavior: 'yield',
				mergeAngle: 15,
				priorityRoads: true
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
	let fabric: any = null;
	onMount(async () => {
		if (!browser) return;
		console.log('Loading fabric');
		try {
			console.log('Importing fabric');
			fabric = await import('fabric');
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
		const currentRoad: RoadType = roadTypes.mainRoad;

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
	function updateConnectedRoads(intersection: any) {
		const connectedPaths = fabricCanvas.getObjects('path').filter((path: any) => {
			return path.intersectsWithObject(intersection);
		});

		connectedPaths.forEach((path: any) => {
			adjustRoadConnection(path, intersection);
		});
	}

	function adjustRoadConnection(road: any, intersection: any) {
		// Implement road connection logic based on intersection type
		const intersectionType = intersection.data.type;
		const roadType = road.data.type;

		switch (intersectionType) {
			case 'roundabout':
				adjustRoundaboutConnection(road, intersection);
				break;
			case 'signalized':
				adjustSignalizedConnection(road, intersection);
				break;
			case 'slip_road':
				adjustSlipRoadConnection(road, intersection);
				break;
		}
	}
	function adjustRoundaboutConnection(road: any, intersection: any) {
		console.log('Adjusting slip road connection', road, intersection);
	}
	function adjustSignalizedConnection(road: any, intersection: any) {
		console.log('Adjusting slip road connection', road, intersection);
	}
	function adjustSlipRoadConnection(road: any, intersection: any) {
		console.log('Adjusting slip road connection', road, intersection);
	}

	function setupEventListeners() {
		fabricCanvas.on('path:created', (e: any) => {
			const path = e.path;
			dispatch('update', {
				canvas: fabricCanvas.toDataURL(),
				roadData: path.data
			});
		});
		fabricCanvas.on('mouse:dblclick', handleIntersectionCreation);

		fabricCanvas.on('object:moving', (e: any) => {
			if (e.target.data?.type === 'roundabout') {
				updateConnectedRoads(e.target);
			}
		});
	}

	async function addLaneMarkers(path: any, roadType: RoadType) {
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

	function createEntryPoint(fabric: any, config: IntersectionType, angle: number) {
		const length = 20;
		const x = config.radius * Math.cos((angle * Math.PI) / 180);
		const y = config.radius * Math.sin((angle * Math.PI) / 180);

		return new fabric.Line(
			[
				x,
				y,
				x + length * Math.cos((angle * Math.PI) / 180),
				y + length * Math.sin((angle * Math.PI) / 180)
			],
			{
				stroke: '#FFFFFF',
				strokeWidth: 2
			}
		);
	}

	function createTrafficLightPoint(fabric: any, config: IntersectionType, angle: number) {
		return new fabric.Circle({
			radius: 3,
			fill: '#FF0000',
			left: config.radius + config.radius * Math.cos((angle * Math.PI) / 180),
			top: config.radius + config.radius * Math.sin((angle * Math.PI) / 180)
		});
	}

	function addPedestrianCrossings(fabric: any, intersection: any, config: IntersectionType) {
		const crossingWidth = 10;
		const stripeCount = 6;

		for (let i = 0; i < 4; i++) {
			const group = new fabric.Group([], {
				left: i % 2 === 0 ? -crossingWidth : config.radius * 2,
				top: i < 2 ? 0 : config.radius * 2 - crossingWidth
			});

			for (let j = 0; j < stripeCount; j++) {
				const stripe = new fabric.Rect({
					left: j * (crossingWidth / stripeCount),
					top: 0,
					width: crossingWidth / stripeCount / 2,
					height: crossingWidth,
					fill: '#FFFFFF'
				});
				group.addWithUpdate(stripe);
			}

			intersection.addWithUpdate(group);
		}
	}
	function addRoundaboutElements(fabric: any, intersection: any, config: IntersectionType) {
		// Central circle
		const circle = new fabric.Circle({
			radius: config.radius,
			fill: config.style.fill,
			stroke: config.style.stroke,
			strokeWidth: config.style.strokeWidth
		});

		// Lane markings
		const innerCircle = new fabric.Circle({
			radius: config.radius - 15,
			fill: 'transparent',
			stroke: '#FFFFFF',
			strokeWidth: 1,
			strokeDashArray: [5, 5]
		});

		// Entry points
		for (let i = 0; i < config.entries; i++) {
			const angle = (i * 360) / config.entries;
			const entry = createEntryPoint(fabric, config, angle);
			intersection.addWithUpdate(entry);
		}

		intersection.addWithUpdate(circle);
		intersection.addWithUpdate(innerCircle);
	}

	function addSignalizedElements(fabric: any, intersection: any, config: IntersectionType) {
		// Create base intersection
		const base = new fabric.Rect({
			width: config.radius * 2,
			height: config.radius * 2,
			fill: config.style.fill,
			stroke: config.style.stroke,
			strokeWidth: config.style.strokeWidth
		});

		// Add traffic light points
		for (let i = 0; i < config.entries; i++) {
			const angle = i * 90;
			const light = createTrafficLightPoint(fabric, config, angle);
			intersection.addWithUpdate(light);
		}

		// Add pedestrian crossings
		addPedestrianCrossings(fabric, intersection, config);

		intersection.addWithUpdate(base);
	}

	function addSlipRoadElements(fabric: any, intersection: any, config: IntersectionType) {
		// Create curved slip road path
		const path = new fabric.Path('M 0 0 Q 50 0 50 50', {
			fill: 'transparent',
			stroke: config.style.fill,
			strokeWidth: config.style.strokeWidth
		});

		// Add yield markings
		const yieldLine = new fabric.Path('M 40 40 L 60 40', {
			stroke: '#FFFFFF',
			strokeWidth: 2,
			strokeDashArray: [5, 5]
		});

		intersection.addWithUpdate(path);
		intersection.addWithUpdate(yieldLine);
	}
	function createIntersection(
		fabric: any,
		intersectionType: IntersectionType,
		position: { x: number; y: number }
	) {
		const intersection = new fabric.Group([], {
			left: position.x,
			top: position.y,
			selectable: true,
			data: {
				type: intersectionType.type,
				capacity: intersectionType.capacity,
				trafficRules: intersectionType.trafficRules
			}
		});

		switch (intersectionType.type) {
			case 'roundabout':
				addRoundaboutElements(fabric, intersection, intersectionType);
				break;
			case 'signalized':
				addSignalizedElements(fabric, intersection, intersectionType);
				break;
			case 'slip_road':
				addSlipRoadElements(fabric, intersection, intersectionType);
				break;
		}

		return intersection;
	}
	function handleIntersectionCreation(e: any) {
		const pointer = fabricCanvas.getPointer(e);
		const intersectionType = intersectionTypes[selectedTool as keyof typeof intersectionTypes];

		if (intersectionType) {
			const intersection = createIntersection(fabric, intersectionType, {
				x: pointer.x,
				y: pointer.y
			});

			fabricCanvas.add(intersection);
			fabricCanvas.renderAll();
		}
	}
	async function updateBrush() {
		if (!fabricCanvas) return;

		const settings = toolSettings[selectedTool];
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
	async function setupIntersection(e: any) {
		const pointer = fabricCanvas.getPointer(e);
		const intersectionType = intersectionTypes[selectedTool as keyof typeof intersectionTypes];

		if (intersectionType) {
			const intersection = createIntersection(fabric, intersectionType, {
				x: pointer.x,
				y: pointer.y
			});
			fabricCanvas.add(intersection);
			fabricCanvas.renderAll();
		}
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
