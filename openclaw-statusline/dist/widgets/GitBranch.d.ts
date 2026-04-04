export declare class GitBranchWidget {
    private currentBranch;
    constructor();
    getValue(): Promise<{
        label: string;
        value: string;
        color: string;
    }>;
    private getCurrentBranch;
    refresh(): void;
    getCurrentBranchName(): string;
}
