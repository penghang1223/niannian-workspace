/**
 * Configuration manager for OpenClaw Status Line
 */

interface ConfigData {
  [key: string]: any;
}

export class Config {
  private config: ConfigData = {};
  private configFile: string;

  constructor(configFile: string = 'openclaw-statusline.json') {
    this.configFile = configFile;
    this.loadDefaults();
  }

  private loadDefaults(): void {
    this.config = {
      refreshInterval: 1000, // milliseconds
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

  async load(): Promise<void> {
    // Try to load from file, fall back to defaults if not found
    try {
      const fs = require('fs');
      if (fs.existsSync(this.configFile)) {
        const fileConfig = JSON.parse(fs.readFileSync(this.configFile, 'utf8'));
        this.config = { ...this.config, ...fileConfig };
      }
    } catch (error: any) {
      console.warn(`Could not load config from ${this.configFile}:`, error.message);
      // Use defaults if config file is invalid
    }
  }

  save(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const fs = require('fs');
        fs.writeFileSync(this.configFile, JSON.stringify(this.config, null, 2));
        resolve();
      } catch (error) {
        reject(error);
      }
    });
  }

  get(key: string, defaultValue?: any): any {
    return this.config[key] !== undefined ? this.config[key] : defaultValue;
  }

  set(key: string, value: any): void {
    this.config[key] = value;
  }
}