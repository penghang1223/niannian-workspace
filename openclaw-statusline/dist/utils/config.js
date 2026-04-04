"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Config = void 0;
class Config {
    constructor(configFile = 'openclaw-statusline.json') {
        this.config = {};
        this.configFile = configFile;
        this.loadDefaults();
    }
    loadDefaults() {
        this.config = {
            refreshInterval: 1000,
            showCost: true,
            showGit: true,
            showAgent: true,
            showModel: true,
            theme: 'default',
            position: 'bottom',
            separator: ' | ',
            colors: {
                token: '#00ff00',
                clock: '#ffff00',
                project: '#ff00ff',
                cost: '#00ffff',
                git: '#ffa500',
                agent: '#ff0000',
                model: '#800080'
            }
        };
    }
    async load() {
        try {
            const fs = require('fs');
            if (fs.existsSync(this.configFile)) {
                const fileConfig = JSON.parse(fs.readFileSync(this.configFile, 'utf8'));
                this.config = { ...this.config, ...fileConfig };
            }
        }
        catch (error) {
            console.warn(`Could not load config from ${this.configFile}:`, error.message);
        }
    }
    save() {
        return new Promise((resolve, reject) => {
            try {
                const fs = require('fs');
                fs.writeFileSync(this.configFile, JSON.stringify(this.config, null, 2));
                resolve();
            }
            catch (error) {
                reject(error);
            }
        });
    }
    get(key, defaultValue) {
        return this.config[key] !== undefined ? this.config[key] : defaultValue;
    }
    set(key, value) {
        this.config[key] = value;
    }
}
exports.Config = Config;
//# sourceMappingURL=config.js.map