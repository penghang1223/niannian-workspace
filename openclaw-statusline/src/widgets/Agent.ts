/**
 * Agent Status Widget for OpenClaw Status Line
 * Shows the current active agent status
 */

export class AgentWidget {
  private currentAgent: string = 'main';
  private agentStatus: string = 'idle';
  private agentCount: number = 1;

  constructor() {
    this.refreshAgentInfo();
  }

  async getValue(): Promise<{ label: string; value: string; color: string }> {
    // Refresh agent info periodically
    this.refreshAgentInfo();
    
    const agentDisplay = `${this.currentAgent} (${this.agentCount})`;
    
    return {
      label: 'Agent',
      value: agentDisplay,
      color: '#ff0000' // Red
    };
  }

  private refreshAgentInfo(): void {
    // In a real implementation, this would get agent information from OpenClaw
    // For now, we'll simulate some basic agent information
    try {
      // This would normally connect to OpenClaw's agent management system
      // For simulation purposes, we'll just use static data
      this.currentAgent = 'main';
      this.agentStatus = 'idle';
      this.agentCount = 1;
    } catch (error) {
      this.currentAgent = 'unknown';
      this.agentStatus = 'error';
      this.agentCount = 0;
    }
  }

  // Method to update agent info externally
  updateAgentInfo(agentName: string, status: string, count: number): void {
    this.currentAgent = agentName;
    this.agentStatus = status;
    this.agentCount = count;
  }

  // Get current agent info
  getAgentInfo(): { name: string; status: string; count: number } {
    return {
      name: this.currentAgent,
      status: this.agentStatus,
      count: this.agentCount
    };
  }
}