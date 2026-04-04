#!/usr/bin/env node
"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OpenClawStatusLine = void 0;
const config_1 = require("./utils/config");
const renderer_1 = require("./utils/renderer");
const Tokens_1 = require("./widgets/Tokens");
const SessionClock_1 = require("./widgets/SessionClock");
const Project_1 = require("./widgets/Project");
const Cost_1 = require("./widgets/Cost");
const GitBranch_1 = require("./widgets/GitBranch");
const Agent_1 = require("./widgets/Agent");
const Model_1 = require("./widgets/Model");
class OpenClawStatusLine {
    constructor() {
        this.config = new config_1.Config();
        this.renderer = new renderer_1.Renderer(this.config);
        this.tokenWidget = new Tokens_1.TokenWidget();
        this.sessionClockWidget = new SessionClock_1.SessionClockWidget();
        this.projectWidget = new Project_1.ProjectWidget();
        this.costWidget = new Cost_1.CostWidget();
        this.gitBranchWidget = new GitBranch_1.GitBranchWidget();
        this.agentWidget = new Agent_1.AgentWidget();
        this.modelWidget = new Model_1.ModelWidget();
    }
    async init() {
        await this.config.load();
        console.log('OpenClaw Status Line initialized');
    }
    async update() {
        const widgets = [];
        widgets.push(await this.tokenWidget.getValue());
        widgets.push(await this.sessionClockWidget.getValue());
        widgets.push(await this.projectWidget.getValue());
        if (this.config.get('showCost', true)) {
            widgets.push(await this.costWidget.getValue());
        }
        if (this.config.get('showGit', true)) {
            widgets.push(await this.gitBranchWidget.getValue());
        }
        if (this.config.get('showAgent', true)) {
            widgets.push(await this.agentWidget.getValue());
        }
        if (this.config.get('showModel', true)) {
            widgets.push(await this.modelWidget.getValue());
        }
        return this.renderer.render(widgets);
    }
    async start() {
        await this.init();
        console.log(await this.update());
        setInterval(async () => {
            console.clear();
            console.log(await this.update());
        }, this.config.get('refreshInterval', 1000));
    }
}
exports.OpenClawStatusLine = OpenClawStatusLine;
async function main() {
    const statusLine = new OpenClawStatusLine();
    await statusLine.start();
}
if (require.main === module) {
    main().catch(console.error);
}
//# sourceMappingURL=openclaw-statusline.js.map