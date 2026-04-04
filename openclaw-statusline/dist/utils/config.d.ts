export declare class Config {
    private config;
    private configFile;
    constructor(configFile?: string);
    private loadDefaults;
    load(): Promise<void>;
    save(): Promise<void>;
    get(key: string, defaultValue?: any): any;
    set(key: string, value: any): void;
}
