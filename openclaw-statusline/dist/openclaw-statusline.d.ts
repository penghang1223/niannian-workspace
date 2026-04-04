#!/usr/bin/env node
declare class OpenClawStatusLine {
    private config;
    private renderer;
    private tokenWidget;
    private sessionClockWidget;
    private projectWidget;
    private costWidget;
    private gitBranchWidget;
    private agentWidget;
    private modelWidget;
    constructor();
    init(): Promise<void>;
    update(): Promise<string>;
    start(): Promise<void>;
}
export { OpenClawStatusLine };
