export type Tool = keyof typeof roadTypes | keyof typeof intersectionTypes;
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
const roadTypes = {
	highway: {
		name: 'Highway',
		color: '#505050',
		width: 40,
		style: {
			strokeWidth: 40,
			stroke: '#505050',
			strokeDashArray: [20, 10]
		}
	},
	mainRoad: {
		name: 'Main Road',
		color: '#454545',
		width: 30,
		style: {
			strokeWidth: 30,
			stroke: '#454545',
			strokeDashArray: [15, 10]
		}
	},
	localRoad: {
		name: 'Local Road',
		color: '#383838',
		width: 20,
		style: {
			strokeWidth: 20,
			stroke: '#383838',
			strokeDashArray: [5, 5]
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
