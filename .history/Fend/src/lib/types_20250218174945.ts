export type Tool = keyof RoadType | keyof IntersectionType;
export interface SimulationState {
	networkImage: string;
	vehicles: Array<{
		x: number;
		y: number;
		direction: number;
		speed: number;
	}>;
	trafficLights: Array<{
		x: number;
		y: number;
		state: 'red' | 'green';
	}>;
	timestamp: number;
}
let selectedTool: Tool =
export interface IntersectionType {
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
export interface RoadType {
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
