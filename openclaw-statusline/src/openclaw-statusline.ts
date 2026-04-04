#!/usr/bin/env node

/**
 * OpenClaw Status Line - A beautiful status bar system for OpenClaw
 * Inspired by ccstatusline but built specifically for OpenClaw's needs
 */

import { Config } from './utils/config';
import { Renderer } from './utils/renderer';
import { TokenWidget } from './widgets/Tokens';
import { SessionClockWidget } from './widgets/SessionClock';
import { ProjectWidget } from './widgets/Project';
import { CostWidget } from './widgets/Cost';
import { GitBranchWidget } from './widgets/GitBranch';
import { AgentWidget } from './widgets/Agent';
import { ModelWidget } from './widgets/Model';

class OpenClawStatusLine {
  private config: Config;
  private renderer: Renderer;
  
  // Core widgets
  private tokenWidget: TokenWidget;
  private sessionClockWidget: SessionClockWidget;
  private projectWidget: ProjectWidget;
  
  // Additional widgets
  private costWidget: CostWidget;
  private gitBranchWidget: GitBranchWidget;
  private agentWidget: AgentWidget;
  private modelWidget: ModelWidget;

  constructor() {
    this.config = new Config();
    this.renderer = new Renderer(this.config);
    
    // Initialize core widgets
    this.tokenWidget = new TokenWidget();
    this.sessionClockWidget = new SessionClockWidget();
    this.projectWidget = new ProjectWidget();
    
    // Initialize additional widgets
    this.costWidget = new CostWidget();
    this.gitBranchWidget = new GitBranchWidget();
    this.agentWidget = new AgentWidget();
    this.modelWidget = new ModelWidget();
  }

  async init(): Promise<void> {
    await this.config.load();
    console.log('OpenClaw Status Line initialized');
  }

  async update(): Promise<string> {
    const widgets = [];
    
    // Add core widgets
    widgets.push(await this.tokenWidget.getValue());
    widgets.push(await this.sessionClockWidget.getValue());
    widgets.push(await this.projectWidget.getValue());
    
    // Add additional widgets if enabled
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

  async start(): Promise<void> {
    await this.init();
    
    // Initial update
    console.log(await this.update());
    
    // Set up interval for updates
    setInterval(async () => {
      console.clear();
      console.log(await this.update());
    }, this.config.get('refreshInterval', 1000));
  }
}

// Handle command line arguments
async function main(): Promise<void> {
  const statusLine = new OpenClawStatusLine();
  await statusLine.start();
}

if (require.main === module) {
  main().catch(console.error);
}

export { OpenClawStatusLine };