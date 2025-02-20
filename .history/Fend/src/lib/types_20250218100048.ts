export type Tool = 'road' | 'intersection' | 'trafficLight';

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
