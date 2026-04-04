export declare class CostWidget {
    private sessionCost;
    private startTime;
    constructor();
    private initializeCostTracking;
    getValue(): Promise<{
        label: string;
        value: string;
        color: string;
    }>;
    updateCost(newCost: number): void;
    getCost(): number;
    resetCost(): void;
}
