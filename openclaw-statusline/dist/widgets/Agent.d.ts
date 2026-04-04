export declare class AgentWidget {
    private currentAgent;
    private agentStatus;
    private agentCount;
    constructor();
    getValue(): Promise<{
        label: string;
        value: string;
        color: string;
    }>;
    private refreshAgentInfo;
    updateAgentInfo(agentName: string, status: string, count: number): void;
    getAgentInfo(): {
        name: string;
        status: string;
        count: number;
    };
}
