export declare class ModelWidget {
    private currentModel;
    private modelProvider;
    constructor();
    getValue(): Promise<{
        label: string;
        value: string;
        color: string;
    }>;
    private fetchModelInfo;
    private extractProvider;
    updateModelInfo(modelName: string): void;
    getModelInfo(): {
        name: string;
        provider: string;
    };
}
