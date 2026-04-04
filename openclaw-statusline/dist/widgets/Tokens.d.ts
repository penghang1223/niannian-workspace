export declare class TokenWidget {
    private tokenCount;
    private startTime;
    constructor();
    private initializeTokenTracking;
    getValue(): Promise<{
        label: string;
        value: string;
        color: string;
    }>;
    private formatTokenCount;
    updateTokenCount(newCount: number): void;
    getTokenCount(): number;
}
