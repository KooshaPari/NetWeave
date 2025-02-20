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
	zoning: boolean;
	margin: number;
	style: {
		strokeWidth: number;
		stroke: string;
		strokeDashArray?: number[];
	};
}
