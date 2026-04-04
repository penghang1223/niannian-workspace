"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AgentWidget = void 0;
class AgentWidget {
    constructor() {
        this.currentAgent = 'main';
        this.agentStatus = 'idle';
        this.agentCount = 1;
        this.refreshAgentInfo();
    }
    async getValue() {
        this.refreshAgentInfo();
        const agentDisplay = `${this.currentAgent} (${this.agentCount})`;
        return {
            label: 'Agent',
            value: agentDisplay,
            color: '#ff0000'
        };
    }
    refreshAgentInfo() {
        try {
            this.currentAgent = 'main';
            this.agentStatus = 'idle';
            this.agentCount = 1;
        }
        catch (error) {
            this.currentAgent = 'unknown';
            this.agentStatus = 'error';
            this.agentCount = 0;
        }
    }
    updateAgentInfo(agentName, status, count) {
        this.currentAgent = agentName;
        this.agentStatus = status;
        this.agentCount = count;
    }
    getAgentInfo() {
        return {
            name: this.currentAgent,
            status: this.agentStatus,
            count: this.agentCount
        };
    }
}
exports.AgentWidget = AgentWidget;
//# sourceMappingURL=Agent.js.map