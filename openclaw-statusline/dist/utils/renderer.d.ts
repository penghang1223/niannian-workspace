import { Config } from './config';
export declare class Renderer {
    private config;
    constructor(config: Config);
    render(widgets: Array<{
        label: string;
        value: string;
        color: string;
    }>): string;
    private applyColor;
}
