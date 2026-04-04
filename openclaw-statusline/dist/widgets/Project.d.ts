export declare class ProjectWidget {
    private currentProject;
    constructor();
    getValue(): Promise<{
        label: string;
        value: string;
        color: string;
    }>;
    private getCurrentProject;
    setCurrentProject(projectName: string): void;
    getCurrentProjectName(): string;
}
