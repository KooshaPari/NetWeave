<script lang="ts">
	import { onMount, createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';
	import type { Tool } from '$lib/types';

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

	// Add to existing event listeners
	function setupEventListeners() {
		// ... existing listeners ...

		fabricCanvas.on('mouse:dblclick', handleIntersectionCreation);

		fabricCanvas.on('object:moving', (e: any) => {
			if (e.target.data?.type === 'roundabout') {
				updateConnectedRoads(e.target);
			}
		});
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
</script>
