export declare class SessionClockWidget {
    private startTime;
    constructor();
    getValue(): Promise<{
        label: string;
        value: string;
        color: string;
    }>;
    private formatElapsedTime;
    reset(): void;
    getElapsedTime(): number;
}
